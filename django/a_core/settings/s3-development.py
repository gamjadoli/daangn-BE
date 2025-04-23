from .base import *

DEBUG = True

INSTALLED_APPS += [
    "django_extensions",
]

# 로컬 개발 환경에서는 인메모리 채널 레이어 사용
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "api.myapp.com"]
SERVER_BASE_URL = "http://localhost:3000"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CORS_ALLOWED_ORIGINS = [
    "https://myapp.com",
    "https://api.myapp.com",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
]


DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",  # PostGIS 엔진 사용
        "NAME": os.getenv("DEV_DB_NAME"),
        "USER": os.getenv("DEV_DB_USER"),  # 기본 PostgreSQL 유저네임
        "PASSWORD": os.getenv("DEV_DB_PASSWORD"),  # PostgreSQL 설치시 지정한 비밀번호
        "HOST": os.getenv("DEV_DB_HOST"),
        "PORT": os.getenv("DEV_DB_PORT"),
    }
}

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB limit
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB limit
# Shell Plus 설정
SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True
SHELL_PLUS_IMPORTS = [
    "from datetime import datetime, timedelta",
    "from django.conf import settings",
    "from django.core.cache import cache",
]


# JWT 설정
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),  # 개발환경에서는 7일로 설정
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

AWS_ACCESS_KEY_ID = os.getenv("AWS_S3_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_S3_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_S3_STORAGE_BUCKET_NAME", "")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "")
AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_CLOUDFRONT_DOMAIN", "")

STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"


MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

AWS_QUERYSTRING_AUTH = False

STATICFILES_DIRS = []

# 미디어 파일이 저장될 폴더 경로 설정
MEDIAFILES_LOCATION = "media"
AWS_LOCATION = MEDIAFILES_LOCATION

# s3 storage 설정
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB limit
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB limit

# Shell Plus 설정
SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True
SHELL_PLUS_IMPORTS = [
    "from datetime import datetime, timedelta",
    "from django.conf import settings",
    "from django.core.cache import cache",
]


# GDAL 라이브러리 경로 설정
GDAL_LIBRARY_PATH = "/opt/homebrew/opt/gdal/lib/libgdal.dylib"
GEOS_LIBRARY_PATH = "/opt/homebrew/opt/geos/lib/libgeos_c.dylib"
