# Docker Hub의 공식 Python 이미지 사용
FROM python:3.12-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV DEBIAN_FRONTEND=noninteractive
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV POETRY_VERSION=1.6.1

# 작업 디렉토리 설정
WORKDIR /app

# 필수 패키지만 설치하고 캐시 삭제하여 이미지 크기 감소
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils libproj-dev gdal-bin python3-gdal \
    build-essential libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && pip install --no-cache-dir --upgrade pip poetry==${POETRY_VERSION} \
    && poetry config virtualenvs.create false

# 의존성 파일만 먼저 복사하여 캐싱 활용
COPY pyproject.toml poetry.lock* /app/

# 개발 의존성을 제외하고 패키지 설치
RUN poetry install --no-interaction --no-ansi --without dev \
    && pip cache purge

# 소스 코드 복사
COPY . /app/

# 정적 파일 디렉토리 생성 및 불필요한 파일 정리
RUN mkdir -p /app/static /app/media \
    # 캐시 파일 정리
    && find /app -type d -name __pycache__ -exec rm -rf {} +  2>/dev/null || true \
    && find /app -name "*.pyc" -delete \
    # 임시 파일 정리
    && rm -rf /tmp/* /var/tmp/* \
    # 불필요한 개발 파일 제거
    && rm -rf /app/.git* /app/.pytest_cache /app/.coverage*

# 8000번 포트 노출
EXPOSE 8000

# 애플리케이션 실행을 위한 기본 명령어 정의
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "a_core.asgi:application"]
