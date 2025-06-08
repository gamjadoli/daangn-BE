import json
import tempfile
from datetime import timedelta
from io import BytesIO
from unittest.mock import MagicMock, patch

from a_apis.models.email_verification import EmailVerification
from a_user.models import User
from PIL import Image

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


class UserProfileUpdateTest(TestCase):
    """사용자 프로필 업데이트 테스트"""

    def setUp(self):
        """각 테스트 실행 전 초기화"""
        self.client = Client()

        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="testPassword123!",
            nickname="원래닉네임",
            phone_number="01012345678",
            is_email_verified=True,
        )

        # Mock Request 객체 준비 - 실제 토큰 대신 직접 사용자 객체를 넣음
        class MockRequest:
            def __init__(self, user):
                self.user = user  # auth 대신 user 속성 사용

        self.mock_request = MockRequest(self.user)

        # 이미지 파일 생성 함수
        self.create_test_image = lambda: self._create_image()

    def _create_image(self):
        """테스트용 이미지 파일 생성"""
        file = BytesIO()
        image = Image.new("RGB", size=(100, 100), color=(155, 0, 0))
        image.save(file, "jpeg")
        file.name = "test.jpg"
        file.seek(0)
        return file

    @patch("a_apis.service.files.FileService.upload_file")
    @patch("a_apis.service.files.FileService.delete_file")
    def test_update_nickname(self, mock_delete_file, mock_upload_file):
        """닉네임 변경 테스트"""
        from a_apis.schema.users import UpdateProfileSchema
        from a_apis.service.users import UserService

        # 스키마와 서비스 직접 호출
        data = UpdateProfileSchema(nickname="변경된닉네임")
        result = UserService.update_user_profile(self.mock_request, data)

        # 응답 검증
        self.assertTrue(result["success"])
        self.assertIn("nickname", result["message"])

        # DB에 변경 사항 반영 확인
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, "변경된닉네임")

    @patch("a_apis.service.files.FileService.upload_file")
    @patch("a_apis.service.files.FileService.delete_file")
    def test_update_profile_image(self, mock_delete_file, mock_upload_file):
        """프로필 이미지 업로드 테스트"""
        from a_apis.models.files import File
        from a_apis.schema.users import UpdateProfileSchema
        from a_apis.service.users import UserService

        # File 객체 생성
        test_file = File.objects.create(
            file="uploaded_test_path.jpg", size=1024, type="jpg"
        )

        # FileService.upload_file가 실제 File 객체를 반환하도록 설정
        mock_upload_file.return_value = test_file

        # 이미지 파일 생성
        test_image = self.create_test_image()

        # 스키마와 서비스 직접 호출
        data = UpdateProfileSchema(nickname="이미지테스트")
        result = UserService.update_user_profile(self.mock_request, data, test_image)

        # 디버깅 정보 출력
        print(f"\nUpdate Profile Image Test - Result: {result}")

        # 응답 검증
        self.assertTrue(
            result["success"],
            f"Failed with message: {result.get('message', 'No message')}",
        )
        self.assertIn("profile_img", result["message"])

        # 모킹 함수 호출 확인
        mock_upload_file.assert_called_once()
        self.assertEqual(mock_upload_file.call_args[1]["file_type"], "profile")

        # DB에 변경 사항 반영 확인
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile_img, test_file)

    @patch("a_apis.service.files.FileService.upload_file")
    @patch("a_apis.service.files.FileService.delete_file")
    def test_remove_profile_image(self, mock_delete_file, mock_upload_file):
        """프로필 이미지 삭제 테스트"""
        from a_apis.models.files import File
        from a_apis.schema.users import UpdateProfileSchema
        from a_apis.service.users import UserService

        # 먼저 사용자에게 프로필 이미지 설정
        test_file = File.objects.create(file="test_path.jpg", size=1024, type="jpg")
        self.user.profile_img = test_file  # profile_image -> profile_img
        self.user.save()

        # 스키마와 서비스 직접 호출
        data = UpdateProfileSchema(remove_profile_image=True)
        result = UserService.update_user_profile(self.mock_request, data)

        # 디버깅 정보 출력
        print(f"\nRemove Profile Image Test - Result: {result}")

        # 응답 검증
        self.assertTrue(
            result["success"],
            f"Failed with message: {result.get('message', 'No message')}",
        )
        self.assertIn("profile_img", result["message"])  # profile_image -> profile_img

        # 모킹 함수 호출 확인
        mock_delete_file.assert_called_once_with(test_file)

        # DB에 변경 사항 반영 확인
        self.user.refresh_from_db()
        self.assertIsNone(self.user.profile_img)  # profile_image -> profile_img

    @patch("a_apis.service.files.FileService.upload_file")
    @patch("a_apis.service.files.FileService.delete_file")
    def test_profile_image_priority(self, mock_delete_file, mock_upload_file):
        """프로필 이미지 삭제와 업로드 동시 요청 시 삭제 우선 처리 테스트"""
        from a_apis.models.files import File
        from a_apis.schema.users import UpdateProfileSchema
        from a_apis.service.users import UserService

        # 먼저 사용자에게 프로필 이미지 설정
        test_file = File.objects.create(file="test_path.jpg", size=1024, type="jpg")
        self.user.profile_img = test_file  # profile_image -> profile_img
        self.user.save()

        # 이미지 파일 생성
        test_image = self.create_test_image()

        # 스키마와 서비스 직접 호출
        data = UpdateProfileSchema(remove_profile_image=True)
        result = UserService.update_user_profile(self.mock_request, data, test_image)

        # 디버깅 정보 출력
        print(f"\nProfile Image Priority Test - Result: {result}")

        # 응답 검증
        self.assertTrue(
            result["success"],
            f"Failed with message: {result.get('message', 'No message')}",
        )
        self.assertIn("profile_img", result["message"])  # profile_image -> profile_img

        # 모킹 함수 호출 확인 - delete_file은 호출되어야 하고, upload_file은 호출되지 않아야 함
        mock_delete_file.assert_called_once_with(test_file)
        mock_upload_file.assert_not_called()

        # DB에 변경 사항 반영 확인 - 프로필 이미지가 None이어야 함
        self.user.refresh_from_db()
        self.assertIsNone(self.user.profile_img)  # profile_image -> profile_img


class UserLoginAndMeAPITest(TestCase):
    """로그인 및 내 정보 조회 API에서 유저 ID 반환 테스트"""

    def setUp(self):
        """테스트 셋업: 사용자 생성"""
        self.client = Client()

        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="testPassword123!",
            nickname="테스터",
            phone_number="01012345678",
            is_email_verified=True,
        )

    def test_login_api_returns_user_id(self):
        """로그인 API에서 사용자 ID가 반환되는지 테스트"""
        from a_apis.schema.users import LoginSchema
        from a_apis.service.users import UserService

        from django.test import RequestFactory

        # 로그인 데이터 준비
        login_data = LoginSchema(email="test@example.com", password="testPassword123!")

        # Django RequestFactory를 사용해서 실제 request 객체 생성
        factory = RequestFactory()
        request = factory.post("/api/users/login")

        # 세션 미들웨어 설정
        from django.contrib.sessions.middleware import SessionMiddleware

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        # UserService.login_user 직접 호출
        result = UserService.login_user(request, login_data)

        # 응답 검증
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "로그인 되었습니다.")

        # 사용자 정보에 ID가 포함되어 있는지 확인
        self.assertIn("user", result)
        user_data = result["user"]
        self.assertIn("id", user_data)
        self.assertEqual(user_data["id"], self.user.id)
        self.assertEqual(user_data["email"], self.user.email)
        self.assertEqual(user_data["nickname"], self.user.nickname)

        # 토큰 정보도 확인
        self.assertIn("tokens", result)
        self.assertIn("access", result["tokens"])
        self.assertIn("refresh", result["tokens"])

        print(f"로그인 API 응답에서 사용자 ID: {user_data['id']}")

    def test_get_user_api_returns_user_id(self):
        """내 정보 조회 API에서 사용자 ID가 반환되는지 테스트"""
        from a_apis.service.users import UserService
        from rest_framework_simplejwt.tokens import RefreshToken

        # JWT 토큰 생성
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)

        # Mock Request 객체 생성 (토큰 포함)
        class MockRequest:
            def __init__(self, token):
                self.auth = token

        mock_request = MockRequest(access_token)

        # UserService.get_user 직접 호출
        result = UserService.get_user(mock_request)

        # 응답 검증
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "인증된 사용자입니다.")

        # 사용자 정보에 ID가 포함되어 있는지 확인
        self.assertIn("user", result)
        user_data = result["user"]
        self.assertIn("id", user_data)
        self.assertEqual(user_data["id"], self.user.id)
        self.assertEqual(user_data["email"], self.user.email)
        self.assertEqual(user_data["nickname"], self.user.nickname)

        # 기타 필수 필드들도 확인
        self.assertIn("phone_number", user_data)
        self.assertIn("is_activated", user_data)
        self.assertIn("is_email_verified", user_data)
        self.assertIn("rating_score", user_data)
        self.assertIn("profile_img_url", user_data)
        self.assertIn("regions", user_data)
        self.assertIn("current_region", user_data)

        print(f"내 정보 조회 API 응답에서 사용자 ID: {user_data['id']}")

    def test_user_data_structure_consistency(self):
        """로그인과 내 정보 조회 API의 사용자 데이터 구조 일관성 테스트"""
        from a_apis.schema.users import LoginSchema
        from a_apis.service.users import UserService
        from rest_framework_simplejwt.tokens import RefreshToken

        from django.test import RequestFactory

        # 1. 로그인 API 호출
        login_data = LoginSchema(email="test@example.com", password="testPassword123!")

        # Django RequestFactory를 사용해서 실제 request 객체 생성
        factory = RequestFactory()
        request = factory.post("/api/users/login")

        # 세션 미들웨어 설정
        from django.contrib.sessions.middleware import SessionMiddleware

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        login_result = UserService.login_user(request, login_data)

        # 2. 내 정보 조회 API 호출
        access_token = login_result["tokens"]["access"]

        class MockRequestWithAuth:
            def __init__(self, token):
                self.auth = token

        mock_request_with_auth = MockRequestWithAuth(access_token)
        user_result = UserService.get_user(mock_request_with_auth)

        # 3. 두 API의 사용자 데이터 구조가 동일한지 확인
        login_user_data = login_result["user"]
        get_user_data = user_result["user"]

        # 필수 필드들이 모두 동일한지 확인
        required_fields = [
            "id",
            "email",
            "nickname",
            "phone_number",
            "is_activated",
            "is_email_verified",
            "rating_score",
            "profile_img_url",
            "regions",
            "current_region",
        ]

        for field in required_fields:
            self.assertIn(
                field, login_user_data, f"로그인 응답에 {field} 필드가 없습니다"
            )
            self.assertIn(
                field, get_user_data, f"내 정보 조회 응답에 {field} 필드가 없습니다"
            )

            # 값도 동일한지 확인 (객체 타입은 제외)
            if field not in ["regions", "current_region"]:
                self.assertEqual(
                    login_user_data[field],
                    get_user_data[field],
                    f"{field} 필드 값이 두 API에서 다릅니다",
                )

        print(
            "로그인과 내 정보 조회 API의 사용자 데이터 구조가 일관성 있게 구성되었습니다."
        )
        print(f"공통 사용자 ID: {login_user_data['id']}")
