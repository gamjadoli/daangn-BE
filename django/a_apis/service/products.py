from a_apis.models import Product, ProductImage
from a_apis.service.files import FileService

from django.contrib.gis.geos import Point
from django.db import transaction


class ProductService:
    @staticmethod
    @transaction.atomic
    def create_product(user_id: int, data: dict, images: list = None) -> dict:
        try:
            # 거래 위치 생성
            meeting_point = Point(
                data.meeting_location.longitude,
                data.meeting_location.latitude,
                srid=4326,
            )

            # 상품 생성
            product = Product.objects.create(
                user_id=user_id,
                title=data.title,
                trade_type=data.trade_type,
                price=data.price if data.trade_type == "sale" else None,
                accept_price_offer=data.accept_price_offer,
                description=data.description,
                meeting_location=meeting_point,
                location_description=data.meeting_location.description,
            )

            # 이미지 처리
            if images:
                for image_file in images:
                    # FileService를 통해 파일 업로드
                    file = FileService.upload_file(image_file)
                    ProductImage.objects.create(product=product, file=file)

            return {
                "success": True,
                "message": "상품이 등록되었습니다.",
                "data": {
                    "id": product.id,
                    "title": product.title,
                    "trade_type": product.get_trade_type_display(),
                    "price": product.price,
                },
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
