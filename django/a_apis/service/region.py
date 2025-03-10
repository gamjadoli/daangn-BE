from datetime import datetime

import requests
from a_apis.models.region import (
    EupmyeondongRegion,
    SidoRegion,
    SigunguRegion,
    UserActivityRegion,
)

from django.conf import settings
from django.db import transaction


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


class RegionService:
    """지역 서비스"""

    @staticmethod
    @transaction.atomic
    def verify_user_location(user_id: int, latitude: float, longitude: float) -> dict:
        """
        사용자 위치 인증 및 활동지역 등록
        """
        try:
            sgis = SGISService()
            region_info = sgis.get_region_info(latitude, longitude)

            current_version = (
                f"{datetime.now().year}-Q{(datetime.now().month-1)//3 + 1}"
            )

            # 현재 위치의 행정구역 정보 조회 또는 생성
            sido, _ = SidoRegion.objects.get_or_create(
                code=region_info["sido_cd"],
                version=current_version,
                defaults={"name": region_info["sido_nm"]},
            )

            sigungu, _ = SigunguRegion.objects.get_or_create(
                code=region_info["sgg_cd"],
                version=current_version,
                sido=sido,
                defaults={"name": region_info["sgg_nm"]},
            )

            eupmyeondong, _ = EupmyeondongRegion.objects.get_or_create(
                code=region_info["adm_cd"],
                version=current_version,
                sigungu=sigungu,
                defaults={"name": region_info["adm_nm"]},
            )

            # 사용자 활동지역 등록
            activity_region, created = UserActivityRegion.objects.get_or_create(
                user_id=user_id,
                eupmyeondong=eupmyeondong,
                defaults={"is_primary": True},
            )

            if not created:
                activity_region.is_primary = True
                activity_region.save()

            return {
                "success": True,
                "message": "활동지역이 인증되었습니다.",
                "data": {
                    "sido": sido.name,
                    "sigungu": sigungu.name,
                    "eupmyeondong": eupmyeondong.name,
                    "is_primary": True,
                },
            }

        except SGISAPIException as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            return {"success": False, "message": f"위치 인증 실패: {str(e)}"}

    @staticmethod
    def get_user_regions(user_id: int) -> dict:
        """사용자의 활동지역 목록 조회"""
        try:
            regions = UserActivityRegion.objects.filter(user_id=user_id).select_related(
                "eupmyeondong__sigungu__sido"
            )

            return {
                "success": True,
                "data": [
                    {
                        "sido": region.eupmyeondong.sigungu.sido.name,
                        "sigungu": region.eupmyeondong.sigungu.name,
                        "eupmyeondong": region.eupmyeondong.name,
                        "is_primary": region.is_primary,
                    }
                    for region in regions
                ],
            }

        except Exception as e:
            return {"success": False, "message": f"활동지역 조회 실패: {str(e)}"}
