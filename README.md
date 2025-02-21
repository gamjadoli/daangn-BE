# 당마 클론 프로젝트

```
git clone 레포지토리 주소
```

- 폴더 이동
```
cd 폴더명
```

- 포이트리 가상환경 설치
```
poetry install
```

- 가상환경 실행
```
poetry shell
```

- 장고 폴더로 이동
```
cd django
```

- 장고 마이그레이션
```
poetry run python manage.py makemigrations --settings=a_core.settings.development
poetry run python manage.py migrate --settings=a_core.settings.development
```

- 프로젝트 실행
```
poetry run python manage.py runserver --settings=a_core.settings.development
```

- 브라우저에서 스웨거 실행
```
http://127.0.0.1:8000/api/docs
```

---
---

## ERD 설계

### 1. 프로젝트 개요
이 프로젝트는 Django 기반의 백엔드 API 서버로, Poetry를 사용한 의존성 관리와 Docker를 통한 컨테이너화를 구현하고 있습니다.

### 2. 주요 디렉토리 구조
```
django/
├── a_core/           # 프로젝트 코어 설정
├── a_apis/           # API 관련 로직
├── a_user/           # 사용자 관리
├── a_common/         # 공통 기능
└── templates/        # HTML 템플릿

nginx/                # Nginx 설정
```

### 3. 주요 컴포넌트 설명

#### A. 설정 관리 (a_core)
- 다중 환경 설정 (development, production, dev-aws)
- 보안 설정 및 데이터베이스 설정
- URL 라우팅

#### B. API 구현 (a_apis)
- Ninja API 프레임워크 사용
- 주요 엔드포인트:
  - 인증 (auth/)
  - 사용자 관리 (users/)
  - 상태 체크 (health/)
  - 법적 문서 (legal/)

#### C. 사용자 관리 (a_user)
- 커스텀 User 모델
- 이메일 인증 기능
- 소셜 로그인 (Google) 지원

#### D. 인프라 설정
1. Nginx 설정:

```1:74:nginx.conf
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    sendfile on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    types_hash_bucket_size 64;

    upstream web_backend {
        server web:8000;  # 컨테이너 이름을 실제 컨테이너 이름으로 수정
    }

    # 로그 설정
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log warn;

    # 서버 블록 - HTTP -> HTTPS 리디렉션
    server {
        listen 80;
        server_name api.somedomain.com;
        return 301 https://$host$request_uri;
    }

    # 서버 블록 - HTTPS 설정
    server {
        listen 443 ssl;
        server_name api.somedomain.com;

        ssl_certificate /etc/letsencrypt/live/api.somedomain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/api.somedomain.com/privkey.pem;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;
        ssl_ciphers "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256";

        # SSL 설정 추가
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        ssl_session_tickets off;
        ssl_stapling on;
        ssl_stapling_verify on;
        resolver 8.8.8.8 8.8.4.4 valid=300s;
        resolver_timeout 5s;

        location / {
            proxy_pass http://web_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static/ {
            alias /app/static/;  # 여기에 정적 파일이 있는 경로를 설정
        }

        location /media/ {
            alias /app/media/;
        }

        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
```


2. Docker 구성:

```1:43:docker-compose.yml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: django/Dockerfile
    command: gunicorn a_core.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - ./django/:/app/
      - static_volume:/app/static
      - media_volume:/app/media
    env_file:
      - ./django/.env
    networks:
      - backend-network
    environment:
      - DJANGO_SETTINGS_MODULE=a_core.settings.product

  nginx:
    image: nginx:1.21-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./django/static:/app/static
      - ./django/media:/app/media
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - web
    networks:
      - backend-network

volumes:
  static_volume:
  media_volume:

networks:
  backend-network:
    driver: bridge 
```


### 4. 주요 기능
1. 인증 시스템
   - JWT 기반 인증
   - Google OAuth 통합
   - 이메일 인증

2. 보안 기능
   - HTTPS 리다이렉션
   - CORS 설정
   - 쿠키 보안

3. 데이터베이스
   - PostgreSQL 지원
   - AWS RDS 연동 가능

4. 파일 저장
   - AWS S3 통합
   - 정적/미디어 파일 관리

### 5. 개발 도구
- Poetry 의존성 관리
- Black 코드 포맷터
- pre-commit 훅
- Docker 컨테이너화

### 6. 배포 구성
- GitHub Actions를 통한 CI/CD
- Docker Compose 기반 배포
- Nginx 리버스 프록시
- SSL/TLS 지원

이 구조는 확장 가능하고 유지보수가 용이한 현대적인 Django 백엔드 애플리케이션의 좋은 예시를 보여주고 있습니다.
