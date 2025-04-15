from typing import List, Optional

from ninja import Field, Schema


class LocationVerificationSchema(Schema):
    """위치 인증 요청 스키마"""

    latitude: float = Field(..., description="위도 좌표 (예: 37.5665)")
    longitude: float = Field(..., description="경도 좌표 (예: 126.9780)")


class RegionDataSchema(Schema):
    """행정구역 정보 스키마"""

    id: int = Field(..., description="활동지역 ID (삭제 시 필요)")
    sido: str = Field(..., description="시/도 (예: 서울특별시, 경기도)")
    sigungu: str = Field(..., description="시/군/구 (예: 강남구, 중구)")
    eupmyeondong: str = Field(..., description="읍/면/동 (예: 역삼동, 명동)")
    priority: int = Field(..., description="우선순위 (1: 대표 지역, 2~3: 추가 지역)")
    is_primary: bool = Field(..., description="대표 지역 여부 (true: 대표 지역)")


class RegionResponseSchema(Schema):
    """지역 응답 스키마"""

    success: bool = Field(..., description="요청 처리 성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
    data: Optional[RegionDataSchema] = Field(None, description="지역 정보")


class RegionListResponseSchema(Schema):
    """지역 목록 응답 스키마"""

    success: bool = Field(..., description="요청 처리 성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
    data: Optional[List[RegionDataSchema]] = Field(None, description="지역 정보 목록")


# 새로운 퍼블릭 API용 스키마 추가
class PublicRegionDataSchema(Schema):
    """퍼블릭 API용 행정구역 정보 스키마"""

    sido: str = Field(..., description="시/도 (예: 서울특별시, 경기도)")
    sigungu: str = Field(..., description="시/군/구 (예: 강남구, 중구)")
    eupmyeondong: str = Field(..., description="읍/면/동 (예: 역삼동, 명동)")
    latitude: float = Field(..., description="위도 좌표")
    longitude: float = Field(..., description="경도 좌표")


class PublicRegionResponseSchema(Schema):
    """퍼블릭 API용 지역 응답 스키마"""

    success: bool = Field(..., description="요청 처리 성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
    data: Optional[PublicRegionDataSchema] = Field(None, description="지역 정보")


# 근처 동네 정보를 위한 스키마 추가
class NearbyRegionDataSchema(Schema):
    """근처 동네 정보 스키마"""

    sido: str = Field(..., description="시/도 (예: 서울특별시, 경기도)")
    sigungu: str = Field(..., description="시/군/구 (예: 강남구, 중구)")
    eupmyeondong: str = Field(..., description="읍/면/동 (예: 역삼동, 명동)")
    distance: int = Field(..., description="현재 위치에서의 거리(미터)")


class NearbyRegionsResponseSchema(Schema):
    """근처 동네 목록 응답 스키마"""

    success: bool = Field(..., description="요청 처리 성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
    data: Optional[List[NearbyRegionDataSchema]] = Field(
        None, description="근처 동네 목록"
    )
