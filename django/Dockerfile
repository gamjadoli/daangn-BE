# Docker Hub의 공식 Python 이미지 사용
FROM python:3.12-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# GDAL 관련 패키지와 PostgreSQL 개발 패키지 설치
RUN apt-get update && apt-get install -y \
    binutils libproj-dev gdal-bin python3-gdal \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치 및 설정
RUN pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false

# 의존성 설치 (수정된 경로)
COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-interaction --no-ansi

# 소스 코드 복사
COPY . /app/

# 정적 파일 디렉토리 생성
RUN mkdir -p /app/static /app/media

# 8000번 포트 노출
EXPOSE 8000

# 애플리케이션 실행을 위한 기본 명령어 정의
CMD ["gunicorn", "a_core.wsgi:application", "--bind", "0.0.0.0:8000"]
