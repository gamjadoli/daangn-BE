import json
import unittest
from unittest import mock

from a_apis.service.region import RegionService, SGISAPIException, SGISService
from a_user.models import User  # 사용자 모델 임포트 추가

from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings


class SGISServiceMockTestCase(TestCase):
    """SGIS API 서비스 테스트 (모킹 사용)"""

    def setUp(self):
        self.sgis_service = SGISService()
        self.test_coordinates = [
            {"name": "서울시청", "latitude": 37.5665, "longitude": 126.9780},
            {"name": "강남역", "latitude": 37.4980, "longitude": 127.0276},
            {"name": "명동", "latitude": 37.5638, "longitude": 126.9857},
        ]

        # 예상되는 API 응답 데이터 정의
        self.mock_seoul_city_hall_response = {
            "sido_cd": "11",
            "sido_nm": "서울특별시",
            "sgg_cd": "11000",
            "sgg_nm": "중구",
            "adm_cd": "1100000",
            "adm_nm": "명동",
        }

        self.mock_gangnam_response = {
            "sido_cd": "11",
            "sido_nm": "서울특별시",
            "sgg_cd": "11230",
            "sgg_nm": "강남구",
            "adm_cd": "1123000",
            "adm_nm": "역삼동",
        }

    def test_access_token(self):
        """SGIS API 액세스 토큰 발급 테스트"""
        # 실제 액세스 토큰 발급 테스트는 유지
        try:
            token = self.sgis_service.access_token
            self.assertIsNotNone(token)
            self.assertTrue(len(token) > 10)  # 토큰은 일정 길이 이상이어야 함
            print(f"SGIS API 액세스 토큰 발급 성공: {token[:20]}...")
        except SGISAPIException as e:
            self.fail(f"액세스 토큰 발급 실패: {str(e)}")

    @mock.patch("a_apis.service.region.SGISService.get_region_info")
    def test_region_info_seoul_city_hall_mock(self, mock_get_region_info):
        """서울시청 좌표로 지역 정보 조회 테스트 (모킹 사용)"""
        # 모의 응답 설정
        mock_get_region_info.return_value = self.mock_seoul_city_hall_response

        coords = self.test_coordinates[0]
        result = self.sgis_service.get_region_info(
            coords["latitude"], coords["longitude"]
        )

        # 결과 검증
        self.assertIsNotNone(result)
        self.assertEqual(result["sido_nm"], "서울특별시")
        self.assertEqual(result["sgg_nm"], "중구")
        self.assertEqual(result["adm_nm"], "명동")

        # mock 함수가 호출되었는지 확인
        mock_get_region_info.assert_called_once_with(
            coords["latitude"], coords["longitude"]
        )

        print(f"{coords['name']} 지역 정보 조회 성공: {result}")

    @mock.patch("a_apis.service.region.SGISService.get_region_info")
    def test_region_info_multiple_locations_mock(self, mock_get_region_info):
        """여러 위치에서 지역 정보 조회 테스트 (모킹 사용)"""
        # 서울시청 요청 시 응답
        mock_get_region_info.side_effect = lambda lat, lon: (
            self.mock_seoul_city_hall_response
            if lat == 37.5665 and lon == 126.9780
            else self.mock_gangnam_response
        )

        for coords in self.test_coordinates:
            result = self.sgis_service.get_region_info(
                coords["latitude"], coords["longitude"]
            )

            # 결과 검증
            self.assertIsNotNone(result)
            self.assertIn("sido_nm", result)
            self.assertIn("sgg_nm", result)
            self.assertIn("adm_nm", result)
            self.assertEqual(result["sido_nm"], "서울특별시")  # 모두 서울특별시

            # 서울시청과 나머지 지역 구분
            if coords["name"] == "서울시청":
                self.assertEqual(result["sgg_nm"], "중구")
                self.assertEqual(result["adm_nm"], "명동")
            else:
                self.assertEqual(result["sgg_nm"], "강남구")
                self.assertEqual(result["adm_nm"], "역삼동")

            print(f"{coords['name']} 지역 정보 조회 성공: {result}")

    def test_validate_coordinates(self):
        """좌표 유효성 검증 테스트"""
        # 유효한 좌표
        self.assertTrue(RegionService.validate_coordinates(37.5665, 126.9780))
        self.assertTrue(RegionService.validate_coordinates(-89.9, 179.9))
        self.assertTrue(RegionService.validate_coordinates(0, 0))

        # 유효하지 않은 좌표
        self.assertFalse(RegionService.validate_coordinates(91, 0))
        self.assertFalse(RegionService.validate_coordinates(0, 181))
        self.assertFalse(RegionService.validate_coordinates(-91, 0))
        self.assertFalse(RegionService.validate_coordinates(0, -181))

        # 타입 에러 발생 케이스
        self.assertFalse(RegionService.validate_coordinates("invalid", 0))
        self.assertFalse(RegionService.validate_coordinates(None, None))


@mock.patch("a_apis.service.region.SGISService.get_region_info")
class RegionServiceTestCase(TestCase):
    """RegionService 테스트 (SGISService 모킹)"""

    def setUp(self):
        # 테스트 사용자 생성 - 외래 키 제약 조건 해결을 위해 필요
        self.test_user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            nickname="테스터",
            phone_number="01012345678",
        )

        self.test_location = Point(126.9780, 37.5665, srid=4326)  # 서울시청 좌표

        # 가상의 지역 정보 응답
        self.mock_region_info = {
            "sido_cd": "11",
            "sido_nm": "서울특별시",
            "sgg_cd": "11000",
            "sgg_nm": "중구",
            "adm_cd": "1100000",
            "adm_nm": "명동",
        }

    def test_verify_user_location_success(self, mock_get_region_info):
        """위치 인증 성공 테스트"""
        # SGIS API 응답 모킹
        mock_get_region_info.return_value = self.mock_region_info

        # 위치 인증 테스트
        result = RegionService.verify_user_location(
            user_id=self.test_user.id,  # 실제 생성된 사용자 ID 사용
            latitude=self.test_location.y,
            longitude=self.test_location.x,
        )

        # 검증
        self.assertTrue(result["success"])
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertEqual(result["data"]["sido"], "서울특별시")
        self.assertEqual(result["data"]["sigungu"], "중구")
        self.assertEqual(result["data"]["eupmyeondong"], "명동")

        # mock 함수가 호출되었는지 확인
        mock_get_region_info.assert_called_once()

    def test_verify_user_location_api_error(self, mock_get_region_info):
        """위치 인증 실패 테스트 (API 오류)"""
        # API 오류 시뮬레이션
        mock_get_region_info.side_effect = SGISAPIException("API 호출 실패")

        # 위치 인증 테스트
        result = RegionService.verify_user_location(
            user_id=self.test_user.id,  # 실제 생성된 사용자 ID 사용
            latitude=self.test_location.y,
            longitude=self.test_location.x,
        )

        # 검증
        self.assertFalse(result["success"])
        self.assertIn("message", result)
        self.assertEqual(result["message"], "API 호출 실패")

    def test_verify_user_location_invalid_coordinates(self, mock_get_region_info):
        """유효하지 않은 좌표로 인한 위치 인증 실패 테스트"""
        # 유효하지 않은 좌표 (-100, 1000)
        result = RegionService.verify_user_location(
            user_id=self.test_user.id,  # 실제 생성된 사용자 ID 사용
            latitude=-100,
            longitude=1000,
        )

        # 검증
        self.assertFalse(result["success"])
        self.assertIn("message", result)
        self.assertEqual(result["message"], "유효하지 않은 좌표값입니다.")

        # API 호출이 일어나지 않아야 함
        mock_get_region_info.assert_not_called()


if __name__ == "__main__":
    unittest.main()
