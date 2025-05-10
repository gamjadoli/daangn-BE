# 🥕 당마(DangMa) - 위치 기반 중고거래 플랫폼

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.1.6-green)
![Django Ninja](https://img.shields.io/badge/Django_Ninja-1.0-orange)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Nginx](https://img.shields.io/badge/Nginx-1.21-brightgreen)
![CI/CD](https://img.shields.io/badge/CI/CD-GitHub_Actions-blue)
![SSL](https://img.shields.io/badge/SSL-Let's_Encrypt-brightgreen)

## 📋 프로젝트 개요

**당마**는 사용자의 지리적 위치를 기반으로 근처 이웃과 중고 물품을 거래할 수 있는 플랫폼입니다. Django와 PostGIS를 활용한 위치 기반 서비스와 WebSocket을 통한 실시간 채팅 기능을 핵심으로 하는 백엔드 API 서버를 개발했습니다.

- **개발 기간**: 2025.04 ~  (개발중)
- **역할**: 백엔드 개발자 (Django 백엔드 API 서버 설계 및 구현)
- **GitHub**: https://github.com/Jeedoli

## 🛠️ 기술 스택

### 백엔드

- **언어 & 프레임워크**: Python 3.12, Django 5.1.6, Django Ninja
- **비동기 처리**: Django Channels, ASGI(Daphne)
- **인증**: JWT 기반 인증 시스템
- **보안**: Let's Encrypt SSL 인증서, HTTPS 적용

### 데이터베이스

- **메인 DB**: PostgreSQL + PostGIS(위치 데이터)
- **캐싱 & 메시징**: Redis

### 인프라

- **컨테이너화**: Docker, Docker Compose
- **웹 서버**: Nginx
- **CI/CD**: GitHub Actions
- **배포 환경**: AWS
- **보안**: Let's Encrypt 자동 갱신, Certbot

## 💡 핵심 기능

### 1. 위치 기반 서비스

- 사용자 위치 인증 및 활동 지역 설정
- 반경 기반 근처 상품 검색 (PostGIS 활용)
- 행정구역(시도, 시군구, 읍면동) 기반 지역 필터링

### 2. 실시간 채팅 시스템

- WebSocket을 활용한 실시간 1:1 채팅
- 채팅방 및 메시지 관리
- 읽음 상태 추적 및 오프라인 메시지 처리

### 3. 상품 관리 시스템

- 상품 등록, 수정, 삭제, 조회 API
- 카테고리별 분류 및 검색
- 관심 상품 등록 및 관리

### 4. 거래 프로세스 관리

- 거래 약속 설정 및 관리
- 가격 제안 및 협상 기능
- 거래 완료 및 평가(매너온도) 시스템

## 🔍 기술적 도전 및 해결책

### 위치 데이터 처리 최적화

- **도전**: 대량의 위치 데이터를 효율적으로 처리하고 신속한 검색 결과 제공
- **해결책**:
    - PostGIS 공간 인덱스를 통한 위치 검색 쿼리 최적화
    - 행정구역 경계를 MultiPolygon 형태로 저장하여 효율적인 위치 계산
    - Redis 캐싱으로 자주 요청되는 지역 정보의 응답 시간 단축
    
    ```python
    # 위치 기반 상품 검색 최적화 예시
    user_location = Point(lng, lat, srid=4326)
    products = Product.objects.filter(
        status="on_sale",
        location__distance_lte=(user_location, D(m=radius))
    ).annotate(
        distance=Distance("location", user_location)
    ).select_related("user").prefetch_related("images")
    
    ```

### 실시간 채팅 구현

- **도전**: 확장 가능하고 신뢰성 있는 실시간 메시징 시스템 구축
- **해결책**:
    - Django Channels와 Redis 채널 레이어를 활용한 WebSocket 구현
    - 데이터베이스에 메시지 영구 저장 및 읽음 상태 추적 메커니즘 개발
    - 채팅방 참여 권한 관리 및 메시지 보안 처리
    
    ```python
    # WebSocket Consumer 핵심 구현
    class ChatConsumer(AsyncWebsocketConsumer):
        async def connect(self):
            # 사용자 인증 및 권한 확인
            # 채팅방 그룹 참여
    
        async def receive(self, text_data):
            # 메시지 처리 및 저장
            # 그룹 브로드캐스트
    
    ```

### Django Ninja를 활용한 API 설계

- **도전**: 타입 안전하고 문서화가 잘된 API 시스템 구축
- **해결책**:
    - Django Ninja를 도입하여 FastAPI 스타일의 타입 힌팅 적용
    - Pydantic 기반 스키마로 요청/응답 데이터 검증 자동화
    - OpenAPI 자동 문서화로 프론트엔드 개발과의 협업 효율화
    
    ```python
    # Django Ninja API 정의 예시
    from ninja import Router, Schema
    
    router = Router()
    
    class ProductSchema(Schema):
        title: str
        price: int
        description: str
    
    @router.post("/products", response={201: ProductSchema})
    def create_product(request, data: ProductSchema):
        product = Product.objects.create(**data.dict())
        return 201, product
    ```

### CI/CD 파이프라인 자동화

- **도전**: 안정적인 배포 환경과 데이터베이스 마이그레이션 자동화
- **해결책**:
    - GitHub Actions를 활용하여 develop→main 브랜치 병합 시 자동 배포
    - Docker Compose에 마이그레이션 및 정적 파일 수집 자동화 통합
    - 배포 과정 로깅 및 오류 알림 시스템 구현

### SSL 인증서 자동화 및 보안 강화

- **도전**: 안전한 HTTPS 연결 제공 및 인증서 관리 자동화
- **해결책**:
    - Let's Encrypt와 Certbot을 활용한 무료 SSL 인증서 발급 및 자동 갱신
    - Nginx 설정에 SSL 암호화 및 보안 헤더 적용
    - HTTP/2 프로토콜 지원으로 성능 최적화
    
    ```nginx
    # Nginx SSL 설정 예시
    server {
        listen 443 ssl http2;
        server_name dangma.store;
        
        ssl_certificate /etc/letsencrypt/live/dangma.store/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/dangma.store/privkey.pem;
        
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
        
        # 보안 헤더 설정
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options nosniff;
    }
    ```

## 📊 시스템 아키텍처

```mermaid
flowchart TD
    %% 주요 구성요소 정의
    Client([클라이언트 앱])
    Nginx{Nginx}
    ASGI[Django ASGI]
    WSGI[Django WSGI]
    Django{{Django 애플리케이션}}
    DB[(PostgreSQL + PostGIS)]
    Redis[(Redis)]
    External([외부 API])
    
    %% 주요 모듈 정의
    Core([a_core])
    Apis([a_apis])
    User([a_user])
    Common([a_common])
    
    %% 연결 관계
    Client -->|HTTPS/WSS| Nginx
    Nginx -->|WS| ASGI
    Nginx -->|HTTP| WSGI
    ASGI --> Django
    WSGI --> Django
    
    Django --> Core & Apis & User & Common
    Django <-->|READ/WRITE| DB
    Django <-->|캐싱/메시징| Redis
    Django <-->|API 연동| External
    
    %% 스타일링 - 더 높은 대비의 색상으로 조정
    classDef client fill:#e6f7ff,stroke:#0066cc,stroke-width:2px,color:#000000
    classDef server fill:#ccefdc,stroke:#006633,stroke-width:2px,color:#000000
    classDef app fill:#fff2cc,stroke:#996600,stroke-width:2px,color:#000000
    classDef module fill:#e6e6ff,stroke:#000066,stroke-width:2px,color:#000000
    classDef database fill:#f9d9ff,stroke:#660066,stroke-width:2px,color:#000000
    classDef external fill:#ffe6e6,stroke:#990000,stroke-width:2px,color:#000000
    
    class Client client
    class Nginx,ASGI,WSGI server
    class Django app
    class Core,Apis,User,Common module
    class DB,Redis database
    class External external
```

### 주요 컴포넌트

- **Django API 서버**: Django Ninja를 통한 API 및 비즈니스 로직 처리
- **Channels**: WebSocket 연결 관리 및 실시간 메시징
- **PostgreSQL & PostGIS**: 관계형 데이터 및 위치 데이터 저장
- **Redis**: 캐싱, 세션 관리, 채널 레이어
- **Nginx**: 리버스 프록시, SSL 종료, 정적 파일 서빙
- **Certbot**: SSL 인증서 발급 및 자동 갱신

## 📝 프로젝트 구조

```
당마(DangMa)/
├── django/
│   ├── a_core/          # 프로젝트 설정 및 코어
│   ├── a_apis/          # API 엔드포인트 및 비즈니스 로직
│   │   ├── api/         # API 라우팅 및 엔드포인트
│   │   │   ├── api.py   # API 진입점
│   │   │   ├── chat.py  # 채팅 API
│   │   │   ├── products.py # 상품 API
│   │   │   ├── region.py # 지역 API
│   │   │   └── users.py # 사용자 API
│   │   ├── auth/        # 인증 관련 모듈
│   │   ├── models/      # 데이터 모델
│   │   │   ├── chat.py  # 채팅 모델
│   │   │   ├── product.py # 상품 모델
│   │   │   ├── region.py # 지역 모델
│   │   │   └── trade.py # 거래 모델
│   │   ├── schema/      # Django Ninja 스키마
│   │   │   ├── chat.py  # 채팅 스키마
│   │   │   ├── products.py # 상품 스키마
│   │   │   ├── region.py # 지역 스키마
│   │   │   └── users.py # 사용자 스키마
│   │   ├── service/     # 비즈니스 로직 서비스
│   │   ├── consumers.py # WebSocket 소비자
│   │   └── routing.py   # WebSocket 라우팅
│   ├── a_user/          # 사용자 관련 기능
│   └── a_common/        # 공통 모듈 및 유틸리티
├── nginx/               
│   ├── nginx.conf       # Nginx 메인 설정
│   └── ssl/             # SSL 인증서 관련 설정
└── docker-compose.yml   # 컨테이너 구성
```

## 🔧 테스트 및 품질 관리

- **단위 테스트**: 핵심 기능별 테스트 케이스 작성 (위치 검색, 채팅, 인증)
- **통합 테스트**: API 엔드포인트 및 WebSocket 연결 테스트
- **외부 API 모킹**: SGIS API 연동 테스트를 위한 모킹 구현
- **코드 품질 관리**: Black, flake8을 통한 코드 스타일 일관성 유지

## 🚀 로컬 개발 환경 설정

### 사전 요구사항
- Python 3.12 이상
- Poetry
- Docker & Docker Compose

### 설치 및 실행

1. 레포지토리 클론
```bash
git clone https://github.com/yourusername/dangma.git
cd dangma
```

2. Poetry로 의존성 설치
```bash
poetry install
poetry shell
```

3. Django 설정
```bash
cd django
poetry run python manage.py makemigrations --settings=a_core.settings.development
poetry run python manage.py migrate --settings=a_core.settings.development
```

4. 개발 서버 실행
```bash
poetry run python manage.py runserver --settings=a_core.settings.development
```

5. API 문서 접속
```
https://api.dangma.store/api/docs#/
```

### Docker를 통한 실행
```bash
docker-compose up -d
```

### SSL 개발 환경 설정 (선택사항)
```bash
# 로컬 개발용 자체 서명 인증서 생성
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ./nginx/ssl/local-cert.key -out ./nginx/ssl/local-cert.crt

# 또는 mkcert 사용 (권장)
mkcert -install
mkcert -key-file ./nginx/ssl/local-cert.key -cert-file ./nginx/ssl/local-cert.crt localhost 127.0.0.1
```

## 📚 성과 및 배운 점

### 성과

- Django와 Django Ninja를 활용한 타입 안전한 API 서버 구축
- PostGIS를 활용한 효율적인 위치 기반 검색 시스템 개발
- WebSocket을 통한 실시간 양방향 통신 구현
- Docker 기반 개발/배포 환경 및 CI/CD 파이프라인 구축

### 배운 점

- **API 설계 패턴**: Django Ninja와 스키마 기반 API 설계로 코드 견고성 향상
- **비동기 프로그래밍**: Channels와 ASGI를 통한 비동기 통신 패턴 습득
- **공간 데이터 처리**: GIS 개념과 공간 쿼리 최적화 기법 습득
- **컨테이너 오케스트레이션**: Docker Compose를 통한 멀티 컨테이너 관리 경험

### 향후 개선 계획

- Elasticsearch 도입을 통한 검색 기능 고도화
- 푸시 알림 시스템 구현 (FCM, WebPush)
- 성능 모니터링 도구 도입 (Prometheus, Grafana)
- 마이크로서비스 아키텍처로의 점진적 전환

## 🔗 추가 자료

- **API 문서**: [https://api.dangma.store/api/docs#](https://api.dangma.store/api/docs#/)
- **GitHub**: https://github.com/Jeedoli

## 👨‍💻 연락처

- **개발자**: 이재훈
- **이메일**: ljhx6787@naver.com
- **GitHub**: https://github.com/Jeedoli
---

© 2025 당마(DangMa) 프로젝트
