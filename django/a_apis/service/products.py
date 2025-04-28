import math
from datetime import datetime, timedelta

from a_apis.models import InterestProduct, Product, ProductCategory, ProductImage
from a_apis.service.files import FileService

from django.contrib.gis.geos import Point
from django.db import transaction
from django.db.models import Count, OuterRef, Q, Subquery
from django.utils import timezone


class ProductService:
    @staticmethod
    def get_product_model():
        """Product 모델 반환 (테스트 모킹 용이성 위함)"""
        return Product

    @staticmethod
    @transaction.atomic
    def create_product(user_id: int, data: dict, images: list = None) -> dict:
        try:
            # 거래 위치 생성
            meeting_point = Point(
                data.meeting_location.longitude,
                data.meeting_location.latitude,
                srid=4326,
            )

            # 상품 생성
            product = Product.objects.create(
                user_id=user_id,
                title=data.title,
                trade_type=data.trade_type,
                price=data.price if data.trade_type == "sale" else None,
                accept_price_offer=data.accept_price_offer,
                description=data.description,
                category_id=data.category_id,  # 카테고리 필드 추가
                meeting_location=meeting_point,
                location_description=data.meeting_location.description,
                refresh_at=timezone.now(),  # 등록 시점으로 refresh_at 설정
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
        """상품 목록 조회 서비스"""
        try:
            # 기본 쿼리셋
            queryset = Product.objects.select_related("user").order_by("-refresh_at")

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

            # 페이지네이션 파라미터
            page = int(filter_params.get("page", 1))
            page_size = int(filter_params.get("page_size", 20))

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

            # 쿼리 실행 및 페이지네이션 - URL 대신 file_id를 가져옴
            products = queryset.annotate(
                file_id=Subquery(first_image.values("file__id")[:1]),
                interest_count=Subquery(interest_count[:1]),
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

                product_list.append(
                    {
                        "id": product.id,
                        "title": product.title,
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
                        "location_description": product.location_description,
                        "interest_count": product.interest_count or 0,
                    }
                )

            return {
                "success": True,
                "message": "상품 목록이 조회되었습니다.",
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
            product = Product.objects.select_related("user").get(id=product_id)

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
                .select_related("user")
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

            # 쿼리 실행 및 페이지네이션 - URL 대신 file_id를 가져옴
            products = queryset.annotate(
                file_id=Subquery(first_image.values("file__id")[:1]),
                interest_count=Subquery(interest_count[:1]),
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

                product_list.append(
                    {
                        "id": product.id,
                        "title": product.title,
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
                        "location_description": product.location_description,
                        "interest_count": product.interest_count or 0,
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
            queryset = Product.objects.filter(user_id=user_id).order_by("-refresh_at")

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

            # 쿼리 실행 및 페이지네이션 - file_id를 가져옴
            products = queryset.annotate(
                file_id=Subquery(first_image.values("file__id")[:1]),
                interest_count=Subquery(interest_count[:1]),
            )[start_idx:end_idx]

            # 결과 변환 - 이미지가 있는 경우 URL을 별도로 조회
            product_list = []
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

                product_list.append(
                    {
                        "id": product.id,
                        "title": product.title,
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
                        "location_description": product.location_description,
                        "interest_count": product.interest_count or 0,
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
        }

        # 카테고리 정보
        category_data = None
        if product.category:
            category_data = {
                "id": product.category.id,
                "name": product.category.name,
                "parent_id": product.category.parent_id,
            }

        return {
            "id": product.id,
            "title": product.title,
            "trade_type": product.trade_type,
            "price": product.price,
            "accept_price_offer": product.accept_price_offer,
            "description": product.description,
            "view_count": product.view_count,
            "status": product.status,
            "created_at": product.created_at.isoformat(),
            "refresh_at": (
                product.refresh_at.isoformat() if product.refresh_at else None
            ),
            "seller_nickname": product.user.nickname,
            "seller_id": product.user.id,
            "meeting_location": location,
            "images": images,
            "is_interested": is_interested,
            "category": category_data,
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
            if not title or len(title) < 2:
                return {
                    "success": True,
                    "message": "제목이 너무 짧습니다.",
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
                # 가구/인테리어 관련 키워드
                "매트리스": 201,  # 침대
                "쇼파": 202,  # 소파
                "테이블": 203,  # 책상
                "책상": 203,  # 책상
                "의자": 204,  # 의자
                "서랍": 205,  # 옷장
                "스탠드": 206,  # 조명
                "전등": 206,  # 조명
                "블라인드": 207,  # 커튼
                "카펫": 208,  # 러그
                # 의류 관련 키워드
                "원피스": 301,  # 여성의류
                "스커트": 301,  # 여성의류
                "블라우스": 301,  # 여성의류
                "셔츠": 302,  # 남성의류
                "정장": 302,  # 남성의류
                "운동화": 303,  # 신발
                "구두": 303,  # 신발
                "나이키": 303,  # 신발
                "아디다스": 303,  # 신발
                "백팩": 304,  # 가방
                "롤렉스": 305,  # 시계
                "목걸이": 306,  # 주얼리
                "반지": 306,  # 주얼리
                "귀걸이": 306,  # 주얼리
                "모자": 307,  # 모자
                "양말": 308,  # 양말
            }

            # 제목에 포함된 키워드로 카테고리 검색
            # 1. 단어 단위로 분리하여 각 단어로 검색
            words = title.lower().split()  # 소문자로 변환하여 대소문자 구분 없앰
            categories = set()
            matched_keywords = set()

            # 키워드 매핑 기반 검색
            for word in words:
                if len(word) >= 2 and word in keyword_mapping:  # 매핑된 키워드 확인
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
                    len(word) >= 2 and word not in matched_keywords
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

            # 결과가 없으면 대분류 제안
            if not result:
                # 디지털/가전 카테고리 기본 제안
                try:
                    digital_category = ProductCategory.objects.get(id=1)  # 디지털/가전
                    result.append(
                        {
                            "id": digital_category.id,
                            "name": digital_category.name,
                            "parent_id": digital_category.parent_id,
                        }
                    )
                except ProductCategory.DoesNotExist:
                    pass

            return {
                "success": True,
                "message": "추천 카테고리를 조회했습니다.",
                "data": result[:5],  # 최대 5개로 제한
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"카테고리 추천 실패: {str(e)}",
                "data": [],
            }
