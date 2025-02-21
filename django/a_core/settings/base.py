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


# Application definition
DEFAULT_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
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
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "storages",
    "django_cleanup.apps.CleanupConfig",
    "channels",
]

INSTALLED_APPS = DEFAULT_APPS + CUSTOM_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
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

# Allauth 설정
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_USERNAME_REQUIRED = False

# 이메일 설정 (개발환경)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")  # Gmail 주소
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")  # Gmail 앱 비밀번호

# 사이트 설정
SITE_ID = 1

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
