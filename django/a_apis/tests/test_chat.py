import json

from a_apis.models import ChatMessage, ChatRoom, ChatRoomParticipant, Product
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
            status="new",
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
        response = self.client.post(f"/api/chats/create?product_id={self.product.id}")

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

        # 채팅방 상세 정보 검증
        data = response_data["data"]
        self.assertEqual(data["id"], chat_room.id)
        self.assertEqual(data["product_id"], self.product.id)
        self.assertEqual(data["product_title"], self.product.title)
        self.assertEqual(data["seller_id"], self.seller.id)
        self.assertEqual(data["seller_nickname"], self.seller.nickname)
        self.assertEqual(data["buyer_id"], self.buyer.id)
        self.assertEqual(data["buyer_nickname"], self.buyer.nickname)

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
        response = self.client.post(f"/api/chats/create?product_id={self.product.id}")

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
