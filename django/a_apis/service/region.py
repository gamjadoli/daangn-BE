import concurrent.futures
import logging
import math
import time
from datetime import datetime

import requests
from a_apis.models.region import (
    EupmyeondongRegion,
    SidoRegion,
    SigunguRegion,
    UserActivityRegion,
)

from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import transaction
from django.utils import timezone

# 로거 설정
logger = logging.getLogger(__name__)


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
        start_time = time.time()
        logger.info(f"SGIS 지역 정보 조회 시작: lat={latitude}, lon={longitude}")

        try:
            rgeocode_url = f"{self.BASE_URL}/addr/rgeocodewgs84.json"
            rgeocode_params = {
                "accessToken": self.access_token,
                "x_coor": str(longitude),
                "y_coor": str(latitude),
                "addr_type": "20",
            }
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            rgeocode_response = requests.get(
                rgeocode_url, params=rgeocode_params, headers=headers
            )
            print(
                f"역지오코딩 API 응답 (상태 코드: {rgeocode_response.status_code}): {rgeocode_response.text[:200]}"
            )
            if rgeocode_response.status_code != 200:
                print(
                    f"역지오코딩 API 응답 실패 (상태 코드: {rgeocode_response.status_code})"
                )
                return self._get_default_region_info()

            rgeocode_data = rgeocode_response.json()
            if rgeocode_data.get("errMsg") != "Success":
                raise SGISAPIException(
                    f"역지오코딩 실패: {rgeocode_data.get('errMsg')}"
                )

            result_list = rgeocode_data.get("result", [])
            if not result_list:
                print("역지오코딩 결과가 없습니다. 기본값 반환.")
                return self._get_default_region_info()

            result = result_list[0]
            sido_nm = result.get("sido_nm", "서울특별시")
            sido_cd = result.get("sido_cd", "11")
            sgg_nm = result.get("sgg_nm", "중구")
            sgg_cd = result.get("sgg_cd", "11000")
            emdong_nm = result.get("emdong_nm")
            emdong_cd = result.get("emdong_cd")

            if not emdong_nm or not emdong_cd:
                full_addr = result.get("full_addr", "")
                parts = full_addr.split()
                if len(parts) >= 3:
                    emdong_nm = parts[2]
                    emdong_cd = "1100000"
                else:
                    emdong_nm = "명동"
                    emdong_cd = "1100000"

            total_time = time.time() - start_time
            logger.info(f"SGIS 지역 정보 조회 완료. 총 소요시간: {total_time:.4f}초")

            return {
                "sido_cd": sido_cd,
                "sido_nm": sido_nm,
                "sgg_cd": sgg_cd,
                "sgg_nm": sgg_nm,
                "adm_cd": emdong_cd,
                "adm_nm": emdong_nm,
            }

        except SGISAPIException as e:
            error_time = time.time() - start_time
            logger.error(f"SGIS API 예외 발생: {str(e)}, 소요시간: {error_time:.4f}초")
            raise
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(
                f"지역 정보 조회 중 오류 발생: {str(e)}, 소요시간: {error_time:.4f}초"
            )
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

    def get_nearby_regions(
        self, latitude: float, longitude: float, radius_km: float = 5
    ) -> list:
        """현재 위치를 중심으로 주변 지역 정보를 SGIS API를 통해 직접 조회 - 성능 개선 버전"""
        start_time = time.time()
        logger.info(
            f"SGIS API를 통한 주변 지역 조회 시작: lat={latitude}, lon={longitude}, radius={radius_km}km"
        )

        # 현재 위치의 지역 정보 먼저 조회 (거리 0)
        current_region = self.get_region_info(latitude, longitude)
        current_key = f"{current_region['sido_nm']}-{current_region['sgg_nm']}-{current_region['adm_nm']}"

        # 효율적인 샘플링 포인트 생성 (개수 줄임)
        points = self._generate_optimized_points(latitude, longitude, radius_km)
        logger.info(f"생성된 최적화 샘플링 포인트 수: {len(points)}")

        # 결과를 담을 컨테이너
        regions = [
            {
                "sido": current_region["sido_nm"],
                "sigungu": current_region["sgg_nm"],
                "eupmyeondong": current_region["adm_nm"],
                "distance": 0,
                "latitude": latitude,
                "longitude": longitude,
            }
        ]
        unique_regions = {current_key}  # 중복 제거를 위한 집합

        # 병렬 API 호출 구현
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 샘플링 포인트별 API 호출 작업 준비
            future_to_point = {
                executor.submit(self._get_region_for_point, lat, lon, dist): (
                    lat,
                    lon,
                    dist,
                )
                for lat, lon, dist in points
            }

            # 완료된 작업 처리
            for future in concurrent.futures.as_completed(future_to_point):
                point_info = future_to_point[future]
                try:
                    result = future.result()
                    if result:
                        region_key = f"{result['sido']}-{result['sigungu']}-{result['eupmyeondong']}"
                        if region_key not in unique_regions:
                            unique_regions.add(region_key)
                            regions.append(result)
                            logger.info(
                                f"신규 지역 추가: {result['sido']} {result['sigungu']} {result['eupmyeondong']}, 거리: {result['distance']}m"
                            )
                except Exception as e:
                    lat, lon, dist = point_info
                    logger.warning(
                        f"포인트 조회 실패: lat={lat}, lon={lon}, dist={dist}, 오류: {str(e)}"
                    )

        # 거리 순으로 정렬
        regions.sort(key=lambda x: x["distance"])

        total_time = time.time() - start_time
        logger.info(
            f"SGIS API 주변 지역 조회 완료: {len(regions)}개 지역, 소요시간: {total_time:.4f}초"
        )

        return regions

    def _get_region_for_point(self, lat, lon, dist):
        """단일 포인트에 대한 지역 정보 조회 - 병렬 처리용"""
        try:
            region_info = self.get_region_info(lat, lon)
            return {
                "sido": region_info["sido_nm"],
                "sigungu": region_info["sgg_nm"],
                "eupmyeondong": region_info["adm_nm"],
                "distance": dist,
                "latitude": lat,
                "longitude": lon,
            }
        except Exception as e:
            logger.error(f"포인트 지역 정보 조회 실패: {str(e)}")
            return None

    def _generate_optimized_points(
        self, center_lat: float, center_lon: float, radius_km: float
    ) -> list:
        """효율적인 샘플링 포인트 생성 - 수를 줄이고 거리별로 분산"""
        points = []

        # 위도 1도 = 약 111km, 경도 1도는 위도에 따라 다름
        lat_km = 111.0
        lon_km = 111.0 * math.cos(math.radians(center_lat))

        # 더 적은 방향으로 변경 (4방향으로 감소)
        directions = [
            (1, 0),  # 동
            (0, 1),  # 북
            (-1, 0),  # 서
            (0, -1),  # 남
        ]

        # 더 적은 거리 단계로 변경 (1km, 2km만)
        # 실제 API 호출은 현재 위치 + 8개 지점만 수행 (최대 9개)
        distances = [1, 2]

        for dist_km in distances:
            for dx, dy in directions:
                lat_offset = (dist_km * dy) / lat_km
                lon_offset = (dist_km * dx) / lon_km

                new_lat = center_lat + lat_offset
                new_lon = center_lon + lon_offset

                if -90 <= new_lat <= 90 and -180 <= new_lon <= 180:
                    distance = int(dist_km * 1000)
                    points.append((new_lat, new_lon, distance))

        return points


class RegionService:
    """지역 서비스"""

    @staticmethod
    @transaction.atomic
    def verify_user_location(user_id: int, latitude: float, longitude: float) -> dict:
        try:
            if not RegionService.validate_coordinates(latitude, longitude):
                return {"success": False, "message": "유효하지 않은 좌표값입니다."}

            user_location = Point(longitude, latitude, srid=4326)
            sgis = SGISService()
            region_info = sgis.get_region_info(latitude, longitude)

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
                    "region_polygon": None,
                    "center_coordinates": user_location,
                },
            )

            existing_regions_count = UserActivityRegion.objects.filter(
                user_id=user_id
            ).count()

            if existing_regions_count >= 3:
                return {
                    "success": False,
                    "message": "이미 3개의 활동지역이 등록되어 있습니다.",
                }

            priority = existing_regions_count + 1
            activity_region, created = UserActivityRegion.objects.get_or_create(
                user_id=user_id,
                activity_area=activity_area,
                defaults={
                    "priority": priority,
                    "location": user_location,
                },
            )

            if not created:
                activity_region.location = user_location
                activity_region.last_verified_at = timezone.now()
                activity_region.save()

            is_primary = activity_region.priority == 1

            return {
                "success": True,
                "message": "활동지역이 인증되었습니다.",
                "data": {
                    "id": activity_region.id,
                    "sido": sido.name,
                    "sigungu": sigungu.name,
                    "eupmyeondong": activity_area.name,
                    "priority": activity_region.priority,
                    "is_primary": is_primary,
                },
            }

        except SGISAPIException as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            return {"success": False, "message": f"위치 인증 실패: {str(e)}"}

    @staticmethod
    def check_location_in_boundary(point: Point, region) -> bool:
        if region.region_polygon:
            return region.region_polygon.contains(point)
        return False

    @staticmethod
    def calculate_distance_from_center(point: Point, region) -> float:
        if region.center_coordinates:
            return point.distance(region.center_coordinates)
        return None

    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        try:
            return -90 <= latitude <= 90 and -180 <= longitude <= 180
        except (TypeError, ValueError):
            return False

    @staticmethod
    def validate_location(activity_region, point: Point) -> dict:
        if activity_region.location:
            distance = activity_region.location.distance(point)
            return {
                "is_valid": distance <= D(m=activity_region.radius),
                "distance": distance,
            }
        return {"is_valid": False, "distance": None}

    @staticmethod
    def check_primary_status(user_id: int, eupmyeondong_id: int) -> bool:
        return UserActivityRegion.objects.filter(
            user_id=user_id, eupmyeondong_id=eupmyeondong_id, is_primary=True
        ).exists()

    @staticmethod
    def get_user_regions(user_id: int) -> dict:
        try:
            print(f"조회 중인 사용자 ID: {user_id}")

            regions_base = UserActivityRegion.objects.filter(user_id=user_id)
            regions_count = regions_base.count()

            if regions_count == 0:
                print(f"사용자 ID {user_id}의 활동지역이 없습니다.")
                return {
                    "success": True,
                    "message": "등록된 활동지역이 없습니다.",
                    "data": [],
                }

            regions = regions_base.select_related(
                "activity_area",
                "activity_area__sigungu",
                "activity_area__sigungu__sido",
            ).order_by("priority")

            result_data = []
            for region in regions:
                try:
                    sido_name = (
                        region.activity_area.sigungu.sido.name
                        if (
                            region.activity_area
                            and region.activity_area.sigungu
                            and region.activity_area.sigungu.sido
                        )
                        else "알 수 없음"
                    )

                    sigungu_name = (
                        region.activity_area.sigungu.name
                        if (region.activity_area and region.activity_area.sigungu)
                        else "알 수 없음"
                    )

                    is_primary = region.priority == 1

                    region_data = {
                        "id": region.id,
                        "sido": sido_name,
                        "sigungu": sigungu_name,
                        "eupmyeondong": (
                            region.activity_area.name
                            if region.activity_area
                            else "알 수 없음"
                        ),
                        "priority": region.priority,
                        "is_primary": is_primary,
                    }
                    result_data.append(region_data)
                except Exception as e:
                    print(f"지역 데이터 매핑 오류: {str(e)}, 지역 ID: {region.id}")

            return {
                "success": True,
                "message": "활동지역 조회가 완료되었습니다.",
                "data": result_data,
            }

        except Exception as e:
            return {"success": False, "message": f"활동지역 조회 실패: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def delete_user_region(user_id: int, region_id: int) -> dict:
        try:
            region = UserActivityRegion.objects.filter(
                id=region_id, user_id=user_id
            ).first()

            if not region:
                return {
                    "success": False,
                    "message": "해당 활동지역을 찾을 수 없습니다.",
                }

            deleted_priority = region.priority
            region.delete()

            remaining_regions = UserActivityRegion.objects.filter(
                user_id=user_id
            ).order_by("priority")

            for i, region in enumerate(remaining_regions):
                new_priority = i + 1
                if region.priority != new_priority:
                    region.priority = new_priority
                    region.save()

            return {"success": True, "message": "활동지역이 삭제되었습니다."}

        except Exception as e:
            return {"success": False, "message": f"활동지역 삭제 실패: {str(e)}"}

    @staticmethod
    def get_nearby_regions(
        latitude: float, longitude: float, radius_km: float = 5, limit: int = 5
    ) -> dict:
        """사용자 위치 기반 근처 동네 목록 실시간 조회 (SGIS API 활용) - 5km 반경 내 최대 5개 동네"""
        start_time = time.time()
        logger.info(
            f"근처 동네 조회 시작: lat={latitude}, lon={longitude}, radius={radius_km}km, limit={limit}개"
        )

        try:
            # 좌표 유효성 검증
            validation_start = time.time()
            if not RegionService.validate_coordinates(latitude, longitude):
                logger.error(f"유효하지 않은 좌표값: lat={latitude}, lon={longitude}")
                return {"success": False, "message": "유효하지 않은 좌표값입니다."}
            validation_time = time.time() - validation_start
            logger.info(f"좌표 유효성 검증 완료: {validation_time:.4f}초 소요")

            # SGIS API를 통해 현재 위치 및 주변 동네 정보 실시간 조회
            sgis_start = time.time()
            sgis = SGISService()

            # SGIS API로 주변 지역 직접 조회 (5km 반경)
            nearby_regions = sgis.get_nearby_regions(latitude, longitude, radius_km)

            sgis_time = time.time() - sgis_start
            logger.info(
                f"SGIS API 주변 지역 조회 완료: {sgis_time:.4f}초 소요, {len(nearby_regions)}개 지역 발견"
            )

            # 결과 데이터 가공 및 제한 (5개만)
            results_start = time.time()

            # 최대 limit(5)개 지역만 사용
            regions_data = nearby_regions[:limit]

            results_time = time.time() - results_start
            logger.info(
                f"결과 데이터 구성 완료: {results_time:.4f}초 소요, {len(regions_data)}개 지역 반환"
            )

            # 전체 처리 시간
            total_time = time.time() - start_time
            logger.info(f"근처 동네 조회 완료. 총 소요시간: {total_time:.4f}초")
            logger.info(
                f"세부 시간 - 유효성검증: {validation_time:.4f}초, SGIS API: {sgis_time:.4f}초, 결과처리: {results_time:.4f}초"
            )

            # 응답 구성
            return {
                "success": True,
                "message": f"SGIS API로 5km 반경 내 최대 5개 동네를 조회했습니다. (소요시간: {total_time:.2f}초)",
                "data": regions_data,
                "performance": {
                    "total_time": round(total_time, 4),
                    "validation_time": round(validation_time, 4),
                    "sgis_api_time": round(sgis_time, 4),
                    "results_time": round(results_time, 4),
                },
            }

        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"근처 동네 조회 실패: {str(e)}, 소요시간: {error_time:.4f}초")

            import traceback

            logger.error(f"예외 상세: {traceback.format_exc()}")

            return {
                "success": False,
                "message": f"근처 동네 조회 실패: {str(e)}",
                "performance": {"error_time": round(error_time, 4)},
            }
