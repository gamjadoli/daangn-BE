from a_apis.auth.bearer import AuthBearer
from a_apis.schema.region import NearbyRegionsResponseSchema  # 추가
from a_apis.schema.region import PublicRegionResponseSchema  # 새로 추가한 스키마
from a_apis.schema.region import (
    LocationVerificationSchema,
    RegionListResponseSchema,
    RegionResponseSchema,
)
from a_apis.service.region import RegionService, SGISService
from ninja import Router
from ninja.errors import HttpError

router = Router(auth=AuthBearer())
public_router = Router()  # 인증 없이 접근 가능한 라우터


@router.post("/verify-location", response=RegionResponseSchema)
def verify_location(request, data: LocationVerificationSchema):
    """
    활동지역 인증 API

    인증 필수: Bearer 토큰 헤더 필요
    필수 항목: latitude(위도), longitude(경도)

    성공: 인증된 활동지역 정보 반환
    실패: 지원되지 않는 지역 또는 위치 정보 오류 메시지
    """
    result = RegionService.verify_user_location(
        user_id=request.user.id, latitude=data.latitude, longitude=data.longitude
    )

    if not result["success"]:
        raise HttpError(400, result["message"])
    return result


@router.get("/regions", response=RegionListResponseSchema)
def get_user_regions(request):
    """
    활동지역 목록 조회 API

    인증 필수: Bearer 토큰 헤더 필요

    성공: 사용자의 인증된 활동지역 목록 반환
    실패: 조회 실패 메시지
    """
    result = RegionService.get_user_regions(request.user.id)

    if not result["success"]:
        raise HttpError(400, result["message"])
    return result


@router.post("/get-location-info", response=RegionResponseSchema)
def get_location_info(request, data: LocationVerificationSchema):
    """
    위치 정보 조회 API

    인증 필수: Bearer 토큰 헤더 필요
    필수 항목: latitude(위도), longitude(경도)

    성공: 해당 좌표의 시/도, 시/군/구, 읍/면/동 정보 반환
    실패: 위치 정보 조회 실패 메시지
    """
    try:
        sgis = SGISService()
        region_info = sgis.get_region_info(data.latitude, data.longitude)

        return {
            "success": True,
            "message": "지역 정보가 조회되었습니다.",
            "data": {
                "sido": region_info["sido_nm"],
                "sigungu": region_info["sgg_nm"],
                "eupmyeondong": region_info["adm_nm"],
                "eupmyeondong_code": region_info["adm_cd"],
            },
        }
    except Exception as e:
        return {"success": False, "message": f"지역 정보 조회 실패: {str(e)}"}


@router.delete("/regions/{region_id}", response=RegionResponseSchema)
def delete_region(request, region_id: int):
    """
    활동지역 삭제 API

    인증 필수: Bearer 토큰 헤더 필요
    경로 파라미터: region_id (삭제할 활동지역 ID, 활동지역 조회 API 응답의 id 값)

    성공: 활동지역 삭제 완료 메시지
    실패: 권한 없음 또는 존재하지 않는 지역 오류 메시지
    """
    result = RegionService.delete_user_region(
        user_id=request.user.id, region_id=region_id
    )

    if not result["success"]:
        raise HttpError(400, result["message"])
    return result


@public_router.post("/lookup-location", response=PublicRegionResponseSchema)
def lookup_location(request, data: LocationVerificationSchema):
    """
    위치 정보 조회 API (회원가입용, 인증 불필요)

    좌표를 기준으로 행정구역 정보만 반환하고, 사용자 활동지역은 등록하지 않음

    필수 항목: latitude(위도), longitude(경도)

    성공: 해당 좌표의 시/도, 시/군/구, 읍/면/동 정보 반환
    실패: 위치 정보 조회 실패 메시지
    """
    try:
        # 좌표 유효성 검증
        if not RegionService.validate_coordinates(data.latitude, data.longitude):
            return {"success": False, "message": "유효하지 않은 좌표값입니다."}

        # SGIS API를 통해 위치 정보 조회
        sgis = SGISService()
        region_info = sgis.get_region_info(data.latitude, data.longitude)

        return {
            "success": True,
            "message": "위치 정보를 조회했습니다.",
            "data": {
                "sido": region_info["sido_nm"],
                "sigungu": region_info["sgg_nm"],
                "eupmyeondong": region_info["adm_nm"],
                "latitude": data.latitude,
                "longitude": data.longitude,
            },
        }
    except Exception as e:
        return {"success": False, "message": f"위치 정보 조회 실패: {str(e)}"}


@public_router.post("/nearby-regions", response=NearbyRegionsResponseSchema)
def get_nearby_regions(request, data: LocationVerificationSchema):
    """
    근처 동네 목록 조회 API (회원가입용, 인증 없음)

    위치 기준 주변 동네 조회. 반경 10km 내 동네를 거리순으로 최대 10개 반환.

    입력값:
    - latitude: 위도 좌표
    - longitude: 경도 좌표

    응답:
    - 성공: 거리순 정렬된 동네 목록
    - 실패: 오류 메시지
    """
    return RegionService.get_nearby_regions(
        latitude=data.latitude, longitude=data.longitude
    )
