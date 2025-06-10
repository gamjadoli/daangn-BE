"""
더미 테스트 데이터 생성 명령어
"""

import random
from decimal import Decimal

from a_apis.models.product import Product, ProductCategory
from a_apis.models.region import (
    EupmyeondongRegion,
    SidoRegion,
    SigunguRegion,
    UserActivityRegion,
)
from a_user.models import User

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "개발/테스트용 더미 데이터를 생성합니다"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users", type=int, default=10, help="생성할 사용자 수 (기본값: 10명)"
        )
        parser.add_argument(
            "--products", type=int, default=50, help="생성할 상품 수 (기본값: 50개)"
        )
        parser.add_argument(
            "--show-stats", action="store_true", help="지역 및 사용자 통계 정보 출력"
        )

    def create_dummy_regions(self):
        """더미 지역 데이터 생성"""
        # 다양한 시도 데이터
        sido_data = [
            {"code": "11", "name": "서울특별시"},
            {"code": "26", "name": "부산광역시"},
            {"code": "27", "name": "대구광역시"},
            {"code": "28", "name": "인천광역시"},
            {"code": "29", "name": "광주광역시"},
            {"code": "30", "name": "대전광역시"},
            {"code": "31", "name": "울산광역시"},
            {"code": "41", "name": "경기도"},
            {"code": "42", "name": "강원도"},
            {"code": "43", "name": "충청북도"},
            {"code": "44", "name": "충청남도"},
            {"code": "45", "name": "전라북도"},
            {"code": "46", "name": "전라남도"},
            {"code": "47", "name": "경상북도"},
            {"code": "48", "name": "경상남도"},
            {"code": "50", "name": "제주특별자치도"},
        ]

        # 시군구 및 읍면동 샘플 데이터
        region_data = [
            # 서울특별시
            {
                "sido": "11",
                "sigungu_code": "11110",
                "sigungu_name": "종로구",
                "regions": [
                    "청운효자동",
                    "사직동",
                    "삼청동",
                    "부암동",
                    "평창동",
                    "무악동",
                    "교남동",
                    "가회동",
                    "종로1가동",
                    "종로2가동",
                ],
            },
            {
                "sido": "11",
                "sigungu_code": "11140",
                "sigungu_name": "중구",
                "regions": [
                    "소공동",
                    "회현동",
                    "명동",
                    "필동",
                    "장충동",
                    "광희동",
                    "을지로동",
                    "신당동",
                    "다산동",
                    "황학동",
                ],
            },
            {
                "sido": "11",
                "sigungu_code": "11170",
                "sigungu_name": "용산구",
                "regions": [
                    "후암동",
                    "용산2가동",
                    "남영동",
                    "청파동",
                    "원효로1동",
                    "원효로2동",
                    "효창동",
                    "용문동",
                    "한강로동",
                    "이촌1동",
                ],
            },
            {
                "sido": "11",
                "sigungu_code": "11200",
                "sigungu_name": "성동구",
                "regions": [
                    "왕십리도선동",
                    "마장동",
                    "사근동",
                    "행당1동",
                    "행당2동",
                    "응봉동",
                    "금호1가동",
                    "금호2가동",
                    "금호4가동",
                    "옥수동",
                ],
            },
            # 경기도
            {
                "sido": "41",
                "sigungu_code": "41131",
                "sigungu_name": "수원시",
                "regions": [
                    "장안구 파장동",
                    "장안구 정자1동",
                    "장안구 정자2동",
                    "장안구 정자3동",
                    "영통구 매탄1동",
                    "영통구 매탄2동",
                    "영통구 매탄3동",
                    "영통구 매탄4동",
                    "팔달구 인계동",
                    "팔달구 우만1동",
                ],
            },
            {
                "sido": "41",
                "sigungu_code": "41111",
                "sigungu_name": "성남시",
                "regions": [
                    "수정구 태평1동",
                    "수정구 태평2동",
                    "수정구 태평3동",
                    "수정구 태평4동",
                    "중원구 성남동",
                    "중원구 중앙동",
                    "중원구 금광1동",
                    "중원구 금광2동",
                    "분당구 분당동",
                    "분당구 수내1동",
                ],
            },
            # 부산광역시
            {
                "sido": "26",
                "sigungu_code": "26110",
                "sigungu_name": "중구",
                "regions": [
                    "중앙동",
                    "동광동",
                    "대청동",
                    "보수동",
                    "부평동",
                    "광복동",
                    "남포동",
                    "영주동",
                    "창선동",
                    "동인동",
                ],
            },
            {
                "sido": "26",
                "sigungu_code": "26140",
                "sigungu_name": "서구",
                "regions": [
                    "동대신1동",
                    "동대신2동",
                    "동대신3동",
                    "서대신1동",
                    "서대신2동",
                    "서대신3동",
                    "부민동",
                    "충무동",
                    "영도동",
                    "신선동",
                ],
            },
            # 인천광역시
            {
                "sido": "28",
                "sigungu_code": "28110",
                "sigungu_name": "중구",
                "regions": [
                    "운서동",
                    "중산동",
                    "덕교동",
                    "인현동",
                    "답동",
                    "신흥동",
                    "도원동",
                    "송월동",
                    "신포동",
                    "선린동",
                ],
            },
            {
                "sido": "28",
                "sigungu_code": "28140",
                "sigungu_name": "동구",
                "regions": [
                    "만석동",
                    "화수1동",
                    "화수2동",
                    "송현1동",
                    "송현2동",
                    "송현3동",
                    "금창동",
                    "금곡동",
                    "화평동",
                    "송림1동",
                ],
            },
            # 대전광역시
            {
                "sido": "30",
                "sigungu_code": "30110",
                "sigungu_name": "동구",
                "regions": [
                    "중앙동",
                    "신인동",
                    "대별동",
                    "효동",
                    "판암1동",
                    "판암2동",
                    "용운동",
                    "성남동",
                    "홍도동",
                    "삼성동",
                ],
            },
            # 제주특별자치도
            {
                "sido": "50",
                "sigungu_code": "50110",
                "sigungu_name": "제주시",
                "regions": [
                    "일도1동",
                    "일도2동",
                    "이도1동",
                    "이도2동",
                    "삼도1동",
                    "삼도2동",
                    "용담1동",
                    "용담2동",
                    "건입동",
                    "화북동",
                ],
            },
        ]

        regions_created = 0

        for region_group in region_data:
            # 시도 생성 또는 가져오기
            sido, _ = SidoRegion.objects.get_or_create(
                code=region_group["sido"],
                defaults={
                    "name": next(
                        s["name"]
                        for s in sido_data
                        if s["code"] == region_group["sido"]
                    )
                },
            )

            # 시군구 생성 또는 가져오기
            sigungu, _ = SigunguRegion.objects.get_or_create(
                code=region_group["sigungu_code"],
                sido=sido,
                defaults={"name": region_group["sigungu_name"]},
            )

            # 읍면동 생성
            for i, region_name in enumerate(region_group["regions"]):
                # 한국 전체 범위에서 랜덤 좌표 생성
                latitude = round(random.uniform(33.0, 38.6), 6)
                longitude = round(random.uniform(124.6, 131.9), 6)
                center_point = Point(longitude, latitude, srid=4326)

                region_code = f"{region_group['sigungu_code']}{i+1:03d}"

                region, created = EupmyeondongRegion.objects.get_or_create(
                    code=region_code,
                    sigungu=sigungu,
                    defaults={"name": region_name, "center_coordinates": center_point},
                )

                if created:
                    regions_created += 1

        self.stdout.write(f"  📍 {regions_created}개의 새로운 지역 생성 완료")

    def handle(self, *args, **options):
        user_count = options["users"]
        product_count = options["products"]

        self.stdout.write("🎭 더미 데이터 생성 시작...")

        # 카테고리와 지역 체크
        categories = list(ProductCategory.objects.all())
        regions = list(EupmyeondongRegion.objects.all())

        if not categories:
            self.stdout.write(
                self.style.ERROR(
                    "❌ 카테고리가 없습니다. 먼저 init_categories 명령어를 실행하세요."
                )
            )
            return

        # 지역 데이터가 부족하면 더미 지역 생성
        if len(regions) < 20:
            self.stdout.write(
                f"🗺️  지역 데이터가 부족합니다 ({len(regions)}개). 더미 지역을 생성합니다..."
            )
            self.create_dummy_regions()
            regions = list(EupmyeondongRegion.objects.all())
            self.stdout.write(f"✅ 총 {len(regions)}개 지역으로 확장 완료")

        # 더미 사용자 생성
        users_created = 0
        for i in range(user_count):
            username = f"testuser{i+1:03d}"
            email = f"test{i+1:03d}@example.com"

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "nickname": f"테스트유저{i+1:03d}",
                    "phone_number": f"010{random.randint(10000000, 99999999)}",
                    "is_email_verified": True,
                },
            )
            if created:
                users_created += 1

                # 새로 생성된 사용자에게 활동지역 인증 추가
                try:
                    # 랜덤한 지역 선택 (1-2개 지역)
                    num_regions = random.randint(1, 2)
                    selected_regions = random.sample(
                        regions, min(num_regions, len(regions))
                    )

                    for priority, region in enumerate(selected_regions, 1):
                        # 해당 지역 근처의 랜덤 좌표 생성
                        if region.center_coordinates:
                            base_lng = region.center_coordinates.x
                            base_lat = region.center_coordinates.y
                        else:
                            # 기본 좌표 (서울시청) 사용
                            base_lng = 126.9780
                            base_lat = 37.5665

                        # 지역 중심에서 ±0.01도 범위 내의 랜덤 좌표
                        user_lng = base_lng + random.uniform(-0.01, 0.01)
                        user_lat = base_lat + random.uniform(-0.01, 0.01)
                        user_location = Point(user_lng, user_lat, srid=4326)

                        UserActivityRegion.objects.create(
                            user=user,
                            activity_area=region,
                            priority=priority,
                            location=user_location,
                        )

                    self.stdout.write(
                        f"  ✓ {user.nickname}: {num_regions}개 활동지역 인증 완료"
                    )

                except Exception as e:
                    self.stdout.write(f"  ⚠️ {user.nickname} 활동지역 생성 실패: {e}")

        self.stdout.write(
            f"👤 {users_created}명의 사용자 생성 완료 (활동지역 인증 포함)"
        )

        # 기존 사용자 중 활동지역이 없는 사용자들에게 활동지역 추가
        all_users = list(User.objects.all())
        users_without_regions = []

        for user in all_users:
            if not UserActivityRegion.objects.filter(user=user).exists():
                users_without_regions.append(user)

        if users_without_regions:
            self.stdout.write(
                f"🏠 활동지역이 없는 기존 사용자 {len(users_without_regions)}명에게 활동지역 추가 중..."
            )

            for user in users_without_regions:
                try:
                    # 랜덤한 지역 선택 (1-2개 지역)
                    num_regions = random.randint(1, 2)
                    selected_regions = random.sample(
                        regions, min(num_regions, len(regions))
                    )

                    for priority, region in enumerate(selected_regions, 1):
                        # 해당 지역 근처의 랜덤 좌표 생성
                        if region.center_coordinates:
                            base_lng = region.center_coordinates.x
                            base_lat = region.center_coordinates.y
                        else:
                            # 기본 좌표 (서울시청) 사용
                            base_lng = 126.9780
                            base_lat = 37.5665

                        # 지역 중심에서 ±0.01도 범위 내의 랜덤 좌표
                        user_lng = base_lng + random.uniform(-0.01, 0.01)
                        user_lat = base_lat + random.uniform(-0.01, 0.01)
                        user_location = Point(user_lng, user_lat, srid=4326)

                        UserActivityRegion.objects.create(
                            user=user,
                            activity_area=region,
                            priority=priority,
                            location=user_location,
                        )

                    self.stdout.write(
                        f"  ✓ {user.nickname}: {num_regions}개 활동지역 인증 추가"
                    )

                except Exception as e:
                    self.stdout.write(f"  ⚠️ {user.nickname} 활동지역 추가 실패: {e}")

            self.stdout.write(f"🏠 기존 사용자 활동지역 추가 완료")

        # 더미 상품 생성
        users = list(User.objects.all())
        products_created = 0

        # 카테고리 매핑을 위한 도우미 함수
        def get_category_by_names(category_names):
            """카테고리 이름들로 카테고리 객체 찾기"""
            found_categories = []
            for name in category_names:
                category = next((c for c in categories if c.name == name), None)
                if category:
                    found_categories.append(category)
            return found_categories if found_categories else [random.choice(categories)]

        # 카테고리별 상품 제목과 카테고리 ID 직접 매핑
        product_data = [
            # 디지털/가전 (카테고리 ID 직접 지정)
            ("아이폰 15 프로 판매합니다", 101),  # 스마트폰
            ("삼성 갤럭시 S24 울트라", 101),  # 스마트폰
            ("맥북 프로 M3", 103),  # 노트북
            ("에어팟 프로 2세대", 106),  # 이어폰
            ("닌텐도 스위치 OLED", 108),  # 게임기
            ("플레이스테이션 5 슬림", 108),  # 게임기
            ("LG 그램 노트북 17인치", 103),  # 노트북
            ("아이패드 에어 5세대", 102),  # 태블릿
            ("갤럭시 탭 S9", 102),  # 태블릿
            ("애플워치 SE", 305),  # 시계
            ("소니 WH-1000XM5 헤드폰", 107),  # 헤드폰
            ("캐논 EOS R6 카메라", 105),  # 카메라
            ("삼성 4K TV 65인치", 109),  # TV
            ("다이슨 청소기 V15", 1),  # 디지털/가전 대분류
            ("에어프라이어 코스리", 501),  # 주방용품
            ("전자레인지 LG", 1),  # 디지털/가전 대분류
            # 가구/인테리어
            ("수면공감 매트리스 퀸사이즈", 201),  # 침대
            ("한샘 3인 소파", 202),  # 소파
            ("이케아 책상 세트", 203),  # 책상
            ("허먼밀러 의자", 204),  # 의자
            ("시스템 옷장 맞춤제작", 205),  # 옷장
            ("필립스 LED 조명", 206),  # 조명
            ("암막커튼 맞춤제작", 207),  # 커튼
            ("러그 200x300", 208),  # 러그
            ("원목 식탁 4인용", 203),  # 책상
            ("북유럽 스타일 침대", 201),  # 침대
            ("철제 선반", 2),  # 가구/인테리어 대분류
            ("화장대 LED 조명포함", 2),  # 가구/인테리어 대분류
            # 의류/패션
            ("노스페이스 패딩 점퍼", 302),  # 남성의류
            ("나이키 에어맥스 운동화", 303),  # 신발
            ("아디다스 후디", 302),  # 남성의류
            ("유니클로 하이테크 다운", 301),  # 여성의류
            ("구찌 백팩", 304),  # 가방
            ("샤넬 숄더백", 304),  # 가방
            ("롤렉스 서브마리너 시계", 305),  # 시계
            ("티파니 목걸이", 306),  # 주얼리
            ("레이밴 선글라스", 3),  # 의류 대분류
            ("컨버스 척테일러", 303),  # 신발
            ("뉴발란스 990", 303),  # 신발
            ("루이비통 지갑", 304),  # 가방
            # 도서/취미
            ("해리포터 전집", 401),  # 도서
            ("경영학 전공서적", 401),  # 도서
            ("TOEIC 교재세트", 401),  # 도서
            ("기타 야마하 클래식", 407),  # 음악악기
            ("키보드 롤랜드 디지털피아노", 407),  # 음악악기
            ("아크릴 물감세트", 408),  # 미술용품
            ("캔버스 화판", 408),  # 미술용품
            ("보드게임 카탄", 406),  # 게임
            ("레고 테크닉 세트", 406),  # 게임
            ("스타벅스 상품권 5만원", 405),  # 상품권
            ("CGV 영화표 2매", 404),  # 영화티켓
            # 생활/식품
            ("식칼 세트 독일제", 501),  # 주방용품
            ("냄비세트 스테인리스", 501),  # 주방용품
            ("그릇세트 도자기", 501),  # 주방용품
            ("다이어트 식품 세트", 503),  # 식품
            ("프로틴 파우더", 504),  # 건강식품
            ("비타민 멀티팩", 504),  # 건강식품
            ("원두커피 1kg", 505),  # 커피/차
            ("허브티 세트", 505),  # 커피/차
            ("오가닉 쌀 10kg", 503),  # 식품
            ("참기름 들기름 세트", 503),  # 식품
            ("견과류 선물세트", 503),  # 식품
            ("과일 선물세트", 503),  # 식품
            # 뷰티/미용
            ("SK-II 페이셜 트리트먼트", 601),  # 스킨케어
            ("에스티로더 세럼", 601),  # 스킨케어
            ("랑콤 파운데이션", 602),  # 메이크업
            ("헤라 쿠션팩트", 602),  # 메이크업
            ("설화수 윤조에센스", 601),  # 스킨케어
            ("이니스프리 세트", 601),  # 스킨케어
            ("다이슨 헤어드라이어", 603),  # 헤어케어
            ("고데기 세트", 603),  # 헤어케어
            ("향수 샤넬 No.5", 605),  # 향수
            ("디올 립스틱", 602),  # 메이크업
            ("맥 아이섀도우 팔레트", 602),  # 메이크업
            ("젤네일 키트", 606),  # 네일아트
            # 스포츠/레저
            ("트렉 자전거 로드바이크", 701),  # 자전거
            ("인라인 롤러브레이드", 702),  # 인라인스케이트
            ("테니스 라켓 윌슨", 703),  # 테니스
            ("배드민턴 라켓 요넥스", 704),  # 배드민턴
            ("골프 드라이버 타이틀리스트", 705),  # 골프
            ("등산화 살로몬", 706),  # 등산
            ("캠핑 텐트 4인용", 707),  # 캠핑
            ("낚시대 시마노", 708),  # 낚시
            ("요가매트 라이프핏", 7),  # 스포츠/레저 대분류
            ("덤벨 세트 20kg", 7),  # 스포츠/레저 대분류
            ("풀업바", 7),  # 스포츠/레저 대분류
            ("런닝머신 가정용", 7),  # 스포츠/레저 대분류
            # 유아동/출산
            ("유아 원피스 90사이즈", 801),  # 유아의류
            ("아동 운동화 180", 802),  # 유아신발
            ("레고 클래식 세트", 803),  # 장난감
            ("분유 앱솔루트 1단계", 804),  # 유아식품
            ("기저귀 팸퍼스 신생아", 8),  # 유아동/출산 대분류
            ("젖병 세트 필립스", 8),  # 유아동/출산 대분류
            ("유모차 페그페레고", 805),  # 유모차
            ("아기띠 에르고베이비", 806),  # 아기띠
            ("임부복 세트", 807),  # 임부복
            ("이유식 용기 세트", 804),  # 유아식품
            ("아기 장난감 피셔프라이스", 803),  # 장난감
            ("유아 침대", 801),  # 유아의류
            # 반려동물용품
            ("고양이 사료 로얄캐닌", 901),  # 사료
            ("강아지 간식 세트", 902),  # 간식
            ("펫 캐리어 이비야히", 903),  # 용품
            ("고양이 화장실 자동", 903),  # 용품
            ("강아지 목줄 세트", 903),  # 용품
            ("펫 하우스 대형", 903),  # 용품
            ("고양이 타워", 903),  # 용품
            ("강아지 장난감 로프", 904),  # 장난감
            ("펫 계단 3단", 906),  # 집/계단
            ("자동급식기", 903),  # 용품
            ("펫 미용가위", 903),  # 용품
            ("반려동물 이동장", 903),  # 용품
        ]

        for i in range(product_count):
            try:
                # 랜덤하게 상품 데이터 선택
                title, category_id = random.choice(product_data)

                # 카테고리 ID로 카테고리 객체 찾기
                selected_category = next(
                    (c for c in categories if c.id == category_id),
                    random.choice(categories),
                )

                # 랜덤한 사용자 선택
                selected_user = random.choice(users)

                # 선택된 사용자의 활동지역 중에서 하나 선택
                user_regions = UserActivityRegion.objects.filter(user=selected_user)
                if user_regions.exists():
                    # 사용자의 활동지역 중에서 랜덤 선택
                    selected_user_region = random.choice(user_regions)
                    product_region = selected_user_region.activity_area

                    # 선택된 지역 주변의 좌표 사용
                    if product_region.center_coordinates:
                        base_lng = product_region.center_coordinates.x
                        base_lat = product_region.center_coordinates.y
                        # 지역 중심에서 ±0.02도 범위 내의 랜덤 좌표 (약 2km 반경)
                        longitude = round(base_lng + random.uniform(-0.02, 0.02), 6)
                        latitude = round(base_lat + random.uniform(-0.02, 0.02), 6)
                    else:
                        # 대한민국 전체 지역 좌표 범위 (제주도 포함)
                        latitude = round(random.uniform(33.0, 38.6), 6)
                        longitude = round(random.uniform(124.6, 131.9), 6)
                else:
                    # 활동지역이 없는 사용자의 경우 랜덤 지역 선택 (백업)
                    product_region = random.choice(regions)
                    latitude = round(random.uniform(33.0, 38.6), 6)
                    longitude = round(random.uniform(124.6, 131.9), 6)

                product = Product.objects.create(
                    user=selected_user,
                    title=title + f" #{i+1}",
                    trade_type=random.choice(["sale", "share"]),
                    price=(
                        random.randint(10000, 1000000)
                        if random.choice([True, False])
                        else None
                    ),
                    accept_price_offer=random.choice([True, False]),
                    description=f"테스트용 상품 설명입니다. 상품명: {title}, 상품 번호: {i+1}",
                    category=selected_category,
                    region=product_region,
                    meeting_location=Point(longitude, latitude, srid=4326),
                    location_description=f"테스트 만남 장소 {i+1}",
                    status=random.choice(["new", "reserved", "soldout"]),
                    refresh_at=timezone.now(),
                )
                products_created += 1

                # 진행 상황 출력 (10개마다)
                if (i + 1) % 10 == 0:
                    region_info = (
                        f"{product_region.sigungu.sido.name} {product_region.sigungu.name} {product_region.name}"
                        if hasattr(product_region, "sigungu")
                        else product_region.name
                    )
                    self.stdout.write(
                        f"📦 {i + 1}개 상품 생성 중... (최신: {title} -> {selected_category.name}, 사용자: {selected_user.nickname}, 지역: {region_info})"
                    )

            except Exception as e:
                self.stdout.write(f"⚠️  상품 생성 실패: {e}")

        self.stdout.write(f"📦 {products_created}개의 상품 생성 완료")
        self.stdout.write(self.style.SUCCESS("🎉 더미 데이터 생성 완료!"))

        # 통계 정보 출력
        if options.get("show_stats", False):
            self.show_statistics()

    def show_statistics(self):
        """생성된 더미 데이터 통계 정보 출력"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 더미 데이터 통계 정보")
        self.stdout.write("=" * 60)

        # 지역 통계
        total_sidos = SidoRegion.objects.count()
        total_sigungus = SigunguRegion.objects.count()
        total_regions = EupmyeondongRegion.objects.count()

        self.stdout.write(f"🗺️  지역 데이터:")
        self.stdout.write(f"   시도: {total_sidos}개")
        self.stdout.write(f"   시군구: {total_sigungus}개")
        self.stdout.write(f"   읍면동: {total_regions}개")

        # 시도별 지역 분포
        sido_stats = {}
        for region in EupmyeondongRegion.objects.select_related("sigungu__sido"):
            sido_name = region.sigungu.sido.name
            sido_stats[sido_name] = sido_stats.get(sido_name, 0) + 1

        self.stdout.write(f"\n📍 시도별 지역 분포:")
        for sido, count in sorted(sido_stats.items()):
            self.stdout.write(f"   {sido}: {count}개")

        # 사용자 및 활동지역 통계
        total_users = User.objects.count()
        users_with_regions = (
            User.objects.filter(activity_regions__isnull=False).distinct().count()
        )
        total_activity_regions = UserActivityRegion.objects.count()

        self.stdout.write(f"\n👥 사용자 통계:")
        self.stdout.write(f"   총 사용자: {total_users}명")
        self.stdout.write(f"   활동지역 인증 완료: {users_with_regions}명")
        self.stdout.write(f"   총 활동지역: {total_activity_regions}개")

        # 활동지역 다양성
        used_regions = set()
        for ar in UserActivityRegion.objects.select_related(
            "activity_area__sigungu__sido"
        ):
            region_info = f"{ar.activity_area.sigungu.sido.name} {ar.activity_area.sigungu.name} {ar.activity_area.name}"
            used_regions.add(region_info)

        diversity_rate = (
            len(used_regions) / total_regions * 100 if total_regions > 0 else 0
        )
        self.stdout.write(
            f"   지역 다양성: {len(used_regions)}/{total_regions} ({diversity_rate:.1f}%)"
        )

        # 활동지역 샘플
        self.stdout.write(f"\n🏠 활동지역 샘플:")
        sample_regions = list(used_regions)[:8]
        for i, region in enumerate(sample_regions, 1):
            self.stdout.write(f"   {i}. {region}")

        # 상품 통계
        total_products = Product.objects.count()
        self.stdout.write(f"\n📦 상품 통계:")
        self.stdout.write(f"   총 상품: {total_products}개")

        # 상품-지역 일치율 검증
        if total_products > 0:
            matched_products = 0
            total_checked = 0

            # 샘플링으로 상품-지역 일치율 확인 (최대 100개까지)
            sample_products = Product.objects.select_related("user", "region").order_by(
                "?"
            )[: min(100, total_products)]

            for product in sample_products:
                total_checked += 1
                # 사용자의 활동지역 중에 상품 등록 지역이 포함되는지 확인
                user_regions = UserActivityRegion.objects.filter(
                    user=product.user, activity_area=product.region
                ).exists()

                if user_regions:
                    matched_products += 1

            match_rate = (
                (matched_products / total_checked * 100) if total_checked > 0 else 0
            )
            self.stdout.write(
                f"   상품-지역 일치율: {matched_products}/{total_checked} ({match_rate:.1f}%)"
            )
            self.stdout.write(f"   검증 방법: 사용자 활동지역과 상품 등록지역 매칭")

        self.stdout.write("=" * 60)
