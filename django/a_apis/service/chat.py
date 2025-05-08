import math

from a_apis.models import (
    ChatMessage,
    ChatRoom,
    ChatRoomParticipant,
    File,
    Product,
    ProductImage,
)
from a_apis.models.trade import TradeAppointment

from django.contrib.gis.geos import Point
from django.db.models import Count, F, Max, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce


class ChatService:
    @staticmethod
    def create_chat_room(product_id: int, user_id: int) -> dict:
        """채팅방 생성 서비스"""
        try:
            # 상품 조회
            product = Product.objects.select_related("user").get(id=product_id)

            # 자신의 상품에 대해 채팅방 생성 방지
            if product.user_id == user_id:
                return {
                    "success": False,
                    "message": "자신의 상품에 대해 채팅을 시작할 수 없습니다.",
                    "data": None,
                }

            # 이미 해당 상품에 대한 채팅방이 있는지 확인
            existing_chat = ChatRoom.objects.filter(
                product_id=product_id,
                participants__user_id=user_id,
                participants__is_active=True,
            ).first()

            if existing_chat:
                return {
                    "success": True,
                    "message": "이미 존재하는 채팅방입니다.",
                    "data": {"id": existing_chat.id},
                }

            # 새 채팅방 생성
            chat_room = ChatRoom.objects.create(
                product=product, status=ChatRoom.Status.ACTIVE
            )

            # 구매자(현재 사용자) 객체 가져오기
            from a_user.models import User

            buyer = User.objects.get(id=user_id)

            # 판매자와 구매자를 참여자로 추가
            ChatRoomParticipant.objects.create(
                chat_room=chat_room, user=product.user, is_active=True
            )

            ChatRoomParticipant.objects.create(
                chat_room=chat_room, user=buyer, is_active=True
            )

            return {
                "success": True,
                "message": "채팅방이 생성되었습니다.",
                "data": {"id": chat_room.id},
            }

        except Product.DoesNotExist:
            return {
                "success": False,
                "message": "존재하지 않는 상품입니다.",
                "data": None,
            }
        except User.DoesNotExist:
            return {
                "success": False,
                "message": "존재하지 않는 사용자입니다.",
                "data": None,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"채팅방 생성 실패: {str(e)}",
                "data": None,
            }

    @staticmethod
    def get_chat_rooms(user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """사용자의 채팅방 목록 조회"""
        try:
            # 사용자가 참여 중인 채팅방 쿼리
            queryset = (
                ChatRoom.objects.filter(
                    participants__user_id=user_id, participants__is_active=True
                )
                .select_related("product")
                .distinct()
            )

            # 총 개수 파악
            total_count = queryset.count()
            total_pages = math.ceil(total_count / page_size)

            # 페이지 범위 설정
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            # 간소화된 쿼리로 변경
            chat_rooms = queryset.order_by("-updated_at")[start_idx:end_idx]

            # 결과 변환
            result = []
            for room in chat_rooms:
                # 마지막 메시지 조회
                last_message = (
                    ChatMessage.objects.filter(chat_room=room, is_deleted=False)
                    .order_by("-created_at")
                    .first()
                )

                # 안 읽은 메시지 수 계산
                participant = ChatRoomParticipant.objects.filter(
                    chat_room=room, user_id=user_id
                ).first()

                last_read_time = None
                if participant and participant.last_read_message:
                    last_read_time = participant.last_read_message.created_at

                unread_count = 0
                if last_read_time:
                    unread_count = (
                        ChatMessage.objects.filter(
                            chat_room=room,
                            created_at__gt=last_read_time,
                            sender_id__isnull=False,
                            is_deleted=False,
                        )
                        .exclude(sender_id=user_id)
                        .count()
                    )
                else:
                    unread_count = (
                        ChatMessage.objects.filter(
                            chat_room=room, sender_id__isnull=False, is_deleted=False
                        )
                        .exclude(sender_id=user_id)
                        .count()
                    )

                # 이미지 URL 처리
                image_url = None
                product_image = (
                    ProductImage.objects.filter(product=room.product)
                    .select_related("file")
                    .first()
                )

                if product_image and product_image.file:
                    image_url = product_image.file.url

                result.append(
                    {
                        "id": room.id,
                        "product_id": room.product.id,
                        "product_title": room.product.title,
                        "product_image_url": image_url,
                        "last_message": last_message.message if last_message else None,
                        "last_message_time": (
                            last_message.created_at if last_message else None
                        ),
                        "unread_count": unread_count,
                    }
                )

            return {
                "success": True,
                "message": "채팅방 목록을 조회했습니다.",
                "data": result,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"채팅방 목록 조회 실패: {str(e)}",
                "data": [],
            }

    @staticmethod
    def get_chat_room_detail(chat_room_id: int, user_id: int) -> dict:
        """채팅방 상세 정보 조회"""
        try:
            # 채팅방 존재 및 권한 확인
            if not ChatRoomParticipant.objects.filter(
                chat_room_id=chat_room_id, user_id=user_id, is_active=True
            ).exists():
                return {
                    "success": False,
                    "message": "채팅방에 접근할 권한이 없습니다.",
                    "data": None,
                }

            # 채팅방 정보 조회
            chat_room = ChatRoom.objects.select_related("product", "product__user").get(
                id=chat_room_id
            )

            # 판매자 정보
            seller = chat_room.product.user

            # 구매자 정보 (판매자가 아닌 참여자)
            buyer = None
            buyer_participant = (
                ChatRoomParticipant.objects.filter(chat_room=chat_room)
                .exclude(user_id=seller.id)
                .select_related("user")
                .first()
            )

            if buyer_participant:
                buyer = buyer_participant.user

            # 상품 이미지 조회
            product_image_url = None
            product_image = (
                ProductImage.objects.filter(product=chat_room.product)
                .select_related("file")
                .first()
            )

            if product_image and product_image.file:
                product_image_url = product_image.file.url

            return {
                "success": True,
                "message": "채팅방 정보를 조회했습니다.",
                "data": {
                    "id": chat_room.id,
                    "product_id": chat_room.product.id,
                    "product_title": chat_room.product.title,
                    "product_image_url": product_image_url,
                    "seller_id": seller.id,
                    "seller_nickname": seller.nickname,
                    "buyer_id": buyer.id if buyer else None,
                    "buyer_nickname": buyer.nickname if buyer else None,
                    "created_at": chat_room.created_at,
                },
            }

        except ChatRoom.DoesNotExist:
            return {
                "success": False,
                "message": "존재하지 않는 채팅방입니다.",
                "data": None,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"채팅방 정보 조회 실패: {str(e)}",
                "data": None,
            }

    @staticmethod
    def get_chat_messages(
        chat_room_id: int, user_id: int, page: int = 1, page_size: int = 20
    ) -> dict:
        """채팅방 메시지 조회"""
        try:
            # 채팅방 존재 및 권한 확인
            participant = ChatRoomParticipant.objects.filter(
                chat_room_id=chat_room_id, user_id=user_id, is_active=True
            ).first()

            if not participant:
                return {
                    "success": False,
                    "message": "채팅방에 접근할 권한이 없습니다.",
                    "data": [],
                }

            # 메시지 쿼리
            messages = (
                ChatMessage.objects.filter(chat_room_id=chat_room_id, is_deleted=False)
                .select_related("sender")
                .order_by("-created_at")
            )

            # 총 개수 파악
            total_count = messages.count()
            total_pages = math.ceil(total_count / page_size)

            # 페이지네이션
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            messages = messages[start_idx:end_idx]

            # 참여자 정보 업데이트 (마지막 읽은 메시지)
            latest_message = (
                ChatMessage.objects.filter(chat_room_id=chat_room_id)
                .order_by("-created_at")
                .first()
            )

            if latest_message:
                participant.last_read_message = latest_message
                participant.save(update_fields=["last_read_message", "updated_at"])

            # 결과 변환
            result = []
            for msg in messages:
                file_url = None
                if msg.file:
                    file_url = msg.file.url

                result.append(
                    {
                        "id": msg.id,
                        "sender_id": msg.sender.id,
                        "sender_nickname": msg.sender.nickname,
                        "message": msg.message,
                        "created_at": msg.created_at,
                        "is_deleted": msg.is_deleted,
                        "file_url": file_url,
                    }
                )

            return {
                "success": True,
                "message": "메시지를 조회했습니다.",
                "data": result,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"메시지 조회 실패: {str(e)}",
                "data": [],
                "total_count": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
            }

    @staticmethod
    def send_message(
        chat_room_id: int, user_id: int, message: str, file_id: int = None
    ) -> dict:
        """메시지 전송 (REST API용, WebSocket은 별도로 처리)"""
        try:
            # 채팅방 존재 및 권한 확인
            if not ChatRoomParticipant.objects.filter(
                chat_room_id=chat_room_id, user_id=user_id, is_active=True
            ).exists():
                return {
                    "success": False,
                    "message": "채팅방에 접근할 권한이 없습니다.",
                    "data": None,
                }

            # 메시지 저장
            chat_message = ChatMessage.objects.create(
                chat_room_id=chat_room_id,
                sender_id=user_id,
                message=message,
                file_id=file_id,
            )

            # 채팅방 갱신 시간 업데이트 (최근 메시지 순 정렬 위함)
            chat_room = ChatRoom.objects.get(id=chat_room_id)
            chat_room.save(update_fields=["updated_at"])

            # 결과 반환
            file_url = None
            if chat_message.file:
                file_url = chat_message.file.url

            return {
                "success": True,
                "message": "메시지를 전송했습니다.",
                "data": {
                    "id": chat_message.id,
                    "sender_id": chat_message.sender.id,
                    "sender_nickname": chat_message.sender.nickname,
                    "message": chat_message.message,
                    "created_at": chat_message.created_at,
                    "is_deleted": chat_message.is_deleted,
                    "file_url": file_url,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"메시지 전송 실패: {str(e)}",
                "data": None,
            }

    @staticmethod
    def create_appointment(
        chat_room_id: int,
        user_id: int,
        appointment_date,
        location_lat: float,
        location_lng: float,
        location_desc: str,
    ) -> dict:
        """거래약속 생성 서비스"""
        try:
            # 채팅방 존재 및 권한 확인
            chat_room = ChatRoom.objects.select_related("product").get(id=chat_room_id)

            # 채팅방 참여자 확인
            if not ChatRoomParticipant.objects.filter(
                chat_room_id=chat_room_id, user_id=user_id, is_active=True
            ).exists():
                return {
                    "success": False,
                    "message": "채팅방에 접근할 권한이 없습니다.",
                    "data": None,
                }

            # 판매자와 구매자 구분
            product = chat_room.product
            seller_id = product.user_id

            # 판매자 정보 가져오기
            from a_user.models import User

            seller = User.objects.get(id=seller_id)

            # 구매자 찾기 (판매자가 아닌 사용자)
            buyer = None
            buyer_participant = (
                ChatRoomParticipant.objects.filter(chat_room=chat_room)
                .exclude(user_id=seller_id)
                .select_related("user")
                .first()
            )

            if buyer_participant:
                buyer = buyer_participant.user
                buyer_id = buyer.id
            else:
                return {
                    "success": False,
                    "message": "구매자 정보를 찾을 수 없습니다.",
                    "data": None,
                }

            # 약속 장소 생성
            appointment_location = Point(location_lng, location_lat, srid=4326)

            # 기존 약속이 있는지 확인하고 없으면 새로 생성
            appointment, created = TradeAppointment.objects.update_or_create(
                chat_room=chat_room,
                product=product,
                defaults={
                    "seller_id": seller_id,
                    "buyer_id": buyer_id,
                    "appointment_date": appointment_date,
                    "location": appointment_location,
                    "location_description": location_desc,
                    "status": TradeAppointment.Status.PENDING,
                },
            )

            # 상품 상태를 예약중으로 변경
            if created and product.status == Product.Status.NEW:
                product.status = Product.Status.RESERVED
                product.save(update_fields=["status", "updated_at"])

            # 약속 생성 메시지 전송
            appointment_time = appointment.appointment_date.strftime(
                "%Y년 %m월 %d일 %H시 %M분"
            )
            system_message = f"[시스템] 거래약속이 설정되었습니다. \n날짜: {appointment_time}\n장소: {location_desc}"

            # 시스템 메시지를 보낼 때 현재 사용자를 sender로 설정
            ChatMessage.objects.create(
                chat_room=chat_room,
                sender_id=user_id,
                message=system_message,
            )

            # 채팅방 갱신 시간 업데이트
            chat_room.save(update_fields=["updated_at"])

            return {
                "success": True,
                "message": "거래약속이 생성되었습니다.",
                "data": {
                    "id": appointment.id,
                    "product_id": product.id,
                    "product_title": product.title,
                    "seller_id": seller_id,
                    "seller_nickname": seller.nickname,
                    "buyer_id": buyer_id,
                    "buyer_nickname": buyer.nickname,
                    "appointment_date": appointment.appointment_date,
                    "location": {
                        "latitude": appointment.location.y,
                        "longitude": appointment.location.x,
                        "description": appointment.location_description,
                    },
                    "status": appointment.status,
                    "chat_room_id": chat_room.id,
                    "created_at": appointment.created_at,
                },
            }

        except ChatRoom.DoesNotExist:
            return {
                "success": False,
                "message": "존재하지 않는 채팅방입니다.",
                "data": None,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"거래약속 생성 실패: {str(e)}",
                "data": None,
            }

    @staticmethod
    def get_appointment(appointment_id: int, user_id: int) -> dict:
        """거래약속 상세 정보 조회"""
        try:
            # 약속 존재 확인
            appointment = TradeAppointment.objects.select_related(
                "product", "seller", "buyer", "chat_room"
            ).get(id=appointment_id)

            # 권한 체크 (판매자 또는 구매자만 조회 가능)
            if user_id not in [appointment.seller_id, appointment.buyer_id]:
                return {
                    "success": False,
                    "message": "해당 약속에 접근할 권한이 없습니다.",
                    "data": None,
                }

            return {
                "success": True,
                "message": "거래약속 정보를 조회했습니다.",
                "data": {
                    "id": appointment.id,
                    "product_id": appointment.product.id,
                    "product_title": appointment.product.title,
                    "seller_id": appointment.seller.id,
                    "seller_nickname": appointment.seller.nickname,
                    "buyer_id": appointment.buyer.id,
                    "buyer_nickname": appointment.buyer.nickname,
                    "appointment_date": appointment.appointment_date,
                    "location": {
                        "latitude": appointment.location.y,
                        "longitude": appointment.location.x,
                        "description": appointment.location_description,
                    },
                    "status": appointment.status,
                    "chat_room_id": appointment.chat_room.id,
                    "created_at": appointment.created_at,
                },
            }

        except TradeAppointment.DoesNotExist:
            return {
                "success": False,
                "message": "존재하지 않는 거래약속입니다.",
                "data": None,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"거래약속 조회 실패: {str(e)}",
                "data": None,
            }

    @staticmethod
    def get_appointments_for_chat(chat_room_id: int, user_id: int) -> dict:
        """채팅방의 거래약속 목록 조회"""
        try:
            # 채팅방 권한 체크
            if not ChatRoomParticipant.objects.filter(
                chat_room_id=chat_room_id, user_id=user_id, is_active=True
            ).exists():
                return {
                    "success": False,
                    "message": "채팅방에 접근할 권한이 없습니다.",
                    "data": [],
                }

            # 채팅방의 모든 약속 조회
            appointments = TradeAppointment.objects.filter(
                chat_room_id=chat_room_id
            ).order_by("-created_at")

            result = []
            for appointment in appointments:
                result.append(
                    {
                        "id": appointment.id,
                        "appointment_date": appointment.appointment_date,
                        "location_description": appointment.location_description,
                        "status": appointment.status,
                        "created_at": appointment.created_at,
                    }
                )

            return {
                "success": True,
                "message": "거래약속 목록을 조회했습니다.",
                "data": result,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"거래약속 목록 조회 실패: {str(e)}",
                "data": [],
            }

    @staticmethod
    def update_appointment_status(
        appointment_id: int, user_id: int, action: str
    ) -> dict:
        """거래약속 상태 변경 서비스"""
        try:
            # 약속 존재 확인
            appointment = TradeAppointment.objects.select_related(
                "product", "chat_room", "seller", "buyer"
            ).get(id=appointment_id)

            # 권한 체크 (판매자 또는 구매자만 상태 변경 가능)
            if user_id not in [appointment.seller_id, appointment.buyer_id]:
                return {
                    "success": False,
                    "message": "해당 약속의 상태를 변경할 권한이 없습니다.",
                    "data": None,
                }

            # 상태 변경 액션 처리
            if action == "confirm":
                if appointment.status != TradeAppointment.Status.PENDING:
                    return {
                        "success": False,
                        "message": "대기 상태인 약속만 확정할 수 있습니다.",
                        "data": None,
                    }
                appointment.status = TradeAppointment.Status.CONFIRMED
                message = "거래약속이 확정되었습니다."
                system_message = "[시스템] 거래약속이 확정되었습니다."
            elif action == "cancel":
                if appointment.status == TradeAppointment.Status.COMPLETED:
                    return {
                        "success": False,
                        "message": "이미 완료된 약속은 취소할 수 없습니다.",
                        "data": None,
                    }
                appointment.status = TradeAppointment.Status.CANCELED
                message = "거래약속이 취소되었습니다."
                system_message = "[시스템] 거래약속이 취소되었습니다."

                # 상품 상태를 다시 판매중으로 변경 (이미 판매완료가 아닌 경우)
                product = appointment.product
                if product.status == Product.Status.RESERVED:
                    product.status = Product.Status.NEW
                    product.save(update_fields=["status", "updated_at"])
            elif action == "complete":
                if appointment.status not in [
                    TradeAppointment.Status.PENDING,
                    TradeAppointment.Status.CONFIRMED,
                ]:
                    return {
                        "success": False,
                        "message": "대기 또는 확정 상태인 약속만 완료 처리할 수 있습니다.",
                        "data": None,
                    }
                appointment.status = TradeAppointment.Status.COMPLETED
                message = "거래약속이 완료 처리되었습니다."
                system_message = "[시스템] 거래약속이 완료되었습니다. 거래 후기와 매너 평가를 남겨보세요!"
            else:
                return {
                    "success": False,
                    "message": "유효하지 않은 액션입니다. (confirm/cancel/complete 중 하나)",
                    "data": None,
                }

            # 약속 상태 업데이트
            appointment.save(update_fields=["status", "updated_at"])

            # 시스템 메시지 추가 - 여기도 sender=None 대신 sender_id=user_id 사용
            ChatMessage.objects.create(
                chat_room=appointment.chat_room,
                sender_id=user_id,  # None 대신 현재 사용자 ID 사용
                message=system_message,
            )

            # 채팅방 갱신 시간 업데이트
            appointment.chat_room.save(update_fields=["updated_at"])

            return {
                "success": True,
                "message": message,
                "data": {
                    "id": appointment.id,
                    "product_id": appointment.product.id,
                    "product_title": appointment.product.title,
                    "seller_id": appointment.seller.id,
                    "seller_nickname": appointment.seller.nickname,
                    "buyer_id": appointment.buyer.id,
                    "buyer_nickname": appointment.buyer.nickname,
                    "appointment_date": appointment.appointment_date,
                    "location": {
                        "latitude": appointment.location.y,
                        "longitude": appointment.location.x,
                        "description": appointment.location_description,
                    },
                    "status": appointment.status,
                    "chat_room_id": appointment.chat_room.id,
                    "created_at": appointment.created_at,
                    "updated_at": appointment.updated_at,
                },
            }

        except TradeAppointment.DoesNotExist:
            return {
                "success": False,
                "message": "존재하지 않는 거래약속입니다.",
                "data": None,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"거래약속 상태 변경 실패: {str(e)}",
                "data": None,
            }
