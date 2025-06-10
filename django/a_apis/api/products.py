from typing import List, Optional

from a_apis.auth.bearer import AuthBearer
from a_apis.models.product import Product
from a_apis.schema.chat import (
    MannerRatingCreateSchema,
    MannerRatingResponseSchema,
    PriceOfferActionSchema,
    PriceOfferCreateSchema,
    PriceOfferListSchema,
    PriceOfferResponseSchema,
    ReviewCreateSchema,
    ReviewResponseSchema,
    TradeCompleteSchema,
)
from a_apis.schema.products import (
    CategoryListResponseSchema,
    CategorySearchResponseSchema,
    ProductCreateSchema,
    ProductInterestSchema,
    ProductListResponseSchema,
    ProductResponseSchema,
    ProductStatusUpdateSchema,
)
from a_apis.service.products import ProductService
from ninja import File, Query, Router
from ninja.files import UploadedFile

from django.db import transaction
from django.shortcuts import get_object_or_404

router = Router(auth=AuthBearer())


# 명시적인 라우트 먼저 등록 (경로 충돌 방지)
@router.get("/my-interests", response=ProductListResponseSchema)
def get_my_interests(request, page: int = 1, page_size: int = 20):
    """내 관심 상품 목록 API"""
    return ProductService.get_interest_products(
        user_id=request.user.id, page=page, page_size=page_size
    )


@router.get("/my-products", response=ProductListResponseSchema)
def get_my_products(
    request, status: Optional[str] = None, page: int = 1, page_size: int = 20
):
    """내 판매 상품 목록 API"""
    return ProductService.get_user_products(
        user_id=request.user.id, status=status, page=page, page_size=page_size
    )


# 카테고리 관련 API (상품 ID 경로보다 먼저 정의)
@router.get("/categories", response=CategoryListResponseSchema)
def get_categories(request):
    """
    모든 카테고리 목록 조회 API

    상품 등록/수정 시 선택 가능한 모든 카테고리 목록 반환
    """
    return ProductService.get_categories()


@router.get("/categories/suggest", response=CategorySearchResponseSchema)
def suggest_categories(request, title: str):
    """
    제목 기반 카테고리 추천 API

    입력된 상품 제목에 기반하여 적합한 카테고리를 추천
    최소 2글자 이상 입력

    Parameters:
        title: 상품 제목
    """
    return ProductService.suggest_categories(title)


# 새로운 API 엔드포인트들 (구체적인 경로를 먼저 정의)
@router.get("/nearby-keyword")
def get_products_by_keyword_in_region(
    request, keyword: str, radius: float = 3.0, limit: int = 30
):
    """
    활동지역 범위 내 키워드 관련 상품 추천 API

    사용자의 활동지역을 중심으로 지정된 반경 내에서 키워드와 관련된 상품을 추천합니다.

    Parameters:
        keyword: 검색할 키워드
        radius: 검색 반경 (km 단위, 기본값 3km)
        limit: 반환할 상품 개수 (기본값 30개)

    Returns:
        상품 목록과 검색 정보
    """
    return ProductService.get_products_by_keyword_in_region(
        user_id=request.user.id, keyword=keyword, radius=radius, limit=limit
    )


@router.get("/user/{user_id}/products")
def get_user_sales_products(
    request,
    user_id: int,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    특정 유저의 판매 상품 목록 조회 API

    특정 사용자가 판매 중인 상품 목록을 조회합니다.

    Parameters:
        user_id: 조회할 사용자 ID
        status: 필터링할 상품 상태 (new, reserved, soldout)
        page: 페이지 번호 (기본값 1)
        page_size: 페이지 크기 (기본값 20)

    Returns:
        해당 사용자의 상품 목록과 페이지네이션 정보
    """
    return ProductService.get_user_sales_products(
        user_id=request.user.id,
        target_user_id=user_id,
        status=status,
        page=page,
        page_size=page_size,
    )


# 나머지 라우트 등록
@router.post("", response=ProductResponseSchema)
@transaction.atomic
def create_product(
    request,
    data: ProductCreateSchema,
    images: List[UploadedFile] = File(...),  # 필수
):
    """
    상품 등록 API

    필수 항목: 상품 정보(title, trade_type 등), 이미지(최소 1장)

    성공: 생성된 상품 정보 반환
    실패: 유효성 검증 오류 메시지
    """
    # 이미지 유효성 검증
    if not images:
        return {
            "success": False,
            "message": "상품 이미지는 최소 1장 이상 등록해야 합니다.",
        }
    if len(images) > 10:
        return {
            "success": False,
            "message": "상품 이미지는 최대 10장까지 등록 가능합니다.",
        }

    # 판매하기인 경우 가격 필수
    if data.trade_type == "sale" and not data.price:
        return {"success": False, "message": "판매 가격을 입력해주세요."}

    return ProductService.create_product(
        user_id=request.user.id, data=data, images=images
    )


@router.get("", response=ProductListResponseSchema)
def list_products(
    request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    trade_type: Optional[str] = None,
    region_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    상품 목록 조회 API

    필터링 옵션:
    - search: 검색어 (상품명, 설명 검색)
    - status: 상품 상태 필터 (new: 판매중, reserved: 예약중, soldout: 판매완료)
    - trade_type: 거래 방식 필터 (sale: 판매하기, share: 나눔하기)
    - region_id: 특정 동네 ID 필터 (설정된 경우 해당 동네의 상품만 표시, 없으면 현재 활성화된 동네 기준)

    페이징:
    - page: 페이지 번호 (기본값: 1)
    - page_size: 페이지당 상품 수 (기본값: 20)

    예시 엔드포인트:
    - 기본 조회: /api/products
    - 검색: /api/products?search=자전거
    - 필터링: /api/products?status=new&trade_type=sale
    - 동네 필터링: /api/products?region_id=123
    - 페이징: /api/products?page=2&page_size=10
    - 복합 쿼리: /api/products?search=자전거&status=new&region_id=123&page=2

    성공: 상품 목록과 페이징 정보 반환
    """
    filter_params = {
        "search": search,
        "status": status,
        "trade_type": trade_type,
        "region_id": region_id,
        "page": page,
        "page_size": page_size,
    }

    return ProductService.get_products(
        user_id=request.user.id, filter_params=filter_params
    )


@router.get("/{product_id}", response=ProductResponseSchema)
def get_product(request, product_id: int):
    """
    상품 상세 조회 API

    경로 파라미터:
    - product_id: 조회할 상품 ID

    성공: 상품 상세 정보와 판매자 정보 반환
    실패: 존재하지 않는 상품 오류 메시지
    """
    return ProductService.get_product(product_id=product_id, user_id=request.user.id)


@router.put("/{product_id}", response=ProductResponseSchema)
@transaction.atomic
def update_product(
    request,
    product_id: int,
    data: ProductCreateSchema,
    images: Optional[List[UploadedFile]] = None,
):
    """상품 정보 수정 API

    상품 정보 / 이미지 수정 가능
    이미지를 전송하면 기존 이미지를 모두 삭제하고 새로운 이미지로 대체 가능.
    """
    # 상품 소유자 확인
    product = get_object_or_404(Product, id=product_id)
    if product.user_id != request.user.id:
        return {"success": False, "message": "상품 수정 권한이 없습니다."}

    # 이미지 유효성 검증 (이미지 첨부 시)
    if images and len(images) > 10:
        return {
            "success": False,
            "message": "상품 이미지는 최대 10장까지 등록 가능합니다.",
        }

    # 판매하기인 경우 가격 필수
    if data.trade_type == "sale" and not data.price:
        return {"success": False, "message": "판매 가격을 입력해주세요."}

    return ProductService.update_product(
        product_id=product_id, user_id=request.user.id, data=data, images=images
    )


@router.patch("/{product_id}/status", response=ProductResponseSchema)
def update_product_status(request, product_id: int, data: ProductStatusUpdateSchema):
    """상품 상태 변경 API

    상품 상태를 변경 (판매중/예약중/판매완료)
    """
    # 상품 소유자 확인
    product = get_object_or_404(Product, id=product_id)
    if product.user_id != request.user.id:
        return {"success": False, "message": "상품 상태 변경 권한이 없습니다."}

    return ProductService.update_product_status(
        product_id=product_id, user_id=request.user.id, status=data.status
    )


@router.post("/{product_id}/refresh", response=ProductResponseSchema)
def refresh_product(request, product_id: int):
    """상품 끌어올리기 API

    상품을 끌어올려 상품 목록에서 상단에 노출
    하루에 최대 3회까지 가능
    """
    # 상품 소유자 확인
    product = get_object_or_404(Product, id=product_id)
    if product.user_id != request.user.id:
        return {"success": False, "message": "상품 끌어올리기 권한이 없습니다."}

    return ProductService.refresh_product(
        product_id=product_id, user_id=request.user.id
    )


@router.delete("/{product_id}", response=ProductResponseSchema)
def delete_product(request, product_id: int):
    """상품 삭제 API"""
    # 상품 소유자 확인
    product = get_object_or_404(Product, id=product_id)
    if product.user_id != request.user.id:
        return {"success": False, "message": "상품 삭제 권한이 없습니다."}

    return ProductService.delete_product(product_id=product_id, user_id=request.user.id)


@router.post("/{product_id}/interest", response=ProductResponseSchema)
def toggle_interest(request, product_id: int):
    """
    상품 관심 등록/해제 API

    경로 파라미터:
    - product_id: 관심 등록/해제할 상품 ID

    응답:
    - 관심 등록 시: "관심 상품으로 등록되었습니다."
    - 관심 해제 시: "관심 상품에서 해제되었습니다."

    인증 필수: Bearer 토큰 헤더 필요
    """
    return ProductService.toggle_interest_product(
        product_id=product_id, user_id=request.user.id
    )


@router.post("/{product_id}/price-offer", response=PriceOfferResponseSchema)
def create_price_offer(request, product_id: int, data: PriceOfferCreateSchema):
    """
    가격 제안 API

    판매자가 가격 제안을 허용한 상품에 대해 구매 희망자가 가격 제안하는 기능

    경로 파라미터:
    - product_id: 가격 제안할 상품 ID

    요청 데이터:
    - price: 제안 가격
    - chat_room_id: (선택사항) 채팅방 ID

    응답:
    - 성공: 가격 제안 정보 반환
    - 실패: 오류 메시지
    """
    return ProductService.create_price_offer(
        product_id=product_id,
        user_id=request.user.id,
        price=data.price,
        chat_room_id=data.chat_room_id,
    )


@router.get("/{product_id}/price-offers", response=PriceOfferListSchema)
def get_price_offers(request, product_id: int):
    """
    가격 제안 목록 조회 API

    상품에 대한 가격 제안 목록을 조회 (판매자만 조회 가능)

    경로 파라미터:
    - product_id: 상품 ID

    응답:
    - 성공: 가격 제안 목록 반환
    - 실패: 오류 메시지
    """
    return ProductService.get_price_offers(
        product_id=product_id, user_id=request.user.id
    )


@router.post("/price-offers/{offer_id}/respond", response=PriceOfferResponseSchema)
def respond_to_price_offer(request, offer_id: int, data: PriceOfferActionSchema):
    """
    가격 제안 수락/거절 API

    구매자의 가격 제안에 대해 판매자가 수락 또는 거절 가능

    경로 파라미터:
    - offer_id: 가격 제안 ID

    요청 데이터:
    - action: 'accept' 또는 'reject'

    응답:
    - 성공: 수락/거절된 가격 제안 정보 반환
    - 실패: 오류 메시지
    """
    return ProductService.respond_to_price_offer(
        offer_id=offer_id, user_id=request.user.id, action=data.action
    )


@router.post("/{product_id}/complete", response=ProductResponseSchema)
def complete_trade(request, product_id: int, data: TradeCompleteSchema):
    """
    거래 완료 처리 API

    상품 거래가 완료되었음을 기록 (판매자만 가능)

    경로 파라미터:
    - product_id: 상품 ID

    요청 데이터:
    - buyer_id: 구매자 ID
    - final_price: (선택사항) 최종 거래 가격

    응답:
    - 성공: 거래 완료된 상품 정보 반환
    - 실패: 오류 메시지
    """
    return ProductService.complete_trade(
        product_id=product_id,
        user_id=request.user.id,
        buyer_id=data.buyer_id,
        final_price=data.final_price,
    )


@router.post("/{product_id}/review", response=ReviewResponseSchema)
def create_review(request, product_id: int, data: ReviewCreateSchema):
    """
    거래 후기 작성 API

    거래 완료된 상품에 대한 후기 작성 (거래 당사자만 가능)

    경로 파라미터:
    - product_id: 상품 ID

    요청 데이터:
    - content: 후기 내용

    응답:
    - 성공: 작성된 후기 정보 반환
    - 실패: 오류 메시지
    """
    return ProductService.create_review(
        product_id=product_id, user_id=request.user.id, content=data.content
    )


@router.post("/{product_id}/manner-rating", response=MannerRatingResponseSchema)
def create_manner_rating(request, product_id: int, data: MannerRatingCreateSchema):
    """
    매너 평가 등록 API

    거래 완료된 상품에 대한 상대방의 매너를 평가 (거래 당사자만 가능)

    경로 파라미터:
    - product_id: 상품 ID

    요청 데이터:
    - rating_types: 평가 유형 목록 (아래 값 중 하나 이상 선택)
      * 긍정적 평가
        - time: 시간 약속을 잘 지켜요
        - response: 응답이 빨라요
        - kind: 친절하고 매너가 좋아요
        - accurate: 상품 상태가 설명과 일치해요
        - negotiable: 가격 제안에 대해 긍정적이에요
      * 부정적 평가
        - bad_time: 약속시간을 안 지켜요
        - bad_response: 응답이 느려요
        - bad_manner: 불친절해요
        - bad_accuracy: 상품 상태가 설명과 달라요
        - bad_price: 가격 흥정이 너무 심해요

    응답:
    - 성공: 등록된 매너 평가 정보 반환
    - 실패: 오류 메시지
    """
    return ProductService.create_manner_rating(
        product_id=product_id, user_id=request.user.id, rating_types=data.rating_types
    )
