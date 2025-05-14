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

# Redis 설정 업데이트
REDIS_HOST = os.getenv(
    "AWS_ELASTICACHE_ENDPOINT", "redis"
)  # 환경변수 없으면 docker 서비스명 사용
REDIS_PORT = 6379

# Channel Layer 설정 수정 (Redis 호스트 업데이트)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
            "capacity": 100,  # 채널 레이어 용량 제한
            "expiry": 60,  # 메시지 만료 시간
        },
    },
}

# 캐시 설정
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
        "OPTIONS": {
            # "CLIENT_CLASS": "django_redis.client.DefaultClient", # 호환성 문제로 제거
            "SOCKET_TIMEOUT": 5,
            "SOCKET_CONNECT_TIMEOUT": 5,
        },
        "KEY_PREFIX": "dangma",
    }
}

# 세션 설정 최적화 (Redis 저장)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

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
        "CONN_MAX_AGE": 60,  # 연결 재사용 (초)
        "CONN_HEALTH_CHECKS": True,  # 연결 상태 확인
        "OPTIONS": {
            "connect_timeout": 10,  # 연결 타임아웃
        },
    }
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB로 제한
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB로 제한

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
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",  # 경고 수준 이상만 로깅
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "propagate": False,
            "level": "WARNING",
        },
    },
}

# 기타 메모리 최적화 설정
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
