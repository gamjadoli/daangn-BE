from ninja import NinjaAPI

from .health import router as health_router
from .products import router as product_router
from .region import public_router as region_public_router
from .region import router as region_router
from .users import public_router as user_public_router
from .users import router as user_router

api = NinjaAPI(
    title="당근마켓 API",
    description="당근마켓 클론 API documentation",
    version="1.0.0",
)


api.add_router("/users/", user_router, tags=["Users"])
api.add_router("/users/", user_public_router, tags=["Users"])
api.add_router("/", health_router, tags=["Test"])
api.add_router("/regions/", region_router, tags=["Regions"])
api.add_router(
    "/public/regions/", region_public_router, tags=["Regions"]
)  # 공개 지역 API 추가
api.add_router("/products/", product_router, tags=["Products"])
