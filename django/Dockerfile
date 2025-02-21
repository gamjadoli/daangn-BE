# Docker Hub의 공식 Python 이미지 사용
FROM python:3.12-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install --upgrade pip
RUN pip install poetry

# pyproject.toml과 poetry.lock 파일 복사
COPY pyproject.toml poetry.lock /app/

# Poetry가 가상환경을 생성하지 않도록 설정
RUN poetry config virtualenvs.create false

# Python 의존성 설치
RUN poetry install --no-interaction --no-ansi

# Django 프로젝트 복사
COPY django/ /app/

# Django 설정을 위한 환경 변수 설정
ENV DJANGO_SETTINGS_MODULE=a_core.settings.product

# 정적 파일을 위한 디렉토리 생성
RUN mkdir -p /app/static

# 마이그레이션 실행 및 정적 파일 수집
RUN python manage.py makemigrations --noinput --settings=a_core.settings.product && \
    python manage.py migrate --noinput --settings=a_core.settings.product && \
    python manage.py collectstatic --noinput --settings=a_core.settings.product

# 8000번 포트 노출
EXPOSE 8000

# 애플리케이션 실행을 위한 기본 명령어 정의
CMD ["gunicorn", "a_core.wsgi:application", "--bind", "0.0.0.0:8000"]