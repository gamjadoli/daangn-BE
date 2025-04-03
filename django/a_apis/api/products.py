from typing import List, Optional

from a_apis.auth.bearer import AuthBearer
from a_apis.models.product import Product
from a_apis.schema.products import (
    ProductCreateSchema,
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
@router.get("/my-interests/", response=ProductListResponseSchema)
def get_my_interests(request, page: int = 1, page_size: int = 20):
    """내 관심 상품 목록 API"""
    return ProductService.get_interest_products(
        user_id=request.user.id, page=page, page_size=page_size
    )


@router.get("/my-products/", response=ProductListResponseSchema)
def get_my_products(
    request, status: Optional[str] = None, page: int = 1, page_size: int = 20
):
    """내 판매 상품 목록 API"""
    return ProductService.get_user_products(
        user_id=request.user.id, status=status, page=page, page_size=page_size
    )


# 나머지 라우트 등록
@router.post("/", response=ProductResponseSchema)
@transaction.atomic
def create_product(
    request,
    data: ProductCreateSchema,
    images: List[UploadedFile] = File(...),  # 필수
):
    """상품 등록 API

    이미지는 최소 1장, 최대 10장까지 등록 가능하며,
    판매하기 선택 시 가격 입력이 필수입니다.
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


@router.get("/", response=ProductListResponseSchema)
def list_products(
    request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    trade_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    """상품 목록 조회 API

    검색, 상태, 거래 타입 필터링을 지원합니다.
    """
    filter_params = {
        "search": search,
        "status": status,
        "trade_type": trade_type,
        "page": page,
        "page_size": page_size,
    }

    return ProductService.get_products(
        user_id=request.user.id, filter_params=filter_params
    )


@router.get("/{product_id}", response=ProductResponseSchema)
def get_product(request, product_id: int):
    """상품 상세 조회 API"""
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

    상품 정보와 이미지를 수정할 수 있습니다.
    이미지를 전송하면 기존 이미지를 모두 삭제하고 새로운 이미지로 대체합니다.
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

    상품 상태를 변경합니다. (판매중/예약중/판매완료)
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

    상품을 끌어올려 상품 목록에서 상단에 노출되도록 합니다.
    하루에 최대 3회까지 가능합니다.
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
    """상품 관심 등록/해제 API"""
    return ProductService.toggle_interest_product(
        product_id=product_id, user_id=request.user.id
    )
