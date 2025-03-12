from typing import List, Optional

from ninja import Schema


class LocationVerificationSchema(Schema):
    """위치 인증 요청 스키마"""

    latitude: float
    longitude: float


class RegionDataSchema(Schema):
    """행정구역 정보 스키마"""

    sido: str
    sigungu: str
    eupmyeondong: str
    is_primary: bool


class RegionResponseSchema(Schema):
    """지역 응답 스키마"""

    success: bool
    message: Optional[str] = None
    data: Optional[RegionDataSchema] = None


class RegionListResponseSchema(Schema):
    """지역 목록 응답 스키마"""

    success: bool
    message: Optional[str] = None
    data: Optional[List[RegionDataSchema]] = None
