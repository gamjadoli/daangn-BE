from .base import *

DEBUG = True

INSTALLED_APPS += [
    "django_extensions",
]

ALLOWED_HOSTS = ["*"]
SERVER_BASE_URL = "http://localhost:3000"

# EMAIL_BACKEND 설정 제거 (base.py의 SMTP 설정 사용)


# CORS 설정
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

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

# 디버그 로깅 설정
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
