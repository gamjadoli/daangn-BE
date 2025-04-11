from a_apis.auth.bearer import AuthBearer
from a_apis.schema.region import (
    LocationVerificationSchema,
    RegionListResponseSchema,
    RegionResponseSchema,
)
from a_apis.service.region import RegionService
from ninja import Router
from ninja.errors import HttpError

router = Router(auth=AuthBearer())


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
    from a_apis.service.region import SGISService

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
