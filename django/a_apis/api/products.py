from a_apis.auth.bearer import AuthBearer
from a_apis.schema.products import (
    ProductCreateSchema,
    ProductResponseSchema,
)
from a_apis.service.products import ProductService
from ninja import File, Router
from ninja.files import UploadedFile

from django.core.exceptions import ValidationError
from django.db import transaction

router = Router(auth=AuthBearer())


@router.post("/my-products", response=ProductResponseSchema)
@transaction.atomic  # 트랜잭션 추가
def create_my_product(
    request,
    data: ProductCreateSchema,
    images: list[UploadedFile] = File(...),  # 필수
):
    """내 물건팔기 API

    이미지는 최대 10장까지 등록 가능하며,
    판매하기 선택 시 가격 입력이 필수입니다.
    """
    # 이미지 개수 검증
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
