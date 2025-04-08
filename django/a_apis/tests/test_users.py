import json
from datetime import timedelta
from unittest.mock import patch

from a_apis.models.email_verification import EmailVerification
from a_user.models import User

from django.core import mail
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.utils import timezone


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class UserLoginTest(TestCase):
    def setUp(self):
        """각 테스트 실행 전 실행되는 초기화 메서드"""
        self.client = Client()

        # 테스트용 사용자 정보 (위치 정보 추가)
        self.test_user_data = {
            "email": "ljhx6787@naver.com",
            "password": "testPassword123!",
            "nickname": "테스트닉네임",
            "phone_number": "01012345678",
            "latitude": 37.5665,  # 서울시청 위치 (예시)
            "longitude": 126.9780,
        }

        self.verification_code = None  # 이메일 인증 과정에서 설정됨

    def test_request_email_verification_success(self):
        """이메일 인증 요청 테스트"""
        # 테스트 시작 전 메일함 비우기
        mail.outbox = []

        response = self.client.post(
            "/api/users/request-email-verification",
            data=json.dumps({"email": self.test_user_data["email"]}),
            content_type="application/json",
        )

        # 이메일 발송 여부 및 내용 확인
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(mail.outbox) > 0, "이메일이 발송되지 않았습니다")

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
            data=json.dumps(
                {"email": self.test_user_data["email"], "code": self.verification_code}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "이메일 인증이 완료되었습니다.")

    @patch("a_apis.service.region.SGISService.get_region_info")
    def test_signup_success(self, mock_get_region_info):
        """정상적인 회원가입 테스트 (위치 정보 포함)"""
        # SGISService.get_region_info 메서드 모킹
        region_info = {
            "sido_cd": "11",
            "sido_nm": "서울특별시",
            "sgg_cd": "11000",
            "sgg_nm": "중구",
            "adm_cd": "1100000",
            "adm_nm": "명동",
        }
        mock_get_region_info.return_value = region_info

        # 테스트 전에 실제 지역 데이터 생성 (중요)
        from a_apis.models.region import EupmyeondongRegion, SidoRegion, SigunguRegion

        from django.contrib.gis.geos import Point

        # 테스트 데이터베이스에 지역 정보 생성
        sido, _ = SidoRegion.objects.get_or_create(
            code=region_info["sido_cd"], defaults={"name": region_info["sido_nm"]}
        )

        sigungu, _ = SigunguRegion.objects.get_or_create(
            code=region_info["sgg_cd"],
            sido=sido,
            defaults={"name": region_info["sgg_nm"]},
        )

        test_point = Point(
            self.test_user_data["longitude"], self.test_user_data["latitude"], srid=4326
        )
        EupmyeondongRegion.objects.get_or_create(
            code=region_info["adm_cd"],
            sigungu=sigungu,
            defaults={"name": region_info["adm_nm"], "center_coordinates": test_point},
        )

        # 이메일 인증 완료
        self.test_verify_email_success()

        # 회원가입 요청 (위치 정보 포함)
        response = self.client.post(
            "/api/users/signup",
            data=json.dumps(self.test_user_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)

        # 응답 검증
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "회원가입이 완료되었습니다.")
        self.assertIn("tokens", response_data)
        self.assertIn("data", response_data)  # user -> data로 변경됨
        self.assertEqual(response_data["data"]["email"], self.test_user_data["email"])
        self.assertEqual(
            response_data["data"]["nickname"], self.test_user_data["nickname"]
        )

        # 사용자 생성 확인
        self.assertTrue(
            User.objects.filter(email=self.test_user_data["email"]).exists()
        )
        user = User.objects.get(email=self.test_user_data["email"])

        # 활동지역 생성 확인
        self.assertTrue(hasattr(user, "activity_regions"))
        self.assertTrue(user.activity_regions.exists())

        # 첫 번째 활동지역 확인
        activity_region = user.activity_regions.first()
        self.assertEqual(activity_region.priority, 1)  # 첫 번째 지역
        self.assertEqual(
            activity_region.activity_area.name, "명동"
        )  # 모킹된 지역명과 일치

    @patch("a_apis.service.region.SGISService.get_region_info")
    def test_signup_with_location_failure(self, mock_get_region_info):
        """위치 정보 처리 실패 시에도 회원가입은 성공해야 함"""
        # 위치 정보 처리 중 예외 발생 시뮬레이션
        mock_get_region_info.side_effect = Exception("위치 정보 조회 실패")

        # 이메일 인증 완료
        self.test_verify_email_success()

        # 회원가입 요청
        response = self.client.post(
            "/api/users/signup",
            data=json.dumps(self.test_user_data),
            content_type="application/json",
        )

        # 응답 검증 - 위치 정보 처리에 실패해도 회원가입은 성공해야 함
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "회원가입이 완료되었습니다.")

        # 사용자 생성 확인
        self.assertTrue(
            User.objects.filter(email=self.test_user_data["email"]).exists()
        )
