from .base import *

DEBUG = True

INSTALLED_APPS += [
    "django_extensions",
]

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "api.myapp.com"]
SERVER_BASE_URL = "http://localhost:3000"

# EMAIL_BACKEND 설정 제거 (base.py의 SMTP 설정 사용)


CORS_ALLOWED_ORIGINS = [
    "https://myapp.com",
    "https://api.myapp.com",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
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
