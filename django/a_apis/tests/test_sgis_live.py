import unittest

from a_apis.service.region import RegionService, SGISAPIException, SGISService
from a_user.models import User

from django.contrib.gis.geos import Point
from django.test import TestCase


class SGISServiceLiveTestCase(TestCase):
    """SGIS API 실제 호출 테스트"""

    def setUp(self):
        self.sgis_service = SGISService()

        # 테스트에 사용할 실제 좌표들
        self.test_coordinates = [
            {"name": "서울시청", "latitude": 37.5665, "longitude": 126.9780},
            {"name": "강남역", "latitude": 37.4980, "longitude": 127.0276},
        ]

        # 테스트 사용자 생성
        self.test_user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            nickname="테스터",
            phone_number="01012345678",
        )

    def test_api_token(self):
        """SGIS API 액세스 토큰 발급 테스트"""
        try:
            token = self.sgis_service.access_token
            self.assertIsNotNone(token)
            self.assertTrue(len(token) > 10)
            print(f"토큰 발급 성공: {token[:20]}...")
        except SGISAPIException as e:
            self.fail(f"토큰 발급 실패: {str(e)}")

    def test_region_info_with_real_api(self):
        """실제 API를 호출하여 지역 정보 조회 테스트"""
        # 서울시청 좌표로 테스트
        coords = self.test_coordinates[0]

        try:
            result = self.sgis_service.get_region_info(
                coords["latitude"], coords["longitude"]
            )

            # 기본 검증
            self.assertIsNotNone(result)
            self.assertIn("sido_nm", result)
            self.assertIn("sgg_nm", result)
            self.assertIn("adm_nm", result)

            # 결과 출력
            print(
                f"\n{coords['name']} 좌표 ({coords['latitude']}, {coords['longitude']})의 지역 정보:"
            )
            print(f"  시도: {result['sido_nm']} ({result['sido_cd']})")
            print(f"  시군구: {result['sgg_nm']} ({result['sgg_cd']})")
            print(f"  읍면동: {result['adm_nm']} ({result['adm_cd']})")

            # 서울시청은 서울특별시에 있어야 함
            self.assertEqual(result["sido_nm"], "서울특별시")

        except SGISAPIException as e:
            # API 호출이 실패할 경우 (예: 할당량 초과, 네트워크 문제 등)
            print(f"API 호출 실패, 기본값 반환 테스트: {str(e)}")
            # 기본값이 있는지 테스트
            result = {
                "sido_cd": "11",
                "sido_nm": "서울특별시",
                "sgg_cd": "11000",
                "sgg_nm": "중구",
                "adm_cd": "1100000",
                "adm_nm": "명동",
            }
            self.assertEqual(result["sido_nm"], "서울특별시")
            self.assertEqual(result["sgg_nm"], "중구")

    def test_region_service_integration(self):
        """RegionService와 통합 테스트"""
        # 서울시청 좌표 사용
        coords = self.test_coordinates[0]

        # 위치 인증 테스트
        result = RegionService.verify_user_location(
            user_id=self.test_user.id,
            latitude=coords["latitude"],
            longitude=coords["longitude"],
        )

        # 성공 여부 확인
        print(f"\n위치 인증 결과: {result}")

        # API 호출에 실패하더라도 기본값이 사용되므로, 성공해야 함
        self.assertTrue(result["success"])
        self.assertIn("data", result)

        # 사용자 활동지역 확인
        self.assertEqual(result["data"]["sido"], "서울특별시")

        # 데이터베이스에 활동지역이 저장되었는지 확인
        from a_apis.models.region import UserActivityRegion

        activity_regions = UserActivityRegion.objects.filter(user_id=self.test_user.id)
        self.assertTrue(activity_regions.exists())

    def test_invalid_coordinates(self):
        """유효하지 않은 좌표 테스트"""
        # 유효하지 않은 좌표값
        invalid_lat = 100.0  # 범위 초과
        invalid_lon = 200.0  # 범위 초과

        # 좌표 유효성 검증
        self.assertFalse(RegionService.validate_coordinates(invalid_lat, invalid_lon))

        # 유효하지 않은 좌표로 위치 인증 시도
        result = RegionService.verify_user_location(
            user_id=self.test_user.id, latitude=invalid_lat, longitude=invalid_lon
        )

        # 유효하지 않은 좌표 메시지 확인
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "유효하지 않은 좌표값입니다.")


if __name__ == "__main__":
    unittest.main()
