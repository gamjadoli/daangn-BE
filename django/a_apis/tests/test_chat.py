import datetime
import json

from a_apis.models import ChatMessage, ChatRoom, ChatRoomParticipant, Product
from a_apis.models.trade import TradeAppointment
from a_user.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse


class ChatAPITestCase(TestCase):
    """채팅 API 테스트 클래스"""

    def setUp(self):
        """테스트 데이터 설정"""
        # 테스트 사용자 생성 (판매자)
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="testpassword123",
            nickname="판매자",
            phone_number="01012345678",
            is_email_verified=True,
        )

        # 테스트 사용자 생성 (구매자)
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="testpassword123",
            nickname="구매자",
            phone_number="01087654321",
            is_email_verified=True,
        )

        # 테스트 상품 생성
        self.product = Product.objects.create(
            user=self.seller,
            title="테스트 상품",
            trade_type="sale",
            price=10000,
            description="테스트 상품 설명",
            meeting_location=Point(126.9780, 37.5665, srid=4326),
            location_description="서울시청 앞",
            status="selling",
        )

        # API 클라이언트 설정
        self.client = APIClient()

        # JWT 토큰 생성
        self.seller_token = self.get_tokens_for_user(self.seller)
        self.buyer_token = self.get_tokens_for_user(self.buyer)

    def get_tokens_for_user(self, user):
        """사용자를 위한 JWT 토큰 생성"""
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    def test_create_chat_room(self):
        """채팅방 생성 테스트"""
        # 구매자 토큰으로 인증 설정
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.buyer_token['access']}"
        )

        # 채팅방 생성 API 호출 - product_id를 URL 쿼리 파라미터로 전달
        response = self.client.post(f"/api/chats?product_id={self.product.id}")

        # 응답 검증
        self.assertEqual(response.status_code, 200)

        # JSON 응답 파싱
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("data", response_data)
        self.assertIn("id", response_data["data"])

        # 채팅방이 DB에 생성되었는지 확인
        chat_room_id = response_data["data"]["id"]
        self.assertTrue(ChatRoom.objects.filter(id=chat_room_id).exists())

        # 판매자와 구매자가 모두 채팅방 참여자로 등록되었는지 확인
        chat_room = ChatRoom.objects.get(id=chat_room_id)
        self.assertEqual(chat_room.participants.count(), 2)
        self.assertTrue(
            ChatRoomParticipant.objects.filter(
                chat_room=chat_room, user=self.seller
            ).exists()
        )
        self.assertTrue(
            ChatRoomParticipant.objects.filter(
                chat_room=chat_room, user=self.buyer
            ).exists()
        )

        return chat_room  # 다른 테스트에서 사용할 수 있도록 반환

    def test_get_chat_rooms(self):
        """채팅방 목록 조회 테스트"""
        # 먼저 채팅방 생성
        chat_room = self.test_create_chat_room()

        # 구매자 토큰으로 인증 설정
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.buyer_token['access']}"
        )

        # 채팅방 목록 조회 API 호출
        response = self.client.get("/api/chats/")

        # 응답 검증
        self.assertEqual(response.status_code, 200)

        # JSON 응답 파싱
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("data", response_data)

        # 채팅방 목록에 생성한 채팅방이 포함되어 있는지 확인
        chat_rooms = response_data["data"]
        self.assertGreater(len(chat_rooms), 0)

        # 첫 번째 채팅방 정보 검증
        found = False
        for room in chat_rooms:
            if room["id"] == chat_room.id:
                found = True
                self.assertEqual(room["product_id"], self.product.id)
                self.assertEqual(room["product_title"], self.product.title)
                break

        self.assertTrue(found, "생성한 채팅방이 목록에 없습니다.")

    def test_get_chat_room_detail(self):
        """채팅방 상세 정보 조회 테스트"""
        # 먼저 채팅방 생성
        chat_room = self.test_create_chat_room()

        # 구매자 토큰으로 인증 설정
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.buyer_token['access']}"
        )

        # 채팅방 상세 정보 조회 API 호출
        response = self.client.get(f"/api/chats/{chat_room.id}")

        # 응답 검증
        self.assertEqual(response.status_code, 200)

        # JSON 응답 파싱
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("data", response_data)

        # 채팅방 상세 정보 검증 - 새로운 nested 구조
        data = response_data["data"]
        self.assertEqual(data["id"], chat_room.id)

        # 상품 정보 검증
        self.assertIn("product", data)
        product_data = data["product"]
        self.assertEqual(product_data["id"], self.product.id)
        self.assertEqual(product_data["title"], self.product.title)
        self.assertEqual(product_data["price"], self.product.price)
        self.assertEqual(product_data["status"], self.product.status)
        self.assertEqual(product_data["price_offer"], self.product.accept_price_offer)

        # 판매자 정보 검증
        self.assertIn("seller", data)
        seller_data = data["seller"]
        self.assertEqual(seller_data["id"], self.seller.id)
        self.assertEqual(seller_data["nickname"], self.seller.nickname)

        # 구매자 정보 검증
        self.assertIn("buyer", data)
        buyer_data = data["buyer"]
        self.assertEqual(buyer_data["id"], self.buyer.id)
        self.assertEqual(buyer_data["nickname"], self.buyer.nickname)

    def test_send_and_receive_message(self):
        """메시지 전송 및 조회 테스트"""
        # 먼저 채팅방 생성
        chat_room = self.test_create_chat_room()

        # 구매자 토큰으로 인증 설정
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.buyer_token['access']}"
        )

        # 메시지 전송 API 호출
        test_message = "안녕하세요, 상품에 관심이 있습니다."
        response = self.client.post(
            f"/api/chats/{chat_room.id}/messages",
            {"message": test_message},
            format="json",
        )

        # 응답 검증
        self.assertEqual(response.status_code, 200)

        # JSON 응답 파싱
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("data", response_data)

        # 전송된 메시지 정보 검증
        message_data = response_data["data"]
        self.assertEqual(message_data["message"], test_message)
        self.assertEqual(message_data["sender_id"], self.buyer.id)
        self.assertEqual(message_data["sender_nickname"], self.buyer.nickname)

        # 메시지가 DB에 저장되었는지 확인
        message_id = message_data["id"]
        self.assertTrue(ChatMessage.objects.filter(id=message_id).exists())

        # 메시지 조회 API 호출
        response = self.client.get(f"/api/chats/{chat_room.id}/messages")

        # 응답 검증
        self.assertEqual(response.status_code, 200)

        # JSON 응답 파싱
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("data", response_data)

        # 메시지 목록 검증
        messages = response_data["data"]
        self.assertGreater(len(messages), 0)

        # 전송한 메시지가 목록에 있는지 확인
        found = False
        for msg in messages:
            if msg["id"] == message_id:
                found = True
                self.assertEqual(msg["message"], test_message)
                self.assertEqual(msg["sender_id"], self.buyer.id)
                self.assertEqual(msg["sender_nickname"], self.buyer.nickname)
                break

        self.assertTrue(found, "전송한 메시지가 목록에 없습니다.")

    def test_seller_cannot_create_chat_room_for_own_product(self):
        """판매자는 자신의 상품에 대한 채팅방을 생성할 수 없음을 테스트"""
        # 판매자 토큰으로 인증 설정
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.seller_token['access']}"
        )

        # 채팅방 생성 API 호출 - product_id를 URL 쿼리 파라미터로 전달
        response = self.client.post(f"/api/chats?product_id={self.product.id}")

        # 응답 검증 - 실패해야 함
        self.assertEqual(
            response.status_code, 200
        )  # API는 200을 반환하지만 success는 False

        # JSON 응답 파싱
        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertIn("message", response_data)
        self.assertIn(
            "자신의 상품에 대해 채팅을 시작할 수 없습니다", response_data["message"]
        )

    def test_create_appointment(self):
        """거래약속 생성 테스트"""
        # 먼저 채팅방 생성
        chat_room = self.test_create_chat_room()

        # 판매자 토큰으로 인증 설정 (판매자도 약속 생성 가능)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.seller_token['access']}"
        )

        # 약속 날짜 설정 (현재 시간 + 1일)
        appointment_date = datetime.datetime.now() + datetime.timedelta(days=1)

        # 거래약속 생성 API 호출
        appointment_data = {
            "appointment_date": appointment_date.isoformat(),
            "location": {
                "latitude": 37.5665,
                "longitude": 126.9780,
                "description": "서울시청 앞 카페",
            },
            # chat_room_id는 URL 경로에 이미 있으므로 여기서 제거
        }

        response = self.client.post(
            f"/api/chats/{chat_room.id}/appointments",
            appointment_data,
            format="json",
        )

        # 응답 검증
        self.assertEqual(response.status_code, 200)

        # JSON 응답 파싱
        response_data = json.loads(response.content)

        # 오류가 있는 경우 상세 정보 출력
        if not response_data["success"]:
            print(f"API 오류: {response_data['message']}")

        self.assertTrue(response_data["success"])
        self.assertIn("data", response_data)

        # 약속 정보 검증
        appointment_data = response_data["data"]
        self.assertIsNotNone(appointment_data["id"])
        self.assertEqual(appointment_data["product_id"], self.product.id)
        self.assertEqual(appointment_data["seller_id"], self.seller.id)
        self.assertEqual(appointment_data["buyer_id"], self.buyer.id)
        self.assertEqual(appointment_data["status"], TradeAppointment.Status.PENDING)
        self.assertEqual(
            appointment_data["location"]["description"], "서울시청 앞 카페"
        )

        # 약속이 DB에 저장되었는지 확인
        appointment_id = appointment_data["id"]
        self.assertTrue(TradeAppointment.objects.filter(id=appointment_id).exists())

        # 상품 상태가 '예약중'으로 변경되었는지 확인
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.Status.RESERVED)

        # 채팅방에 시스템 메시지가 생성되었는지 확인
        # 이제 sender=None이 아니라 메시지 내용으로 시스템 메시지를 찾아야 함
        system_message = (
            ChatMessage.objects.filter(
                chat_room=chat_room,
                message__contains="[시스템] 거래약속이 설정되었습니다",  # 시스템 메시지 내용으로 검색
            )
            .order_by("-created_at")
            .first()
        )

        self.assertIsNotNone(system_message)
        self.assertIn("거래약속이 설정되었습니다", system_message.message)

        return appointment_id

    def test_get_appointment(self):
        """거래약속 조회 테스트"""
        # 먼저 약속 생성
        appointment_id = self.test_create_appointment()

        # 구매자 토큰으로 인증 설정
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.buyer_token['access']}"
        )

        # 약속 조회 API 호출
        response = self.client.get(f"/api/chats/appointments/{appointment_id}")

        # 응답 검증
        self.assertEqual(response.status_code, 200)

        # JSON 응답 파싱
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("data", response_data)

        # 약속 정보 검증
        appointment = response_data["data"]
        self.assertEqual(appointment["id"], appointment_id)
        self.assertEqual(appointment["product_id"], self.product.id)
        self.assertEqual(appointment["product_title"], self.product.title)
        self.assertEqual(appointment["seller_id"], self.seller.id)
        self.assertEqual(appointment["seller_nickname"], self.seller.nickname)
        self.assertEqual(appointment["buyer_id"], self.buyer.id)
        self.assertEqual(appointment["buyer_nickname"], self.buyer.nickname)
        self.assertIn("location", appointment)
        self.assertIn("latitude", appointment["location"])
        self.assertIn("longitude", appointment["location"])
        self.assertIn("description", appointment["location"])

    def test_get_appointments_for_chat(self):
        """채팅방 거래약속 목록 조회 테스트"""
        # 먼저 약속 생성
        self.test_create_appointment()

        # 채팅방 ID 구하기
        chat_room = ChatRoom.objects.filter(product=self.product).first()
        self.assertIsNotNone(chat_room)

        # 구매자 토큰으로 인증 설정
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.buyer_token['access']}"
        )

        # 채팅방 약속 목록 조회 API 호출
        response = self.client.get(f"/api/chats/{chat_room.id}/appointments")

        # 응답 검증
        self.assertEqual(response.status_code, 200)

        # JSON 응답 파싱
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("data", response_data)

        # 약속 목록 검증
        appointments = response_data["data"]
        self.assertGreater(len(appointments), 0)
        self.assertIn("appointment_date", appointments[0])
        self.assertIn("location_description", appointments[0])
        self.assertIn("status", appointments[0])

    def test_update_appointment_status(self):
        """거래약속 상태 변경 테스트"""
        # 먼저 약속 생성
        appointment_id = self.test_create_appointment()

        # 판매자 토큰으로 인증 설정
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.seller_token['access']}"
        )

        # 약속 확정 API 호출
        response = self.client.post(
            f"/api/chats/appointments/{appointment_id}/status",
            {"action": "confirm"},
            format="json",
        )

        # 응답 검증
        self.assertEqual(response.status_code, 200)

        # JSON 응답 파싱
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["data"]["status"], TradeAppointment.Status.CONFIRMED
        )

        # DB에 상태가 변경되었는지 확인
        appointment = TradeAppointment.objects.get(id=appointment_id)
        self.assertEqual(appointment.status, TradeAppointment.Status.CONFIRMED)

        # 채팅방에 시스템 메시지가 생성되었는지 확인
        chat_room = appointment.chat_room
        system_message = ChatMessage.objects.filter(
            chat_room=chat_room,
            message__contains="[시스템] 거래약속이 확정되었습니다",  # 메시지 내용으로 검색
        ).exists()
        self.assertTrue(system_message)

        # 구매자 토큰으로 인증 설정 (취소 테스트)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.buyer_token['access']}"
        )

        # 약속 취소 API 호출
        response = self.client.post(
            f"/api/chats/appointments/{appointment_id}/status",
            {"action": "cancel"},
            format="json",
        )

        # 응답 검증
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)["success"])

        # DB에 상태가 취소로 변경되었는지 확인
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, TradeAppointment.Status.CANCELED)

        # 상품 상태가 다시 '판매중'으로 변경되었는지 확인
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.Status.SELLING)

        # 채팅방에 시스템 메시지가 생성되었는지 확인
        system_message = ChatMessage.objects.filter(
            chat_room=chat_room,
            message__contains="[시스템] 거래약속이 취소되었습니다",  # 메시지 내용으로 검색
        ).exists()
        self.assertTrue(system_message)

    def test_complete_appointment(self):
        """거래약속 완료 처리 테스트"""
        # 먼저 약속 생성 및 확정
        appointment_id = self.test_create_appointment()

        # 약속 객체 가져오기
        appointment = TradeAppointment.objects.get(id=appointment_id)
        appointment.status = TradeAppointment.Status.CONFIRMED
        appointment.save()

        # 판매자 토큰으로 인증 설정
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.seller_token['access']}"
        )

        # 약속 완료 API 호출
        response = self.client.post(
            f"/api/chats/appointments/{appointment_id}/status",
            {"action": "complete"},
            format="json",
        )

        # 응답 검증
        self.assertEqual(response.status_code, 200)

        # JSON 응답 파싱
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["data"]["status"], TradeAppointment.Status.COMPLETED
        )

        # DB에 상태가 변경되었는지 확인
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, TradeAppointment.Status.COMPLETED)

        # 채팅방에 시스템 메시지가 생성되었는지 확인
        chat_room = appointment.chat_room
        system_message = ChatMessage.objects.filter(
            chat_room=chat_room,
            message__contains="[시스템] 거래약속이 완료되었습니다",  # 메시지 내용으로 검색
        ).exists()
        self.assertTrue(system_message)

    def test_unauthorized_appointment_access(self):
        """권한 없는 사용자의 약속 접근 테스트"""
        # 먼저 약속 생성
        appointment_id = self.test_create_appointment()

        # 제3자 사용자 생성
        third_user = User.objects.create_user(
            email="third@example.com",
            password="testpassword123",
            nickname="제3자",
            phone_number="01099998888",
            is_email_verified=True,
        )
        third_token = self.get_tokens_for_user(third_user)

        # 제3자 토큰으로 인증 설정
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {third_token['access']}")

        # 약속 조회 API 호출 - 권한 없음
        response = self.client.get(f"/api/chats/appointments/{appointment_id}")

        # 응답 검증 - 권한 없음 확인
        self.assertEqual(
            response.status_code, 200
        )  # API는 200을 반환하지만 success는 False

        # JSON 응답 파싱
        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertIn("접근할 권한이 없습니다", response_data["message"])
