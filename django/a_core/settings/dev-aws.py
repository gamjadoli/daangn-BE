from .base import *

DEBUG = True

SERVER_BASE_URL = "http://localhost:3000"


ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8000",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DEV_AWS_RDS_NAME"),
        "USER": os.getenv("DEV_AWS_RDS_USER"),
        "PASSWORD": os.getenv("DEV_AWS_RDS_PASSWORD"),
        "HOST": os.getenv("DEV_AWS_RDS_HOST"),
        "PORT": os.getenv("DEV_AWS_RDS_PORT"),
    }
}


# SSL 설정 비활성화
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = None  # SSL 프록시 헤더 비활성화


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB limit
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB limit
