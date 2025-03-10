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
    """현재 위치 기반 활동지역 인증"""
    result = RegionService.verify_user_location(
        user_id=request.user.id, latitude=data.latitude, longitude=data.longitude
    )

    if not result["success"]:
        raise HttpError(400, result["message"])
    return result


@router.get("/regions", response=RegionListResponseSchema)
def get_user_regions(request):
    """사용자 활동지역 목록 조회"""
    result = RegionService.get_user_regions(request.user.id)

    if not result["success"]:
        raise HttpError(400, result["message"])
    return result
