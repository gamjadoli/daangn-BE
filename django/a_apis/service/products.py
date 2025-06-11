import math
from datetime import datetime, timedelta

from a_apis.models import InterestProduct, Product, ProductCategory, ProductImage
from a_apis.models.chat import ChatRoom
from a_apis.service.files import FileService
from a_user.models import MannerRating, Review

from django.contrib.gis.geos import Point
from django.db import transaction
from django.db.models import Count, OuterRef, Q, Subquery
from django.utils import timezone


class ProductService:
    @staticmethod
    def calculate_distance_text(point1, point2):
        """두 지점 간의 거리를 계산하여 텍스트로 반환"""
        if not point1 or not point2:
            return None

        # 두 점 간의 거리를 미터 단위로 계산
        distance_meters = point1.distance(point2) * 111000  # 대략적인 변환 (도 -> 미터)

        if distance_meters < 1000:
            return f"{int(distance_meters)}m"
        else:
            distance_km = distance_meters / 1000
            return f"{distance_km:.1f}km"

    @staticmethod
    def get_product_model():
        """Product 모델 반환 (테스트 모킹 용이성 위함)"""
        return Product

    @staticmethod
    @transaction.atomic
    def create_product(user_id: int, data: dict, images: list = None) -> dict:
        try:
            # 사용자 인증 동네 확인
            from a_apis.models.region import EupmyeondongRegion, UserActivityRegion

            # 사용자가 선택한 동네가 인증된 동네인지 확인
            region_id = data.region_id
            user_region = UserActivityRegion.objects.filter(
                user_id=user_id, activity_area_id=region_id
            ).first()

            if not user_region:
                return {
                    "success": False,
                    "message": "인증된 동네가 아닙니다. 동네 인증 후 다시 시도해주세요.",
                }

            # 거래 위치 생성 (선택사항)
            meeting_point = None
            location_description = None
            if data.meeting_location:
                meeting_point = Point(
                    data.meeting_location.longitude,
                    data.meeting_location.latitude,
                    srid=4326,
                )
                location_description = data.meeting_location.description

            # 상품 생성 (region 필드 추가)
            product = Product.objects.create(
                user_id=user_id,
                title=data.title,
                trade_type=data.trade_type,
                price=data.price if data.trade_type == "sale" else None,
                accept_price_offer=data.accept_price_offer,
                description=data.description,
                category_id=data.category_id,
                region_id=region_id,  # 선택한 동네 정보 저장
                meeting_location=meeting_point,
                location_description=location_description,
                refresh_at=timezone.now(),
            )

            # 이미지 처리
            if images:
                for image_file in images:
                    # FileService를 통해 파일 업로드
                    file_obj = FileService.upload_file(image_file)
                    ProductImage.objects.create(product=product, file=file_obj)

            return {
                "success": True,
                "message": "상품이 등록되었습니다.",
                "data": ProductService._product_to_detail(product, user_id),
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_products(user_id=None, filter_params=None) -> dict:
        """상품 목록 조회 서비스 (지리적 거리 기반 3km 범위)"""
        try:
            from a_apis.models.region import UserActivityRegion

            from django.contrib.gis.db.models.functions import Distance
            from django.contrib.gis.measure import D

            # 기본 쿼리셋
            queryset = Product.objects.select_related("user", "region").order_by(
                "-refresh_at"
            )

            # 사용자의 활성 동네 중심점 조회 (지리적 필터링용)
            user_center_point = None
            active_region_name = None
            if user_id:
                active_region = (
                    UserActivityRegion.objects.filter(user_id=user_id, priority=1)
                    .select_related("activity_area")
                    .first()
                )

                if (
                    active_region
                    and active_region.activity_area
                    and active_region.activity_area.center_coordinates
                ):
                    user_center_point = active_region.activity_area.center_coordinates
                    active_region_name = active_region.activity_area.name

            # 필터링 적용 (있는 경우)
            if filter_params:
                # 검색어 적용
                if filter_params.get("search"):
                    search_keyword = filter_params["search"]
                    queryset = queryset.filter(
                        Q(title__icontains=search_keyword)
                        | Q(description__icontains=search_keyword)
                    )

                # 상태, 거래타입 필터링
                if filter_params.get("status"):
                    queryset = queryset.filter(status=filter_params["status"])
                if filter_params.get("trade_type"):
                    queryset = queryset.filter(trade_type=filter_params["trade_type"])

                # 지리적 필터링 (반경 3km)
                region_id = filter_params.get("region_id")
                if region_id:
                    # 특정 동네 ID가 제공된 경우 해당 동네 중심에서 3km 범위
                    from a_apis.models.region import EupmyeondongRegion

                    try:
                        specific_region = EupmyeondongRegion.objects.get(id=region_id)
                        if specific_region.center_coordinates:
                            # 3km를 도(degree) 단위로 변환: 1도 ≈ 111km이므로 3km ≈ 0.027도
                            distance_in_degrees = 3.0 / 111.0
                            queryset = queryset.filter(
                                region__center_coordinates__dwithin=(
                                    specific_region.center_coordinates,
                                    distance_in_degrees,
                                )
                            )
                            # 거리순으로 정렬
                            queryset = queryset.annotate(
                                distance=Distance(
                                    "region__center_coordinates",
                                    specific_region.center_coordinates,
                                )
                            ).order_by("distance", "-refresh_at")
                    except EupmyeondongRegion.DoesNotExist:
                        pass
                elif user_center_point:
                    # 사용자의 활성 동네에서 3km 범위의 상품만 필터링
                    # 3km를 도(degree) 단위로 변환: 1도 ≈ 111km이므로 3km ≈ 0.027도
                    distance_in_degrees = 3.0 / 111.0
                    queryset = queryset.filter(
                        region__center_coordinates__dwithin=(
                            user_center_point,
                            distance_in_degrees,
                        )
                    )
                    # 거리순으로 정렬
                    queryset = queryset.annotate(
                        distance=Distance(
                            "region__center_coordinates", user_center_point
                        )
                    ).order_by("distance", "-refresh_at")

            # 페이지네이션 파라미터
            page = filter_params.get("page", 1) if filter_params else 1
            page_size = filter_params.get("page_size", 20) if filter_params else 20

            # 총 개수 파악
            total_count = queryset.count()
            total_pages = math.ceil(total_count / page_size)

            # 페이지 범위 설정
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            # 첫 번째 이미지 ID 서브쿼리로 변경 (URL 대신 ID만 가져옴)
            first_image = (
                ProductImage.objects.filter(product=OuterRef("pk"))
                .select_related("file")
                .order_by("created_at")
            )

            # 관심 수 계산 서브쿼리
            interest_count = (
                InterestProduct.objects.filter(product=OuterRef("pk"))
                .values("product")
                .annotate(count=Count("id"))
                .values("count")
            )

            # 활성화된 채팅방 개수 서브쿼리

            chat_count = (
                ChatRoom.objects.filter(product=OuterRef("pk"), status="active")
                .values("product")
                .annotate(count=Count("id"))
                .values("count")
            )

            # 쿼리 실행 및 페이지네이션 - URL 대신 file_id를 가져옴
            products = queryset.annotate(
                file_id=Subquery(first_image.values("file__id")[:1]),
                interest_count=Subquery(interest_count[:1]),
                chat_count=Subquery(chat_count[:1]),
            )[start_idx:end_idx]

            # 결과 변환 - 이미지가 있는 경우 URL을 별도로 조회
            product_list = []

            for product in products:
                # 이미지 URL 별도 처리
                image_url = None
                if product.file_id:
                    try:
                        product_image = (
                            ProductImage.objects.select_related("file")
                            .filter(product_id=product.id)
                            .first()
                        )
                        if product_image and product_image.file:
                            image_url = product_image.file.url
                    except Exception:
                        # 이미지 URL 조회 실패 시 None으로 처리
                        pass

                # 동네 정보 추가
                region_name = product.region.name if product.region else None

                # 거래장소 정보 구성
                meeting_location = None
                if product.meeting_location:
                    meeting_location = {
                        "latitude": product.meeting_location.y,
                        "longitude": product.meeting_location.x,
                        "description": product.location_description,
                        "distance_text": None,
                    }

                    # 거리 계산 (사용자 인증 동네가 있는 경우)
                    if user_center_point:
                        try:
                            distance_text = ProductService.calculate_distance_text(
                                user_center_point, product.meeting_location
                            )
                            meeting_location["distance_text"] = distance_text
                        except Exception:
                            # 거리 계산 실패 시 무시
                            pass

                product_list.append(
                    {
                        "id": product.id,
                        "title": product.title,
                        "description": product.description,
                        "price": product.price,
                        "status": product.status,
                        "trade_type": product.trade_type,
                        "created_at": product.created_at.isoformat(),
                        "refresh_at": (
                            product.refresh_at.isoformat()
                            if product.refresh_at
                            else None
                        ),
                        "image_url": image_url,
                        "seller_nickname": product.user.nickname,
                        "meeting_location": meeting_location,
                        "interest_count": product.interest_count or 0,
                        "chat_count": product.chat_count or 0,
                        "region_name": region_name,
                    }
                )

            # 지리적 필터링 메시지 구성
            message = "상품 목록이 조회되었습니다."
            if filter_params and filter_params.get("region_id"):
                try:
                    from a_apis.models.region import EupmyeondongRegion

                    region = EupmyeondongRegion.objects.get(
                        id=filter_params["region_id"]
                    )
                    message = f"{region.name} 주변 3km 이내 상품 목록이 조회되었습니다."
                except Exception:
                    pass
            elif active_region_name:
                message = (
                    f"{active_region_name} 주변 3km 이내 상품 목록이 조회되었습니다."
                )

            return {
                "success": True,
                "message": message,
                "data": product_list,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }

        except Exception as e:
            return {"success": False, "message": str(e), "data": []}

    @staticmethod
    def get_product(product_id: int, user_id: int = None) -> dict:
        """상품 상세 조회 서비스"""
        try:
            product = Product.objects.select_related(
                "user", "user__profile_img", "region"
            ).get(id=product_id)

            # 조회수 증가
            product.view_count += 1
            product.save(update_fields=["view_count"])

            return {
                "success": True,
                "message": "상품 정보가 조회되었습니다.",
                "data": ProductService._product_to_detail(product, user_id),
            }

        except Product.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 상품입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    @transaction.atomic
    def update_product(product_id: int, user_id: int, data: dict, images=None) -> dict:
        """상품 수정 서비스"""
        try:
            product = Product.objects.select_related("user").get(id=product_id)

            # 권한 체크
            if product.user_id != user_id:
                return {"success": False, "message": "상품 수정 권한이 없습니다."}

            # 상품 정보 업데이트
            product.title = data.title
            product.trade_type = data.trade_type
            product.price = data.price if data.trade_type == "sale" else None
            product.accept_price_offer = data.accept_price_offer
            product.description = data.description

            # 위치 정보 업데이트
            product.meeting_location = Point(
                data.meeting_location.longitude,
                data.meeting_location.latitude,
                srid=4326,
            )
            product.location_description = data.meeting_location.description

            product.save()

            # 이미지 업데이트 (기존 이미지 삭제 후 새 이미지 등록)
            if images:
                # 기존 이미지 삭제
                for image in product.images.all():
                    FileService.delete_file(image.file)
                    image.delete()

                # 새 이미지 등록
                for image_file in images:
                    file_obj = FileService.upload_file(image_file)
                    ProductImage.objects.create(product=product, file=file_obj)

            return {
                "success": True,
                "message": "상품 정보가 수정되었습니다.",
                "data": ProductService._product_to_detail(product, user_id),
            }

        except Product.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 상품입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def update_product_status(product_id: int, user_id: int, status: str) -> dict:
        """상품 상태 변경 서비스"""
        try:
            product = Product.objects.get(id=product_id)

            # 권한 체크
            if product.user_id != user_id:
                return {"success": False, "message": "상품 상태 변경 권한이 없습니다."}

            # 상태 변경
            product.status = status
            product.save(update_fields=["status", "updated_at"])

            status_display = {
                "new": "판매중",
                "reserved": "예약중",
                "soldout": "판매완료",
            }.get(status, status)

            return {
                "success": True,
                "message": f"상품 상태가 '{status_display}'(으)로 변경되었습니다.",
                "data": ProductService._product_to_detail(product, user_id),
            }

        except Product.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 상품입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def refresh_product(product_id: int, user_id: int) -> dict:
        """상품 끌어올리기 서비스"""
        try:
            product = Product.objects.get(id=product_id)

            # 권한 체크
            if product.user_id != user_id:
                return {"success": False, "message": "상품 끌어올리기 권한이 없습니다."}

            # 하루 3회 제한 확인
            now = timezone.now()
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # 오늘 끌어올린 횟수 계산 (자정 기준)
            refresh_count_today = (
                Product.objects.filter(
                    user_id=user_id, refresh_at__gte=start_of_day, refresh_at__lt=now
                )
                .exclude(id=product_id)
                .count()
            )

            if refresh_count_today >= 3:
                return {
                    "success": False,
                    "message": "하루에 최대 3회까지만 상품을 끌어올릴 수 있습니다.",
                }

            # 끌어올리기 (refresh_at 업데이트)
            product.refresh_at = now
            product.save(update_fields=["refresh_at", "updated_at"])

            return {
                "success": True,
                "message": "상품이 끌어올려졌습니다.",
                "data": ProductService._product_to_detail(product, user_id),
            }

        except Product.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 상품입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    @transaction.atomic
    def delete_product(product_id: int, user_id: int) -> dict:
        """상품 삭제 서비스"""
        try:
            product = Product.objects.get(id=product_id)

            # 권한 체크
            if product.user_id != user_id:
                return {"success": False, "message": "상품 삭제 권한이 없습니다."}

            # 이미지 삭제
            for image in product.images.all():
                FileService.delete_file(image.file)

            # 상품 삭제
            product_title = product.title
            product.delete()

            return {
                "success": True,
                "message": f"상품 '{product_title}'이(가) 삭제되었습니다.",
            }

        except Product.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 상품입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def toggle_interest_product(product_id: int, user_id: int) -> dict:
        """관심 상품 등록/해제 서비스"""
        try:
            product = Product.objects.get(id=product_id)

            # 자신의 상품은 관심등록 불가
            if product.user_id == user_id:
                return {
                    "success": False,
                    "message": "자신의 상품은 관심등록할 수 없습니다.",
                }

            # 관심상품 여부 확인 및 토글
            interest, created = InterestProduct.objects.get_or_create(
                user_id=user_id,
                product_id=product_id,
                defaults={"created_at": timezone.now()},
            )

            if not created:
                # 이미 있으면 관심상품 해제
                interest.delete()
                return {
                    "success": True,
                    "message": "관심상품이 해제되었습니다.",
                    "data": {"is_interested": False},
                }
            else:
                # 새로 등록된 경우
                return {
                    "success": True,
                    "message": "관심상품으로 등록되었습니다.",
                    "data": {"is_interested": True},
                }

        except Product.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 상품입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_interest_products(user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """관심 상품 목록 조회 서비스"""
        try:
            # 관심상품 쿼리셋
            queryset = (
                Product.objects.filter(interested_users__user_id=user_id)
                .select_related("user", "region")
                .order_by("-interested_users__created_at")
            )

            # 총 개수 파악
            total_count = queryset.count()
            total_pages = math.ceil(total_count / page_size)

            # 페이지 범위 설정
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            # 첫 번째 이미지 ID 서브쿼리로 변경 (URL 대신 ID만 가져옴)
            first_image = (
                ProductImage.objects.filter(product=OuterRef("pk"))
                .select_related("file")
                .order_by("created_at")
            )

            # 관심 수 서브쿼리
            interest_count = (
                InterestProduct.objects.filter(product=OuterRef("pk"))
                .values("product")
                .annotate(count=Count("id"))
                .values("count")
            )

            # 활성화된 채팅방 개수 서브쿼리

            chat_count = (
                ChatRoom.objects.filter(product=OuterRef("pk"), status="active")
                .values("product")
                .annotate(count=Count("id"))
                .values("count")
            )

            # 쿼리 실행 및 페이지네이션 - URL 대신 file_id를 가져옴
            products = queryset.annotate(
                file_id=Subquery(first_image.values("file__id")[:1]),
                interest_count=Subquery(interest_count[:1]),
                chat_count=Subquery(chat_count[:1]),
            )[start_idx:end_idx]

            # 결과 변환 - 이미지가 있는 경우 URL을 별도로 조회
            product_list = []

            # 사용자 인증 동네 정보 조회 (거리 계산용)
            user_center_point = None
            try:
                from a_apis.models.region import UserActivityRegion

                active_region = (
                    UserActivityRegion.objects.filter(user_id=user_id, priority=1)
                    .select_related("activity_area")
                    .first()
                )

                if (
                    active_region
                    and active_region.activity_area
                    and active_region.activity_area.center_coordinates
                ):
                    user_center_point = active_region.activity_area.center_coordinates
            except Exception:
                # 인증 동네 조회 실패 시 무시
                pass

            for product in products:
                # 이미지 URL 별도 처리
                image_url = None
                if product.file_id:
                    try:
                        product_image = (
                            ProductImage.objects.select_related("file")
                            .filter(product_id=product.id)
                            .first()
                        )
                        if product_image and product_image.file:
                            image_url = product_image.file.url
                    except Exception:
                        # 이미지 URL 조회 실패 시 None으로 처리
                        pass

                # 동네 정보 추가
                region_name = product.region.name if product.region else None

                # 거래장소 정보 구성
                meeting_location = None
                if product.meeting_location:
                    meeting_location = {
                        "latitude": product.meeting_location.y,
                        "longitude": product.meeting_location.x,
                        "description": product.location_description,
                        "distance_text": None,
                    }

                    # 거리 계산 (사용자 인증 동네가 있는 경우)
                    if user_center_point:
                        try:
                            distance_text = ProductService.calculate_distance_text(
                                user_center_point, product.meeting_location
                            )
                            meeting_location["distance_text"] = distance_text
                        except Exception:
                            # 거리 계산 실패 시 무시
                            pass

                product_list.append(
                    {
                        "id": product.id,
                        "title": product.title,
                        "description": product.description,
                        "price": product.price,
                        "status": product.status,
                        "trade_type": product.trade_type,
                        "created_at": product.created_at.isoformat(),
                        "refresh_at": (
                            product.refresh_at.isoformat()
                            if product.refresh_at
                            else None
                        ),
                        "image_url": image_url,
                        "seller_nickname": product.user.nickname,
                        "meeting_location": meeting_location,
                        "interest_count": product.interest_count or 0,
                        "region_name": region_name,
                    }
                )

            return {
                "success": True,
                "message": "관심 상품 목록이 조회되었습니다.",
                "data": product_list,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }

        except Exception as e:
            return {"success": False, "message": str(e), "data": []}

    @staticmethod
    def get_user_products(
        user_id: int, status=None, page: int = 1, page_size: int = 20
    ) -> dict:
        """사용자 상품 목록 조회 서비스"""
        try:
            # 기본 쿼리셋 (내 상품)
            queryset = (
                Product.objects.filter(user_id=user_id)
                .select_related("region")
                .order_by("-refresh_at")
            )

            # 상태 필터링
            if status:
                queryset = queryset.filter(status=status)

            # 총 개수 파악
            total_count = queryset.count()
            total_pages = math.ceil(total_count / page_size)

            # 페이지 범위 설정
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            # 첫 번째 이미지 ID 서브쿼리로 변경 (URL 대신 ID만 가져옴)
            first_image = (
                ProductImage.objects.filter(product=OuterRef("pk"))
                .select_related("file")
                .order_by("created_at")
            )

            # 관심 수 서브쿼리
            interest_count = (
                InterestProduct.objects.filter(product=OuterRef("pk"))
                .values("product")
                .annotate(count=Count("id"))
                .values("count")
            )

            # 활성화된 채팅방 개수 서브쿼리

            chat_count = (
                ChatRoom.objects.filter(product=OuterRef("pk"), status="active")
                .values("product")
                .annotate(count=Count("id"))
                .values("count")
            )

            # 쿼리 실행 및 페이지네이션 - file_id를 가져옴
            products = queryset.annotate(
                file_id=Subquery(first_image.values("file__id")[:1]),
                interest_count=Subquery(interest_count[:1]),
                chat_count=Subquery(chat_count[:1]),
            )[start_idx:end_idx]

            # 결과 변환 - 이미지가 있는 경우 URL을 별도로 조회
            product_list = []

            # 사용자 인증 동네 정보 조회 (거리 계산용)
            user_center_point = None
            try:
                from a_apis.models.region import UserActivityRegion

                active_region = (
                    UserActivityRegion.objects.filter(user_id=user_id, priority=1)
                    .select_related("activity_area")
                    .first()
                )

                if (
                    active_region
                    and active_region.activity_area
                    and active_region.activity_area.center_coordinates
                ):
                    user_center_point = active_region.activity_area.center_coordinates
            except Exception:
                # 인증 동네 조회 실패 시 무시
                pass

            for product in products:
                # 이미지 URL 별도 처리
                image_url = None
                if product.file_id:
                    # ProductImage를 통해 File 객체를 가져온 후 url 속성 접근
                    try:
                        product_image = (
                            ProductImage.objects.select_related("file")
                            .filter(product_id=product.id)
                            .first()
                        )
                        if product_image and product_image.file:
                            image_url = product_image.file.url
                    except Exception:
                        # 이미지 URL 조회 실패 시 None으로 처리
                        pass

                # 동네 정보 추가
                region_name = product.region.name if product.region else None

                # 거래장소 정보 구성
                meeting_location = None
                if product.meeting_location:
                    meeting_location = {
                        "latitude": product.meeting_location.y,
                        "longitude": product.meeting_location.x,
                        "description": product.location_description,
                        "distance_text": None,
                    }

                    # 거리 계산 (사용자 인증 동네가 있는 경우)
                    if user_center_point:
                        try:
                            distance_text = ProductService.calculate_distance_text(
                                user_center_point, product.meeting_location
                            )
                            meeting_location["distance_text"] = distance_text
                        except Exception:
                            # 거리 계산 실패 시 무시
                            pass

                product_list.append(
                    {
                        "id": product.id,
                        "title": product.title,
                        "description": product.description,
                        "price": product.price,
                        "status": product.status,
                        "trade_type": product.trade_type,
                        "created_at": product.created_at.isoformat(),
                        "refresh_at": (
                            product.refresh_at.isoformat()
                            if product.refresh_at
                            else None
                        ),
                        "image_url": image_url,
                        "seller_nickname": product.user.nickname,
                        "meeting_location": meeting_location,
                        "interest_count": product.interest_count or 0,
                        "region_name": region_name,
                    }
                )

            status_display = {
                "new": "판매중",
                "reserved": "예약중",
                "soldout": "판매완료",
            }.get(status, "전체")

            return {
                "success": True,
                "message": f"{status_display} 상품 목록이 조회되었습니다.",
                "data": product_list,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }

        except Exception as e:
            return {"success": False, "message": str(e), "data": []}

    @staticmethod
    def _product_to_detail(product, user_id=None):
        """상품 객체를 상세 정보 딕셔너리로 변환"""
        # 상품 이미지 조회
        images = []
        for image in product.images.select_related("file").all():
            images.append(
                {
                    "id": image.id,
                    "url": image.file.url,
                }
            )

        # 관심 상품 여부 확인
        is_interested = False
        if user_id:
            is_interested = InterestProduct.objects.filter(
                user_id=user_id, product=product
            ).exists()

        # 위치 정보
        location = {
            "latitude": (
                product.meeting_location.y if product.meeting_location else None
            ),
            "longitude": (
                product.meeting_location.x if product.meeting_location else None
            ),
            "description": product.location_description,
            "distance_text": None,  # 기본값
        }

        # 거리 계산 (사용자 인증 동네가 있고, 상품에 거래장소가 설정된 경우)
        if user_id and product.meeting_location:
            try:
                from a_apis.models.region import UserActivityRegion

                # 사용자의 현재 활성 동네(우선순위 1) 조회
                active_region = (
                    UserActivityRegion.objects.filter(user_id=user_id, priority=1)
                    .select_related("activity_area")
                    .first()
                )

                if active_region and active_region.activity_area.center_coordinates:
                    # 인증 동네의 중심 좌표와 거래장소 간의 거리 계산
                    user_center_point = active_region.activity_area.center_coordinates
                    meeting_point = product.meeting_location

                    distance_text = ProductService.calculate_distance_text(
                        user_center_point, meeting_point
                    )
                    location["distance_text"] = distance_text

            except Exception:
                # 거리 계산 실패 시 None으로 유지
                pass

        # 카테고리 정보
        category_data = None
        if product.category:
            category_data = {
                "id": product.category.id,
                "name": product.category.name,
                "parent_id": product.category.parent_id,
            }

        # 동네 정보 추가
        region_name = product.region.name if product.region else None

        # 판매자 정보 구성
        seller_info = {
            "id": product.user.id,
            "nickname": product.user.nickname,
            "profile_image_url": None,
            "rating_score": float(product.user.rating_score),
        }

        # 판매자 프로필 이미지 URL 처리
        if product.user.profile_img:
            seller_info["profile_image_url"] = product.user.profile_img.url

        # 가격 제안 개수 계산
        from a_user.models import PriceOffer

        price_offer_count = PriceOffer.objects.filter(
            product=product, status="pending"
        ).count()

        return {
            "id": product.id,
            "title": product.title,
            "trade_type": product.trade_type,
            "price": product.price,
            "accept_price_offer": product.accept_price_offer,
            "price_offer_count": price_offer_count,
            "description": product.description,
            "view_count": product.view_count,
            "status": product.status,
            "created_at": product.created_at.isoformat(),
            "refresh_at": (
                product.refresh_at.isoformat() if product.refresh_at else None
            ),
            "seller": seller_info,
            "meeting_location": location,
            "images": images,
            "is_interested": is_interested,
            "category": category_data,
            "region_name": region_name,
            "chat_count": ChatRoom.objects.filter(
                product=product, status="active"
            ).count(),
        }

    # 카테고리 관련 메서드 추가
    @staticmethod
    def get_categories() -> dict:
        """모든 카테고리 목록 조회 - 계층 구조로 정리된 형태"""
        try:
            # 대분류 카테고리 조회 (parent_id가 NULL)
            parent_categories = ProductCategory.objects.filter(
                parent__isnull=True
            ).order_by("order", "name")

            result = []

            # 각 대분류별로 소분류 추가
            for parent in parent_categories:
                # 대분류 정보
                parent_data = {
                    "id": parent.id,
                    "name": parent.name,
                    "parent_id": None,
                    "subcategories": [],
                }

                # 해당 대분류의 소분류 조회
                subcategories = ProductCategory.objects.filter(
                    parent_id=parent.id
                ).order_by("order", "name")

                # 소분류 정보 추가
                for sub in subcategories:
                    parent_data["subcategories"].append(
                        {"id": sub.id, "name": sub.name, "parent_id": parent.id}
                    )

                # 결과에 추가
                result.append(parent_data)

            return {
                "success": True,
                "message": "카테고리 목록을 조회했습니다.",
                "data": result,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"카테고리 목록 조회 실패: {str(e)}",
                "data": [],
            }

    @staticmethod
    def suggest_categories(title: str) -> dict:
        """상품 제목 기반 카테고리 추천"""
        try:
            if not title or not title.strip():
                return {
                    "success": True,
                    "message": "제목이 필요합니다.",
                    "data": [],
                }

            # 키워드-카테고리 매핑 (카테고리 ID 기준)
            keyword_mapping = {
                # 디지털/가전 관련 키워드
                "아이폰": 101,  # 스마트폰
                "갤럭시": 101,  # 스마트폰
                "삼성폰": 101,  # 스마트폰
                "휴대폰": 101,  # 스마트폰
                "핸드폰": 101,  # 스마트폰
                "아이패드": 102,  # 태블릿
                "갤탭": 102,  # 태블릿
                "맥북": 103,  # 노트북
                "그램": 103,  # 노트북
                "삼성북": 103,  # 노트북
                "아이맥": 104,  # 데스크탑
                "컴퓨터": 104,  # 데스크탑
                "pc": 104,  # 데스크탑
                "에어팟": 106,  # 이어폰
                "버즈": 106,  # 이어폰
                "소니": 107,  # 헤드폰
                "플스": 108,  # 게임기
                "닌텐도": 108,  # 게임기
                "플레이스테이션": 108,  # 게임기
                "엑스박스": 108,  # 게임기
                "게임기": 108,  # 게임기
                "콘솔": 108,  # 게임기
                "tv": 109,  # TV
                "텔레비전": 109,  # TV
                "티비": 109,  # TV
                "냉장고": 110,  # 냉장고
                "김치냉장고": 110,  # 냉장고
                "세탁기": 111,  # 세탁기
                "건조기": 111,  # 세탁기
                "에어컨": 112,  # 에어컨
                # 가구/인테리어 관련 키워드
                "매트리스": 201,  # 침대
                "침대": 201,  # 침대
                "쇼파": 202,  # 소파
                "소파": 202,  # 소파
                "테이블": 203,  # 책상
                "책상": 203,  # 책상
                "의자": 204,  # 의자
                "서랍": 205,  # 옷장
                "옷장": 205,  # 옷장
                "스탠드": 206,  # 조명
                "전등": 206,  # 조명
                "조명": 206,  # 조명
                "블라인드": 207,  # 커튼
                "커튼": 207,  # 커튼
                "카펫": 208,  # 러그
                "러그": 208,  # 러그
                # 의류 관련 키워드
                "원피스": 301,  # 여성의류
                "스커트": 301,  # 여성의류
                "블라우스": 301,  # 여성의류
                "셔츠": 302,  # 남성의류
                "정장": 302,  # 남성의류
                "바지": 302,  # 남성의류
                "운동화": 303,  # 신발
                "구두": 303,  # 신발
                "나이키": 303,  # 신발
                "아디다스": 303,  # 신발
                "신발": 303,  # 신발
                "백팩": 304,  # 가방
                "가방": 304,  # 가방
                "핸드백": 304,  # 가방
                "롤렉스": 305,  # 시계
                "시계": 305,  # 시계
                "목걸이": 306,  # 주얼리
                "반지": 306,  # 주얼리
                "귀걸이": 306,  # 주얼리
                "모자": 307,  # 모자
                "양말": 308,  # 양말
                # 도서/티켓/취미 관련 키워드
                "책": 401,  # 도서
                "소설": 401,  # 도서
                "도서": 401,  # 도서
                "교재": 401,  # 도서
                "음반": 402,  # 음반
                "cd": 402,  # 음반
                "공연": 403,  # 공연티켓
                "콘서트": 403,  # 공연티켓
                "영화": 404,  # 영화티켓
                "상품권": 405,  # 상품권
                "게임": 406,  # 게임
                "기타": 407,  # 음악악기
                "피아노": 407,  # 음악악기
                "미술": 408,  # 미술용품
                "그림": 408,  # 미술용품
                # 생활/식품 관련 키워드
                "식칼": 501,  # 주방용품
                "칼": 501,  # 주방용품
                "냄비": 501,  # 주방용품
                "프라이팬": 501,  # 주방용품
                "그릇": 501,  # 주방용품
                "수저": 501,  # 주방용품
                "젓가락": 501,  # 주방용품
                "도마": 501,  # 주방용품
                "주방": 501,  # 주방용품
                "생활용품": 502,  # 생활용품
                "세제": 502,  # 생활용품
                "화장지": 502,  # 생활용품
                "청소": 502,  # 생활용품
                "빨래": 502,  # 생활용품
                "음식": 503,  # 식품
                "식품": 503,  # 식품
                "과자": 503,  # 식품
                "라면": 503,  # 식품
                "쌀": 503,  # 식품
                "햄버거": 503,  # 식품
                "피자": 503,  # 식품
                "치킨": 503,  # 식품
                "건강식품": 504,  # 건강식품
                "비타민": 504,  # 건강식품
                "영양제": 504,  # 건강식품
                "커피": 505,  # 커피/차
                "차": 505,  # 커피/차
                "녹차": 505,  # 커피/차
                "홍차": 505,  # 커피/차
                # 뷰티/미용 관련 키워드
                "화장품": 601,  # 스킨케어
                "스킨케어": 601,  # 스킨케어
                "크림": 601,  # 스킨케어
                "로션": 601,  # 스킨케어
                "메이크업": 602,  # 메이크업
                "립스틱": 602,  # 메이크업
                "파운데이션": 602,  # 메이크업
                "헤어": 603,  # 헤어케어
                "샴푸": 603,  # 헤어케어
                "바디": 604,  # 바디케어
                "향수": 605,  # 향수
                "네일": 606,  # 네일아트
                # 스포츠/레저 관련 키워드
                "자전거": 701,  # 자전거
                "인라인": 702,  # 인라인스케이트
                "스케이트": 702,  # 인라인스케이트
                "테니스": 703,  # 테니스
                "배드민턴": 704,  # 배드민턴
                "골프": 705,  # 골프
                "등산": 706,  # 등산
                "캠핑": 707,  # 캠핑
                "낚시": 708,  # 낚시
                "운동": 7,  # 스포츠/레저 대분류
                "스포츠": 7,  # 스포츠/레저 대분류
                # 유아동/출산 관련 키워드
                "유아": 8,  # 유아동/출산 대분류
                "아기": 8,  # 유아동/출산 대분류
                "아이": 8,  # 유아동/출산 대분류
                "기저귀": 8,  # 유아동/출산 대분류
                "분유": 804,  # 유아식품
                "이유식": 804,  # 유아식품
                "젖병": 8,  # 유아동/출산 대분류
                "유모차": 805,  # 유모차
                "아기띠": 806,  # 아기띠
                "임부복": 807,  # 임부복
                "장난감": 803,  # 장난감
                # 반려동물용품 관련 키워드
                "강아지": 9,  # 반려동물용품 대분류
                "고양이": 9,  # 반려동물용품 대분류
                "개": 9,  # 반려동물용품 대분류
                "고양": 9,  # 반려동물용품 대분류
                "사료": 901,  # 사료
                "간식": 902,  # 간식
                "펫": 9,  # 반려동물용품 대분류
                "애완": 9,  # 반려동물용품 대분류
                "반려": 9,  # 반려동물용품 대분류
                "동물": 9,  # 반려동물용품 대분류
            }

            # 제목에 포함된 키워드로 카테고리 검색
            # 1. 단어 단위로 분리하여 각 단어로 검색
            words = title.lower().split()  # 소문자로 변환하여 대소문자 구분 없앰
            categories = set()
            matched_keywords = set()

            # 키워드 매핑 기반 검색
            for word in words:
                if len(word) >= 1 and word in keyword_mapping:  # 매핑된 키워드 확인
                    category_id = keyword_mapping[word]
                    try:
                        category = ProductCategory.objects.get(id=category_id)
                        categories.add(category)
                        matched_keywords.add(word)
                    except ProductCategory.DoesNotExist:
                        pass

            # 이름 기반 검색 (키워드 매핑에서 찾지 못한 단어에 대해)
            for word in words:
                if (
                    len(word) >= 1 and word not in matched_keywords
                ):  # 이미 매칭된 키워드는 제외
                    found_categories = ProductCategory.objects.filter(
                        name__icontains=word
                    ).order_by("order", "name")[
                        :5
                    ]  # 최대 5개

                    for category in found_categories:
                        categories.add(category)

            # 결과 변환
            result = []
            for category in categories:
                result.append(
                    {
                        "id": category.id,
                        "name": category.name,
                        "parent_id": category.parent_id,
                    }
                )

            # 결과가 없으면 빈 배열 반환 (기본값 제거)
            message = (
                "카테고리를 추천했습니다."
                if result
                else "일치하는 카테고리를 찾을 수 없습니다."
            )

            return {
                "success": True,
                "message": message,
                "data": result[:5],  # 최대 5개로 제한
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"카테고리 추천 실패: {str(e)}",
                "data": [],
            }

    @staticmethod
    def create_price_offer(
        product_id: int, user_id: int, price: int, chat_room_id: int = None
    ) -> dict:
        """가격 제안 서비스"""
        try:
            # 상품 조회
            product = Product.objects.select_related("user").get(id=product_id)

            # 자신의 상품에는 제안 불가
            if product.user_id == user_id:
                return {
                    "success": False,
                    "message": "자신의 상품에는 가격 제안을 할 수 없습니다.",
                }

            # 거래 완료된 상품인지 확인
            if product.status == Product.Status.SOLDOUT:
                return {"success": False, "message": "이미 판매 완료된 상품입니다."}

            # 가격 제안 허용 여부 확인
            if not product.accept_price_offer:
                return {
                    "success": False,
                    "message": "이 상품은 가격 제안을 허용하지 않습니다.",
                }

            # 가격 범위 체크 (원래 가격의 50~150% 범위 내에서만 허용)
            if product.price:
                min_price = max(1, int(product.price * 0.5))
                max_price = int(product.price * 1.5)

                if price < min_price or price > max_price:
                    return {
                        "success": False,
                        "message": f"가격 제안은 원래 가격({product.price}원)의 50% ~ 150% 범위 내에서만 가능합니다.",
                    }

            # 채팅방 확인 (제공된 경우)

            chat_room = None
            if chat_room_id:
                try:
                    chat_room = ChatRoom.objects.get(
                        id=chat_room_id, product_id=product_id
                    )
                except ChatRoom.DoesNotExist:
                    return {"success": False, "message": "유효하지 않은 채팅방입니다."}

            # 중복 제안 확인
            from a_user.models import PriceOffer

            existing_offer = PriceOffer.objects.filter(
                product_id=product_id, user_id=user_id, status="pending"
            ).exists()

            if existing_offer:
                # 기존 제안 업데이트
                offer = PriceOffer.objects.get(
                    product_id=product_id, user_id=user_id, status="pending"
                )
                offer.price = price
                offer.save(update_fields=["price", "updated_at"])
                message = "가격 제안이 업데이트되었습니다."
            else:
                # 새 제안 생성
                from a_user.models import User

                user = User.objects.get(id=user_id)
                offer = PriceOffer.objects.create(
                    product_id=product_id,
                    user_id=user_id,
                    price=price,
                    chat_room_id=chat_room_id if chat_room_id else None,
                )
                message = "가격 제안이 등록되었습니다."

            return {
                "success": True,
                "message": message,
                "data": {
                    "id": offer.id,
                    "product_id": product_id,
                    "product_title": product.title,
                    "user_id": user_id,
                    "user_nickname": user.nickname,
                    "price": price,
                    "status": offer.status,
                    "created_at": offer.created_at.isoformat(),
                },
            }

        except Product.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 상품입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def respond_to_price_offer(offer_id: int, user_id: int, action: str) -> dict:
        """가격 제안 수락/거절 서비스"""
        try:
            from a_user.models import PriceOffer

            offer = PriceOffer.objects.select_related("product", "user").get(
                id=offer_id
            )

            # 상품 소유자 확인
            if offer.product.user_id != user_id:
                return {
                    "success": False,
                    "message": "이 제안에 대한 응답 권한이 없습니다.",
                }

            # 이미 처리된 제안인지 확인
            if offer.status != "pending":
                status_display = {
                    "accepted": "수락",
                    "rejected": "거절",
                    "pending": "대기중",
                }
                return {
                    "success": False,
                    "message": f"이미 {status_display.get(offer.status)}된 제안입니다.",
                }

            # 수락 또는 거절 처리
            if action == "accept":
                offer.status = "accepted"
                # 다른 대기중인 제안 모두 거절
                PriceOffer.objects.filter(
                    product_id=offer.product.id, status="pending"
                ).exclude(id=offer_id).update(status="rejected")

                # 수락 시 상품 가격 업데이트
                offer.product.price = offer.price
                offer.product.save(update_fields=["price", "updated_at"])

                message = "가격 제안을 수락했습니다."
            else:  # reject
                offer.status = "rejected"
                message = "가격 제안을 거절했습니다."

            offer.save(update_fields=["status", "updated_at"])

            return {
                "success": True,
                "message": message,
                "data": {
                    "id": offer.id,
                    "product_id": offer.product.id,
                    "product_title": offer.product.title,
                    "user_id": offer.user.id,
                    "user_nickname": offer.user.nickname,
                    "price": offer.price,
                    "status": offer.status,
                    "created_at": offer.created_at.isoformat(),
                },
            }

        except PriceOffer.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 가격 제안입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_price_offers(product_id: int, user_id: int) -> dict:
        """상품 가격 제안 목록 조회 서비스"""
        try:
            product = Product.objects.get(id=product_id)

            # 권한 확인 (판매자만 조회 가능)
            if product.user_id != user_id:
                return {"success": False, "message": "가격 제안 조회 권한이 없습니다."}

            # 제안 목록 조회
            from a_user.models import PriceOffer

            offers = (
                PriceOffer.objects.filter(product_id=product_id)
                .select_related("user")
                .order_by("-created_at")
            )

            data = []
            for offer in offers:
                data.append(
                    {
                        "id": offer.id,
                        "product_id": product_id,
                        "product_title": product.title,
                        "user_id": offer.user.id,
                        "user_nickname": offer.user.nickname,
                        "price": offer.price,
                        "status": offer.status,
                        "created_at": offer.created_at.isoformat(),
                    }
                )

            return {
                "success": True,
                "message": "가격 제안 목록을 조회했습니다.",
                "data": data,
            }

        except Product.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 상품입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def complete_trade(
        product_id: int, user_id: int, buyer_id: int, final_price: int = None
    ) -> dict:
        """거래 완료 처리 서비스"""
        try:
            product = Product.objects.get(id=product_id)

            # 판매자 확인
            if product.user_id != user_id:
                return {"success": False, "message": "거래 완료 처리 권한이 없습니다."}

            # 이미 판매 완료된 상품인지 확인
            if product.status == Product.Status.SOLDOUT:
                return {"success": False, "message": "이미 판매 완료된 상품입니다."}

            # 구매자 확인
            from a_user.models import User

            try:
                buyer = User.objects.get(id=buyer_id)
            except User.DoesNotExist:
                return {"success": False, "message": "존재하지 않는 구매자입니다."}

            # 판매자와 구매자가 동일한지 확인
            if buyer.id == user_id:
                return {"success": False, "message": "자신에게 판매할 수 없습니다."}

            # 거래 완료 처리
            result = product.mark_as_completed(buyer, final_price)
            if not result:
                return {"success": False, "message": "거래 완료 처리에 실패했습니다."}

            return {
                "success": True,
                "message": "상품이 거래 완료 처리되었습니다.",
                "data": ProductService._product_to_detail(product, user_id),
            }

        except Product.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 상품입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def create_review(product_id: int, user_id: int, content: str) -> dict:
        """거래 후기 작성 서비스"""
        try:
            product = Product.objects.select_related("user").get(id=product_id)

            # 거래 완료된 상품인지 확인
            if product.status != Product.Status.SOLDOUT:
                return {
                    "success": False,
                    "message": "거래 완료된 상품에만 후기를 작성할 수 있습니다.",
                }

            # 거래 당사자(판매자 또는 구매자)인지 확인
            if user_id != product.user_id and user_id != product.buyer_id:
                return {
                    "success": False,
                    "message": "거래 당사자만 후기를 작성할 수 있습니다.",
                }

            # 이미 후기를 작성했는지 확인
            from a_user.models import Review

            if Review.objects.filter(
                product_id=product_id, reviewer_id=user_id
            ).exists():
                return {"success": False, "message": "이미 후기를 작성했습니다."}

            # 판매자가 작성하는지 구매자가 작성하는지 파악
            is_seller = user_id == product.user_id

            # 후기 수신자 설정
            receiver_id = product.buyer_id if is_seller else product.user_id

            # 후기 작성
            from a_user.models import User

            review = Review.objects.create(
                product_id=product_id,
                reviewer_id=user_id,
                receiver_id=receiver_id,
                content=content,
            )

            # 후기 작성 완료 상태로 업데이트
            if product.trade_complete_status == Product.TradeCompleteStatus.COMPLETED:
                product.trade_complete_status = Product.TradeCompleteStatus.REVIEWED
                product.save(update_fields=["trade_complete_status", "updated_at"])

            return {
                "success": True,
                "message": "거래 후기가 등록되었습니다.",
                "data": {
                    "id": review.id,
                    "product_id": product_id,
                    "product_title": product.title,
                    "reviewer_id": user_id,
                    "receiver_id": receiver_id,
                    "content": content,
                    "created_at": review.created_at.isoformat(),
                },
            }

        except Product.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 상품입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def create_manner_rating(product_id: int, user_id: int, rating_types: list) -> dict:
        """매너 평가 등록 서비스"""
        try:
            product = Product.objects.select_related("user").get(id=product_id)

            # 거래 완료된 상품인지 확인
            if product.status != Product.Status.SOLDOUT:
                return {
                    "success": False,
                    "message": "거래 완료된 상품에만 매너 평가를 등록할 수 있습니다.",
                }

            # 거래 당사자(판매자 또는 구매자)인지 확인
            if user_id != product.user_id and user_id != product.buyer_id:
                return {
                    "success": False,
                    "message": "거래 당사자만 매너 평가를 등록할 수 있습니다.",
                }

            # 판매자가 작성하는지 구매자가 작성하는지 파악
            is_seller = user_id == product.user_id

            # 평가 대상자 설정
            rated_user_id = product.buyer_id if is_seller else product.user_id

            # 매너 평가 유효성 검사
            from a_user.models import MannerRating

            valid_types = [choice[0] for choice in MannerRating.MANNER_TYPES]
            invalid_types = [rt for rt in rating_types if rt not in valid_types]
            if invalid_types:
                return {
                    "success": False,
                    "message": f"유효하지 않은 평가 유형입니다: {', '.join(invalid_types)}",
                }

            # 이미 등록한 평가 유형 확인
            existing_types = MannerRating.objects.filter(
                product_id=product_id,
                rater_id=user_id,
            ).values_list("rating_type", flat=True)

            new_types = [rt for rt in rating_types if rt not in existing_types]
            if not new_types:
                return {
                    "success": False,
                    "message": "이미 모든 유형의 평가를 등록했습니다.",
                }

            # 새 평가 등록
            ratings = []
            for rating_type in new_types:
                rating = MannerRating.objects.create(
                    product_id=product_id,
                    rater_id=user_id,
                    rated_user_id=rated_user_id,
                    rating_type=rating_type,
                )
                ratings.append(rating)

            # 매너 평가 완료 상태로 업데이트
            if product.trade_complete_status in [
                Product.TradeCompleteStatus.COMPLETED,
                Product.TradeCompleteStatus.REVIEWED,
            ]:
                product.trade_complete_status = Product.TradeCompleteStatus.RATED
                product.save(update_fields=["trade_complete_status", "updated_at"])

            return {
                "success": True,
                "message": "매너 평가가 등록되었습니다.",
                "data": {
                    "product_id": product_id,
                    "product_title": product.title,
                    "rating_types": new_types,
                    "created_at": timezone.now().isoformat(),
                },
            }

        except Product.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 상품입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_review(product_id, user_id):
        """
        거래 후기 조회 메서드
        product_id: 거래가 완료된 상품 ID
        user_id: 후기를 조회하는 사용자 ID
        """
        try:
            product = Product.objects.get(id=product_id)

            # 거래가 완료된 상품인지 확인
            if product.status != "sold":
                return {
                    "success": False,
                    "message": "거래가 완료된 상품만 후기를 조회할 수 있습니다.",
                    "data": None,
                }

            # 해당 상품에 대한 후기 조회
            # 판매자가 조회하면 구매자가 작성한 후기를, 구매자가 조회하면 판매자가 작성한 후기를 조회
            if user_id == product.user_id:  # 판매자가 조회 중
                review = Review.objects.filter(
                    product=product, reviewer=product.buyer
                ).first()
            elif user_id == product.buyer_id:  # 구매자가 조회 중
                review = Review.objects.filter(
                    product=product, reviewer=product.user
                ).first()
            else:
                return {
                    "success": False,
                    "message": "거래 당사자만 후기를 조회할 수 있습니다.",
                    "data": None,
                }

            if not review:
                return {
                    "success": False,
                    "message": "작성된 후기가 없습니다.",
                    "data": None,
                }

            return {
                "success": True,
                "message": "거래 후기를 조회했습니다.",
                "data": {
                    "id": review.id,
                    "product_id": product.id,
                    "product_title": product.title,
                    "reviewer_id": review.reviewer.id,
                    "reviewer_nickname": review.reviewer.nickname,
                    "receiver_id": review.receiver.id,
                    "receiver_nickname": review.receiver.nickname,
                    "content": review.content,
                    "created_at": review.created_at.isoformat(),
                    "updated_at": (
                        review.updated_at.isoformat() if review.updated_at else None
                    ),
                },
            }
        except Product.DoesNotExist:
            return {
                "success": False,
                "message": "존재하지 않는 상품입니다.",
                "data": None,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"후기 조회 중 오류가 발생했습니다: {str(e)}",
                "data": None,
            }

    @staticmethod
    def update_review(review_id, user_id, content):
        """
        거래 후기 수정 메서드
        review_id: 수정할 후기 ID
        user_id: 후기를 수정하는 사용자 ID
        content: 수정할 후기 내용
        """
        try:
            review = Review.objects.get(id=review_id)

            # 자신이 작성한 후기인지 확인
            if review.reviewer_id != user_id:
                return {
                    "success": False,
                    "message": "자신이 작성한 후기만 수정할 수 있습니다.",
                    "data": None,
                }

            # 후기 내용 수정
            review.content = content
            review.updated_at = timezone.now()
            review.save()

            return {
                "success": True,
                "message": "거래 후기가 수정되었습니다.",
                "data": {
                    "id": review.id,
                    "product_id": review.product.id,
                    "product_title": review.product.title,
                    "reviewer_id": review.reviewer.id,
                    "reviewer_nickname": review.reviewer.nickname,
                    "receiver_id": review.receiver.id,
                    "receiver_nickname": review.receiver.nickname,
                    "content": review.content,
                    "created_at": review.created_at.isoformat(),
                    "updated_at": (
                        review.updated_at.isoformat() if review.updated_at else None
                    ),
                },
            }
        except Review.DoesNotExist:
            return {
                "success": False,
                "message": "존재하지 않는 후기입니다.",
                "data": None,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"후기 수정 중 오류가 발생했습니다: {str(e)}",
                "data": None,
            }

    @staticmethod
    def get_manner_ratings(user_id, page=1, page_size=20):
        """사용자의 매너 평가 목록 조회 메서드"""
        try:
            from django.core.paginator import Paginator

            # 해당 사용자가 받은 모든 매너 평가 목록 조회
            ratings = (
                MannerRating.objects.filter(rated_user_id=user_id)
                .select_related("product", "rater", "rated_user")
                .order_by("-created_at")
            )

            # 페이지네이션 적용
            paginator = Paginator(ratings, page_size)
            current_page = paginator.page(page)

            # 응답 데이터 구성
            ratings_data = []
            for rating in current_page.object_list:
                ratings_data.append(
                    {
                        "id": rating.id,
                        "product_id": rating.product.id,
                        "product_title": rating.product.title,
                        "rater_id": rating.rater.id,
                        "rater_nickname": rating.rater.nickname,
                        "rated_user_id": rating.rated_user.id,
                        "rated_user_nickname": rating.rated_user.nickname,
                        "rating_type": rating.rating_type,
                        "rating_display": rating.get_rating_type_display(),
                        "created_at": rating.created_at.isoformat(),
                    }
                )

            return {
                "success": True,
                "message": "매너 평가 목록을 조회했습니다.",
                "data": ratings_data,
                "total_count": paginator.count,
                "page": page,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"매너 평가 목록 조회 중 오류가 발생했습니다: {str(e)}",
                "data": None,
            }

    @staticmethod
    def get_products_by_keyword_in_region(
        user_id: int, keyword: str, radius: float = 3.0, limit: int = 30
    ) -> dict:
        """
        활동지역 범위 내에서 키워드와 관련된 상품 추천 서비스

        Args:
            user_id: 요청한 사용자 ID
            keyword: 검색 키워드
            radius: 검색 반경 (km 단위, 기본값 3km)
            limit: 반환할 상품 개수 (기본값 30개)

        Returns:
            dict: 검색 결과 및 메타데이터
        """
        try:
            from a_apis.models.region import UserActivityRegion

            from django.contrib.gis.db.models.functions import Distance
            from django.contrib.gis.measure import D

            # 사용자의 활동 지역 중 우선순위가 가장 높은 지역 찾기
            user_region = (
                UserActivityRegion.objects.filter(user_id=user_id, priority=1)
                .select_related("activity_area")
                .first()
            )

            if not user_region or not user_region.activity_area.center_coordinates:
                return {
                    "success": False,
                    "message": "활동 지역이 설정되지 않았습니다.",
                }

            # 사용자의 중심 위치
            user_location = user_region.activity_area.center_coordinates

            # 반경 내 상품 검색 및 키워드로 필터링
            # DWithin에서는 도(degree) 단위를 사용해야 함
            # 대략적으로 1도 = 111km 이므로 km를 도로 변환
            radius_in_degrees = radius / 111.0

            queryset = (
                Product.objects.exclude(user_id=user_id)
                .filter(
                    meeting_location__dwithin=(user_location, radius_in_degrees),
                    status="new",  # 판매중인 상품만
                )
                .annotate(distance=Distance("meeting_location", user_location))
                .order_by("distance")
            )

            # 키워드 필터링
            if keyword:
                queryset = queryset.filter(
                    Q(title__icontains=keyword) | Q(description__icontains=keyword)
                )

            # 총 개수 파악
            total_count = queryset.count()

            # 첫 번째 이미지 ID 서브쿼리
            first_image = (
                ProductImage.objects.filter(product=OuterRef("pk"))
                .select_related("file")
                .order_by("created_at")
            )

            # 관심 수 계산 서브쿼리
            interest_count = (
                InterestProduct.objects.filter(product=OuterRef("pk"))
                .values("product")
                .annotate(count=Count("id"))
                .values("count")
            )

            # 활성화된 채팅방 개수 서브쿼리

            chat_count = (
                ChatRoom.objects.filter(product=OuterRef("pk"), status="active")
                .values("product")
                .annotate(count=Count("id"))
                .values("count")
            )

            # 쿼리 실행 및 제한
            products = queryset.select_related("user", "region").annotate(
                file_id=Subquery(first_image.values("file__id")[:1]),
                interest_count=Subquery(interest_count[:1]),
                chat_count=Subquery(chat_count[:1]),
            )[:limit]

            # 결과 변환
            product_list = []
            for product in products:
                # 이미지 URL 가져오기
                image_url = None
                if product.file_id:
                    from a_apis.models import File

                    file_obj = File.objects.filter(id=product.file_id).first()
                    if file_obj:
                        image_url = file_obj.url

                # 거리 텍스트 계산
                distance_text = ProductService.calculate_distance_text(
                    user_location, product.meeting_location
                )

                is_interested = False
                if user_id:
                    # 관심상품 여부 확인
                    is_interested = InterestProduct.objects.filter(
                        user_id=user_id, product_id=product.id
                    ).exists()

                product_data = {
                    "id": product.id,
                    "title": product.title,
                    "price": product.price,
                    "trade_type": product.trade_type,
                    "status": product.status,
                    "image_url": image_url,
                    "region_name": product.region.name if product.region else None,
                    "distance_text": distance_text,
                    "interest_count": product.interest_count or 0,
                    "chat_count": product.chat_count or 0,
                    "created_at": product.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "refresh_at": (
                        product.refresh_at.strftime("%Y-%m-%d %H:%M:%S")
                        if product.refresh_at
                        else None
                    ),
                    "is_interested": is_interested,
                    "seller_nickname": product.user.nickname,
                }
                product_list.append(product_data)

            return {
                "success": True,
                "message": f"'{keyword}' 키워드 관련 근처 상품 {len(product_list)}개를 조회했습니다.",
                "data": {
                    "products": product_list,
                    "total_count": total_count,
                    "keyword": keyword,
                    "radius": radius,
                    "user_region": user_region.activity_area.name,
                },
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_user_sales_products(
        user_id: int,
        target_user_id: int,
        status: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        특정 유저의 판매 상품 목록 조회 서비스

        Args:
            user_id: 요청한 사용자 ID (권한 확인용)
            target_user_id: 조회할 타겟 사용자 ID
            status: 필터링할 상품 상태 (new, reserved, soldout)
            page: 페이지 번호
            page_size: 페이지 크기

        Returns:
            dict: 조회 결과 및 메타데이터
        """
        try:
            # 기본 쿼리셋 (특정 유저의 상품만)
            queryset = (
                Product.objects.filter(user_id=target_user_id)
                .select_related("user", "region")
                .order_by("-refresh_at", "-created_at")
            )

            # 상태로 필터링 (있는 경우)
            if status:
                queryset = queryset.filter(status=status)

            # 페이지네이션 적용
            total_count = queryset.count()
            total_pages = math.ceil(total_count / page_size)

            # 페이지 범위 설정
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            # 첫 번째 이미지 ID 서브쿼리
            first_image = (
                ProductImage.objects.filter(product=OuterRef("pk"))
                .select_related("file")
                .order_by("created_at")
            )

            # 관심 수 계산 서브쿼리
            interest_count = (
                InterestProduct.objects.filter(product=OuterRef("pk"))
                .values("product")
                .annotate(count=Count("id"))
                .values("count")
            )

            # 활성화된 채팅방 개수 서브쿼리

            chat_count = (
                ChatRoom.objects.filter(product=OuterRef("pk"), status="active")
                .values("product")
                .annotate(count=Count("id"))
                .values("count")
            )

            # 쿼리 실행 및 페이지네이션
            products = queryset.annotate(
                file_id=Subquery(first_image.values("file__id")[:1]),
                interest_count=Subquery(interest_count[:1]),
                chat_count=Subquery(chat_count[:1]),
            )[start_idx:end_idx]

            # 결과 변환
            product_list = []

            # 사용자 인증 동네 정보 조회 (거리 계산용)
            user_center_point = None
            if user_id:
                from a_apis.models.region import UserActivityRegion

                active_region = (
                    UserActivityRegion.objects.filter(user_id=user_id, priority=1)
                    .select_related("activity_area")
                    .first()
                )

                if active_region and active_region.activity_area.center_coordinates:
                    user_center_point = active_region.activity_area.center_coordinates

            for product in products:
                # 이미지 URL 가져오기
                image_url = None
                if product.file_id:
                    from a_apis.models import File

                    file_obj = File.objects.filter(id=product.file_id).first()
                    if file_obj:
                        image_url = file_obj.url

                # 거리 텍스트 계산
                distance_text = None
                if user_center_point and product.meeting_location:
                    distance_text = ProductService.calculate_distance_text(
                        user_center_point, product.meeting_location
                    )

                is_interested = False
                if user_id:
                    # 관심상품 여부 확인
                    is_interested = InterestProduct.objects.filter(
                        user_id=user_id, product_id=product.id
                    ).exists()

                product_data = {
                    "id": product.id,
                    "title": product.title,
                    "price": product.price,
                    "trade_type": product.trade_type,
                    "status": product.status,
                    "image_url": image_url,
                    "region_name": product.region.name if product.region else None,
                    "distance_text": distance_text,
                    "interest_count": product.interest_count or 0,
                    "chat_count": product.chat_count or 0,
                    "created_at": product.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "refresh_at": (
                        product.refresh_at.strftime("%Y-%m-%d %H:%M:%S")
                        if product.refresh_at
                        else None
                    ),
                    "is_interested": is_interested,
                    "seller_nickname": product.user.nickname,
                }
                product_list.append(product_data)

            # 타겟 유저 정보
            from a_user.models import User

            target_user = User.objects.get(id=target_user_id)

            # 페이지네이션 메타데이터
            pagination_data = {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            }

            status_display = {
                "new": "판매중",
                "reserved": "예약중",
                "soldout": "판매완료",
            }.get(status, "전체")

            return {
                "success": True,
                "message": f"{target_user.nickname}님의 {status_display} 상품 목록을 조회했습니다.",
                "data": {
                    "products": product_list,
                    "pagination": pagination_data,
                    "target_user": {
                        "id": target_user.id,
                        "nickname": target_user.nickname,
                    },
                },
            }
        except User.DoesNotExist:
            return {"success": False, "message": "존재하지 않는 사용자입니다."}
        except Exception as e:
            return {"success": False, "message": str(e)}
