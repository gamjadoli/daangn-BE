from .email_verification import EmailVerification
from .files import File
from .product import InterestProduct, Product, ProductImage
from .region import EupmyeondongRegion, SidoRegion, SigunguRegion, UserActivityRegion

# 명시적으로 모든 모델 나열
__all__ = [
    "EmailVerification",
    "File",
    "Product",
    "ProductImage",
    "InterestProduct",
    "SidoRegion",
    "SigunguRegion",
    "EupmyeondongRegion",
    "UserActivityRegion",
]
