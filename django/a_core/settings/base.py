import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env_path = os.path.join(BASE_DIR, ".env")

# .env 파일이 없으면 생성
if not os.path.exists(env_path):
    with open(".env", "w") as env_file:
        env_file.write("AWS_RDS_NAME=\n")
        env_file.write("AWS_RDS_USER=\n")
        env_file.write("AWS_RDS_PASSWORD=\n")
        env_file.write("AWS_RDS_HOST=\n")
        env_file.write("AWS_RDS_PORT=\n")
        env_file.write("\n")
        env_file.write("DJANGO_SECRET_KEY= somekey\n")
        env_file.write("DJANGO_SETTINGS_MODULE=a_core.settings.development\n")
        env_file.write("\n")
        env_file.write("AUTH_GOOGLE_CLIENT_ID=\n")
        env_file.write("AUTH_GOOGLE_CLIENT_SECRET=\n")
        env_file.write("\n")
        env_file.write("AUTH_KAKAO_CLIENT_ID=\n")
        env_file.write("AUTH_KAKAO_CLIENT_SECRET=\n")
        env_file.write("\n")
        env_file.write("AUTH_NAVER_CLIENT_ID=\n")
        env_file.write("AUTH_NAVER_CLIENT_SECRET=\n")
        env_file.write("\n")
        env_file.write("SERVER_BASE_URL=https://myapp.com\n")
        env_file.write("SERVER_BASE_URL_DEV=http://127.0.0.1:3000\n")

# .env 파일 로드
load_dotenv()

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

AUTH_GOOGLE_CLIENT_ID = os.getenv("AUTH_GOOGLE_CLIENT_ID")
AUTH_GOOGLE_CLIENT_SECRET = os.getenv("AUTH_GOOGLE_CLIENT_SECRET")
AUTH_KAKAO_CLIENT_ID = os.getenv("AUTH_KAKAO_CLIENT_ID")
AUTH_KAKAO_CLIENT_SECRET = os.getenv("AUTH_KAKAO_CLIENT_SECRET")
AUTH_NAVER_CLIENT_ID = os.getenv("AUTH_NAVER_CLIENT_ID")
AUTH_NAVER_CLIENT_SECRET = os.getenv("AUTH_NAVER_CLIENT_SECRET")

# SGIS API 설정
SGIS_API_KEY = os.environ.get("SGIS_API_KEY", "")
SGIS_SECRET_KEY = os.environ.get("SGIS_SECRET_KEY", "")


# Application definition
DEFAULT_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
]

# staticfiles 앱을 DEFAULT_APPS에서 제거하고 나중에 추가
STATIC_APPS = [
    "django.contrib.staticfiles",
]

CUSTOM_APPS = [
    "a_user.apps.AUserConfig",
    "a_common.apps.ACommonConfig",
    "a_apis.apps.AApisConfig",
]

THIRD_PARTY_APPS = [
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "storages",
    "django_cleanup.apps.CleanupConfig",
    "channels",
    "daphne",
]

# daphne를 staticfiles 앱보다 먼저 등록하도록 변경
INSTALLED_APPS = DEFAULT_APPS + THIRD_PARTY_APPS + STATIC_APPS + CUSTOM_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # allauth 미들웨어 추가
    "a_apis.middleware.ProcessPUTPatchMiddleware",  # PUT, PATCH 요청 처리 미들웨어
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}


ROOT_URLCONF = "a_core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "a_core.wsgi.application"

# ASGI 적용
ASGI_APPLICATION = "a_core.asgi.application"

# Channel Layer 설정 (Redis 사용)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],  # docker-compose에서 지정한 redis 서비스명
        },
    },
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "ko-kr"  # 한국어로 변경
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_L10N = True  # 로케일의 형식을 사용
USE_TZ = False  # False로 설정하여 DB에 UTC 시간대를 사용하지 않음


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# 디렉토리가 없으면 자동으로 생성
for directory in [STATIC_ROOT, MEDIA_ROOT] + STATICFILES_DIRS:
    os.makedirs(directory, exist_ok=True)

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 사용자 모델 설정
AUTH_USER_MODEL = "a_user.User"

# Allauth 설정 업데이트
ACCOUNT_LOGIN_METHODS = {"email"}  # ACCOUNT_AUTHENTICATION_METHOD 대체

ACCOUNT_RATE_LIMITS = {
    # 로그인 시도 제한 설정
    "login_failed": {
        "TIMER": 300,  # 5분 (300초)
        "LIMIT": 5,  # 5회 시도
    }
}

# 기존 deprecated 설정들 제거
# ACCOUNT_AUTHENTICATION_METHOD = "email"
# ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
# ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300

# 나머지 allauth 설정 유지
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 0.0208333  # 30분

# 이메일 설정 수정
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")  # 발신자 이메일 주소
EMAIL_HOST_PASSWORD = os.getenv(
    "EMAIL_HOST_PASSWORD"
)  # 발신자 이메일 앱 비밀번호 16자리

# SSL 인증서 설정
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()

# 이전 SSL 관련 설정 제거
# EMAIL_USE_SSL = False
# EMAIL_SSL_CERTFILE = None
# EMAIL_SSL_KEYFILE = None
# ssl._create_default_https_context = ssl._create_unverified_context

# 사이트 설정
SITE_ID = 1  # 주석 해제

# JWT 설정
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
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

SERVER_BASE_URL = os.getenv("SERVER_BASE_URL", "")
SERVER_BASE_URL_DEV = os.getenv("SERVER_BASE_URL_DEV", "")

LOGIN_REDIRECT_URL = os.getenv("LOGIN_REDIRECT_URL", "")
LOGIN_REDIRECT_URL_DEV = os.getenv("LOGIN_REDIRECT_URL_DEV", "")
ACCOUNT_LOGOUT_ON_GET = True

# 쿠키 설정
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
