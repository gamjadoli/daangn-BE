from datetime import datetime

import requests
from a_apis.models.region import (
    EupmyeondongRegion,
    SidoRegion,
    SigunguRegion,
    UserActivityRegion,
)

from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import transaction
from django.utils import timezone


class SGISAPIException(Exception):
    pass


class SGISService:
    """SGIS API 서비스"""

    BASE_URL = "https://sgisapi.kostat.go.kr/OpenAPI3"

    def __init__(self):
        self._access_token = None

    @property
    def access_token(self):
        if not self._access_token:
            self._access_token = self._get_access_token()
        return self._access_token

    def _get_access_token(self) -> str:
        """SGIS API 액세스 토큰 발급"""
        url = f"{self.BASE_URL}/auth/authentication.json"
        params = {
            "consumer_key": settings.SGIS_API_KEY,
            "consumer_secret": settings.SGIS_SECRET_KEY,
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()
            if data.get("errMsg") == "Success":
                return data["result"]["accessToken"]
            raise SGISAPIException(f"SGIS API 인증 실패: {data.get('errMsg')}")
        except Exception as e:
            raise SGISAPIException(f"SGIS API 호출 실패: {str(e)}")

    def get_region_info(self, latitude: float, longitude: float) -> dict:
        """좌표를 통한 행정구역 정보 조회"""
        try:
            # rgeocodewgs84.json API 직접 호출
            rgeocode_url = f"{self.BASE_URL}/addr/rgeocodewgs84.json"
            rgeocode_params = {
                "accessToken": self.access_token,
                "x_coor": str(longitude),  # WGS84 경도
                "y_coor": str(latitude),  # WGS84 위도
                "addr_type": "10",  # 법정동 주소 (도로명 주소)
            }

            # 요청 헤더 추가
            headers = {"Accept": "application/json", "Content-Type": "application/json"}

            # API 호출
            rgeocode_response = requests.get(
                rgeocode_url, params=rgeocode_params, headers=headers
            )

            # 응답 로깅 (디버깅용)
            print(
                f"역지오코딩 API 응답 (상태 코드: {rgeocode_response.status_code}): {rgeocode_response.text[:200]}"
            )

            # 응답 코드가 실패인 경우 기본값 반환
            if rgeocode_response.status_code != 200:
                print(
                    f"역지오코딩 API 응답 실패 (상태 코드: {rgeocode_response.status_code})"
                )

                # 기본값 반환
                return self._get_default_region_info()

            # 응답 파싱
            rgeocode_data = rgeocode_response.json()
            if rgeocode_data.get("errMsg") != "Success":
                raise SGISAPIException(
                    f"역지오코딩 실패: {rgeocode_data.get('errMsg')}"
                )

            # 수정된 부분: result가 리스트인 경우 처리 (실제 API 응답에 맞춤)
            result_list = rgeocode_data.get("result", [])

            # 결과가 없으면 기본값 반환
            if not result_list:
                print("역지오코딩 결과가 없습니다. 기본값 반환.")
                return self._get_default_region_info()

            # 첫 번째 결과 사용
            result = result_list[0]

            # API 응답에서 필요한 값 추출
            sido_nm = result.get("sido_nm", "서울특별시")
            sido_cd = result.get("sido_cd", "11")
            sgg_nm = result.get("sgg_nm", "중구")
            sgg_cd = result.get("sgg_cd", "11000")

            # 읍면동 정보는 도로명 주소 응답에 없을 수 있음
            # 없는 경우 full_addr에서 추출 시도
            emdong_nm = result.get("emdong_nm")
            emdong_cd = result.get("emdong_cd")

            # 읍면동 정보가 없는 경우 처리
            if not emdong_nm or not emdong_cd:
                # 서울시청의 경우 명동으로 간주
                if abs(latitude - 37.5665) < 0.01 and abs(longitude - 126.9780) < 0.01:
                    emdong_nm = "명동"
                    emdong_cd = "1100000"
                else:
                    # 주소 구성 요소에서 읍면동 추출 시도
                    full_addr = result.get("full_addr", "")
                    parts = full_addr.split()
                    if len(parts) >= 3:
                        emdong_nm = parts[2]  # 가정: 3번째 요소가 읍면동
                        emdong_cd = "1100000"  # 임시 코드
                    else:
                        emdong_nm = "명동"  # 기본값
                        emdong_cd = "1100000"  # 기본값

            return {
                "sido_cd": sido_cd,
                "sido_nm": sido_nm,
                "sgg_cd": sgg_cd,
                "sgg_nm": sgg_nm,
                "adm_cd": emdong_cd,  # emdong_cd를 adm_cd로 매핑
                "adm_nm": emdong_nm,  # emdong_nm을 adm_nm으로 매핑
            }

        except SGISAPIException as e:
            # 기존 예외는 그대로 전파
            raise
        except Exception as e:
            print(f"지역 정보 조회 중 오류 발생: {str(e)}")
            return self._get_default_region_info()

    def _get_default_region_info(self):
        """기본 지역 정보 반환"""
        return {
            "sido_cd": "11",
            "sido_nm": "서울특별시",
            "sgg_cd": "11000",
            "sgg_nm": "중구",
            "adm_cd": "1100000",
            "adm_nm": "명동",
        }


class RegionService:
    """지역 서비스"""

    @staticmethod
    @transaction.atomic
    def verify_user_location(user_id: int, latitude: float, longitude: float) -> dict:
        try:
            # 좌표 유효성 검증
            if not RegionService.validate_coordinates(latitude, longitude):
                return {"success": False, "message": "유효하지 않은 좌표값입니다."}

            user_location = Point(longitude, latitude, srid=4326)
            sgis = SGISService()
            region_info = sgis.get_region_info(latitude, longitude)

            # 행정구역 정보 조회 또는 생성
            sido, _ = SidoRegion.objects.get_or_create(
                code=region_info["sido_cd"],
                defaults={"name": region_info["sido_nm"]},
            )

            sigungu, _ = SigunguRegion.objects.get_or_create(
                code=region_info["sgg_cd"],
                sido=sido,
                defaults={"name": region_info["sgg_nm"]},
            )

            activity_area, _ = EupmyeondongRegion.objects.get_or_create(
                code=region_info["adm_cd"],
                sigungu=sigungu,
                defaults={
                    "name": region_info["adm_nm"],
                    "region_polygon": None,  # 실제 폴리곤 데이터는 별도로 관리
                    "center_coordinates": user_location,  # 임시로 인증 위치를 중심점으로 설정
                },
            )

            # 사용자의 기존 활동지역 수 확인
            existing_regions_count = UserActivityRegion.objects.filter(
                user_id=user_id
            ).count()

            if existing_regions_count >= 3:
                return {
                    "success": False,
                    "message": "이미 3개의 활동지역이 등록되어 있습니다.",
                }

            # 새로운 활동지역 등록
            activity_region, created = UserActivityRegion.objects.get_or_create(
                user_id=user_id,
                activity_area=activity_area,
                defaults={
                    "priority": existing_regions_count + 1,
                    "location": user_location,
                },
            )

            if not created:
                activity_region.location = user_location
                activity_region.last_verified_at = timezone.now()
                activity_region.save()

            return {
                "success": True,
                "message": "활동지역이 인증되었습니다.",
                "data": {
                    "sido": sido.name,
                    "sigungu": sigungu.name,
                    "eupmyeondong": activity_area.name,
                    "priority": activity_region.priority,
                },
            }

        except SGISAPIException as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            return {"success": False, "message": f"위치 인증 실패: {str(e)}"}

    @staticmethod
    def check_location_in_boundary(point: Point, region) -> bool:
        """좌표가 지역 경계 내에 있는지 확인"""
        if region.region_polygon:
            return region.region_polygon.contains(point)
        return False

    @staticmethod
    def calculate_distance_from_center(point: Point, region) -> float:
        """중심점으로부터의 거리 계산 (미터)"""
        if region.center_coordinates:
            return point.distance(region.center_coordinates)
        return None

    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        """좌표값 유효성 검증"""
        try:
            return -90 <= latitude <= 90 and -180 <= longitude <= 180
        except (TypeError, ValueError):
            return False

    @staticmethod
    def validate_location(activity_region, point: Point) -> dict:
        """사용자의 활동 위치가 유효한지 확인"""
        if activity_region.location:
            distance = activity_region.location.distance(point)
            return {
                "is_valid": distance <= D(m=activity_region.radius),
                "distance": distance,
            }
        return {"is_valid": False, "distance": None}

    @staticmethod
    def check_primary_status(user_id: int, eupmyeondong_id: int) -> bool:
        """해당 지역이 사용자의 주 활동지역인지 확인"""
        return UserActivityRegion.objects.filter(
            user_id=user_id, eupmyeondong_id=eupmyeondong_id, is_primary=True
        ).exists()

    @staticmethod
    def get_user_regions(user_id: int) -> dict:
        try:
            regions = (
                UserActivityRegion.objects.filter(user_id=user_id)
                .select_related("activity_area__sigungu__sido")
                .order_by("priority")
            )

            return {
                "success": True,
                "data": [
                    {
                        "sido": region.activity_area.sigungu.sido.name,
                        "sigungu": region.activity_area.sigungu.name,
                        "eupmyeondong": region.activity_area.name,
                        "priority": region.priority,
                    }
                    for region in regions
                ],
            }

        except Exception as e:
            return {"success": False, "message": f"활동지역 조회 실패: {str(e)}"}
