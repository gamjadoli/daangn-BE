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
from django.utils import timezone  # timezone import 추가


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
        # 1. WGS84 좌표계를 SGIS 좌표계로 변환
        convert_url = f"{self.BASE_URL}/transformation/transcoord.json"
        convert_params = {
            "accessToken": self.access_token,
            "src": "4326",  # WGS84
            "dst": "5179",  # SGIS
            "posX": str(longitude),
            "posY": str(latitude),
        }

        try:
            convert_response = requests.get(convert_url, params=convert_params)
            converted = convert_response.json()
            if converted.get("errMsg") != "Success":
                raise SGISAPIException("좌표 변환 실패")

            # 2. 변환된 좌표로 행정구역 조회
            region_url = f"{self.BASE_URL}/addr/stage.json"
            region_params = {
                "accessToken": self.access_token,
                "coord": "5179",
                "x": converted["result"]["posX"],
                "y": converted["result"]["posY"],
            }

            region_response = requests.get(region_url, params=region_params)
            region_data = region_response.json()

            if region_data.get("errMsg") != "Success":
                raise SGISAPIException("행정구역 조회 실패")

            return region_data["result"]

        except Exception as e:
            raise SGISAPIException(f"지역 정보 조회 실패: {str(e)}")


class KakaoMapService:
    """카카오맵 API 서비스 (개인 개발자용)"""

    def __init__(self):
        self.api_key = settings.KAKAO_API_KEY

    def get_region_info(self, latitude: float, longitude: float) -> dict:
        """좌표를 통한 행정구역 정보 조회"""
        url = f"https://dapi.kakao.com/v2/local/geo/coord2address.json"
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        params = {"x": longitude, "y": latitude}

        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if response.status_code == 200 and data.get("documents"):
                address = data["documents"][0]["address"]
                # 지역코드 생성 로직 (임시)
                sido_code = self._get_region_code(address["region_1depth_name"])
                sigungu_code = self._get_region_code(address["region_2depth_name"])
                adm_code = self._get_region_code(address["region_3depth_name"])

                return {
                    "sido_nm": address["region_1depth_name"],
                    "sgg_nm": address["region_2depth_name"],
                    "adm_nm": address["region_3depth_name"],
                    "sido_cd": sido_code,
                    "sgg_cd": sigungu_code,
                    "adm_cd": adm_code,
                }

            raise Exception("주소 정보를 찾을 수 없습니다.")

        except Exception as e:
            raise Exception(f"카카오맵 API 호출 실패: {str(e)}")

    def _get_region_code(self, region_name: str) -> str:
        """지역명으로 임시 코드 생성 (실제 구현 시 DB 매핑 테이블 사용)"""
        import hashlib

        # 임시로 지역명의 해시값 앞 10자리를 코드로 사용
        return hashlib.md5(region_name.encode()).hexdigest()[:10]


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
