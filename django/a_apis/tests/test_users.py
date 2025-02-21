import json
from datetime import timedelta

from a_apis.models.email_verification import EmailVerification
from a_user.models import User

from django.core import mail
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.utils import timezone


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class UserLoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.email = "test@example.com"
        self.password = "testpass123"
        self.username = "testuser"
        self.verification_code = "123456"

    def test_request_email_verification_success(self):
        """이메일 인증 요청 테스트"""
        # 테스트 시작 전 메일함 비우기
        mail.outbox = []

        response = self.client.post(
            "/api/users/request-email-verification",
            data=json.dumps({"email": self.email}),
            content_type="application/json",
        )

        # 이메일 발송 여부 및 내용 확인
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            len(mail.outbox) > 0, "이메일이 발송되지 않았습니다"
        )  # 수정된 부분

        if len(mail.outbox) > 0:
            sent_mail = mail.outbox[0]
            self.verification_code = sent_mail.body.split("인증번호: ")[1].split("\n")[
                0
            ]

    def test_verify_email_success(self):
        """이메일 인증 테스트"""
        # 먼저 이메일 인증 요청을 보내서 인증번호를 받아옴
        self.test_request_email_verification_success()

        # 받아온 인증번호로 이메일 인증 시도
        response = self.client.post(
            "/api/users/verify-email",
            data=json.dumps({"email": self.email, "code": self.verification_code}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "이메일 인증이 완료되었습니다.")

    def test_signup_success(self):
        """정상적인 회원가입 테스트"""

        self.test_verify_email_success()

        # 회원가입 요청
        signup_data = {
            "username": "newuser",
            "password": "newpass123",
            "phone_number": "01012345678",
            "email": "test@example.com",
        }

        response = self.client.post(
            "/api/users/signup",
            data=json.dumps(signup_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)

        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "회원가입이 완료되었습니다.")
        self.assertIn("tokens", response_data)
        self.assertIn("user", response_data)
        self.assertEqual(response_data["user"]["email"], signup_data["email"])
        self.assertEqual(response_data["user"]["username"], signup_data["username"])
