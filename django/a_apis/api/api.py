from ninja import NinjaAPI

from .auth import router as auth_router
from .health import router as health_router
from .legal import router as legal_router
from .users import router as user_router
from .users import public_router as user_public_router

api = NinjaAPI(
    title="Auto Posting API",
    description="Auto Posting API documentation",
    version="1.0.0",
)

api.add_router("/auth/", auth_router, tags=["Auth"])
api.add_router("/users/", user_router, tags=["Users"])
api.add_router("/users/", user_public_router, tags=["Users"])
api.add_router("/legal/", legal_router, tags=["Test"])
api.add_router("/", health_router, tags=["Test"])
