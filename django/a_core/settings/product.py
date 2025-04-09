from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "dangma.store",
    "www.dangma.store",
    "api.dangma.store",
    "localhost",
    "127.0.0.1",
    "13.125.219.86",  # EC2 IP
]
CORS_ALLOWED_ORIGINS = [
    "https://dangma.store",
    "https://www.dangma.store",
    "https://api.dangma.store",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
]
CSRF_TRUSTED_ORIGINS = [
    "https://dangma.store",
    "https://www.dangma.store",
    "https://api.dangma.store",
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # React / Next.js dev server
    "http://localhost:8000",  # Django dev server
]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True  # 쿠키 및 인증 헤더를 허용합니다.
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True  # HTTPS에서만 CSRF 쿠키 전송
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_DOMAIN = ".dangma.store"
CSRF_COOKIE_DOMAIN = ".dangma.store"

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",  # PostgreSQL이 아닌 PostGIS로 변경
        "NAME": os.getenv("AWS_RDS_NAME"),
        "USER": os.getenv("AWS_RDS_USER"),
        "PASSWORD": os.getenv("AWS_RDS_PASSWORD"),
        "HOST": os.getenv("AWS_RDS_HOST"),
        "PORT": os.getenv("AWS_RDS_PORT"),
    }
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB limit
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB limit

AWS_ACCESS_KEY_ID = os.getenv("AWS_S3_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_S3_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_S3_STORAGE_BUCKET_NAME", "")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "")
AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_CLOUDFRONT_DOMAIN", "")
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}

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


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",  # 표준 출력
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",  # INFO 이상 레벨 로그를 stdout에 출력
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "propagate": False,
            "level": "INFO",
        },
    },
}
