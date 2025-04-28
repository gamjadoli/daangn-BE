import logging

from a_apis.models import ProductCategory

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

CATEGORY_DATA = [
    # 대분류 카테고리
    {"id": 1, "name": "디지털/가전", "parent": None, "order": 10},
    {"id": 2, "name": "가구/인테리어", "parent": None, "order": 20},
    {"id": 3, "name": "의류", "parent": None, "order": 30},
    {"id": 4, "name": "도서/티켓/취미", "parent": None, "order": 40},
    {"id": 5, "name": "생활/식품", "parent": None, "order": 50},
    {"id": 6, "name": "뷰티/미용", "parent": None, "order": 60},
    {"id": 7, "name": "스포츠/레저", "parent": None, "order": 70},
    {"id": 8, "name": "유아동/출산", "parent": None, "order": 80},
    {"id": 9, "name": "반려동물용품", "parent": None, "order": 90},
    # 디지털/가전 하위 카테고리
    {"id": 101, "name": "스마트폰", "parent": 1, "order": 1},
    {"id": 102, "name": "태블릿", "parent": 1, "order": 2},
    {"id": 103, "name": "노트북", "parent": 1, "order": 3},
    {"id": 104, "name": "데스크탑", "parent": 1, "order": 4},
    {"id": 105, "name": "카메라", "parent": 1, "order": 5},
    {"id": 106, "name": "이어폰", "parent": 1, "order": 6},
    {"id": 107, "name": "헤드폰", "parent": 1, "order": 7},
    {"id": 108, "name": "게임기", "parent": 1, "order": 8},
    {"id": 109, "name": "TV", "parent": 1, "order": 9},
    {"id": 110, "name": "냉장고", "parent": 1, "order": 10},
    {"id": 111, "name": "세탁기", "parent": 1, "order": 11},
    {"id": 112, "name": "에어컨", "parent": 1, "order": 12},
    # 가구/인테리어 하위 카테고리
    {"id": 201, "name": "침대", "parent": 2, "order": 1},
    {"id": 202, "name": "소파", "parent": 2, "order": 2},
    {"id": 203, "name": "책상", "parent": 2, "order": 3},
    {"id": 204, "name": "의자", "parent": 2, "order": 4},
    {"id": 205, "name": "옷장", "parent": 2, "order": 5},
    {"id": 206, "name": "조명", "parent": 2, "order": 6},
    {"id": 207, "name": "커튼", "parent": 2, "order": 7},
    {"id": 208, "name": "러그", "parent": 2, "order": 8},
    # 의류 하위 카테고리
    {"id": 301, "name": "여성의류", "parent": 3, "order": 1},
    {"id": 302, "name": "남성의류", "parent": 3, "order": 2},
    {"id": 303, "name": "신발", "parent": 3, "order": 3},
    {"id": 304, "name": "가방", "parent": 3, "order": 4},
    {"id": 305, "name": "시계", "parent": 3, "order": 5},
    {"id": 306, "name": "주얼리", "parent": 3, "order": 6},
    {"id": 307, "name": "모자", "parent": 3, "order": 7},
    {"id": 308, "name": "양말", "parent": 3, "order": 8},
    # 도서/티켓/취미 하위 카테고리
    {"id": 401, "name": "도서", "parent": 4, "order": 1},
    {"id": 402, "name": "음반", "parent": 4, "order": 2},
    {"id": 403, "name": "공연티켓", "parent": 4, "order": 3},
    {"id": 404, "name": "영화티켓", "parent": 4, "order": 4},
    {"id": 405, "name": "상품권", "parent": 4, "order": 5},
    {"id": 406, "name": "게임", "parent": 4, "order": 6},
    {"id": 407, "name": "음악악기", "parent": 4, "order": 7},
    {"id": 408, "name": "미술용품", "parent": 4, "order": 8},
    # 생활/식품 하위 카테고리
    {"id": 501, "name": "주방용품", "parent": 5, "order": 1},
    {"id": 502, "name": "생활용품", "parent": 5, "order": 2},
    {"id": 503, "name": "식품", "parent": 5, "order": 3},
    {"id": 504, "name": "건강식품", "parent": 5, "order": 4},
    {"id": 505, "name": "커피/차", "parent": 5, "order": 5},
    # 뷰티/미용 하위 카테고리
    {"id": 601, "name": "스킨케어", "parent": 6, "order": 1},
    {"id": 602, "name": "메이크업", "parent": 6, "order": 2},
    {"id": 603, "name": "헤어케어", "parent": 6, "order": 3},
    {"id": 604, "name": "바디케어", "parent": 6, "order": 4},
    {"id": 605, "name": "향수", "parent": 6, "order": 5},
    {"id": 606, "name": "네일아트", "parent": 6, "order": 6},
    # 스포츠/레저 하위 카테고리
    {"id": 701, "name": "자전거", "parent": 7, "order": 1},
    {"id": 702, "name": "인라인스케이트", "parent": 7, "order": 2},
    {"id": 703, "name": "테니스", "parent": 7, "order": 3},
    {"id": 704, "name": "배드민턴", "parent": 7, "order": 4},
    {"id": 705, "name": "골프", "parent": 7, "order": 5},
    {"id": 706, "name": "등산", "parent": 7, "order": 6},
    {"id": 707, "name": "캠핑", "parent": 7, "order": 7},
    {"id": 708, "name": "낚시", "parent": 7, "order": 8},
    # 유아동/출산 하위 카테고리
    {"id": 801, "name": "유아의류", "parent": 8, "order": 1},
    {"id": 802, "name": "유아신발", "parent": 8, "order": 2},
    {"id": 803, "name": "장난감", "parent": 8, "order": 3},
    {"id": 804, "name": "유아식품", "parent": 8, "order": 4},
    {"id": 805, "name": "유모차", "parent": 8, "order": 5},
    {"id": 806, "name": "아기띠", "parent": 8, "order": 6},
    {"id": 807, "name": "임부복", "parent": 8, "order": 7},
    # 반려동물용품 하위 카테고리
    {"id": 901, "name": "사료", "parent": 9, "order": 1},
    {"id": 902, "name": "간식", "parent": 9, "order": 2},
    {"id": 903, "name": "용품", "parent": 9, "order": 3},
    {"id": 904, "name": "장난감", "parent": 9, "order": 4},
    {"id": 905, "name": "의류", "parent": 9, "order": 5},
    {"id": 906, "name": "집/계단", "parent": 9, "order": 6},
]


class Command(BaseCommand):
    help = "상품 카테고리 데이터를 초기화합니다."

    def handle(self, *args, **options):
        try:
            # 기존 카테고리 데이터 확인
            existing_categories = ProductCategory.objects.count()
            if existing_categories > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"이미 {existing_categories}개의 카테고리가 존재합니다. 삭제 후 재생성합니다."
                    )
                )
                ProductCategory.objects.all().delete()

            # 부모 카테고리 ID 매핑
            id_to_instance = {}

            # 첫 번째 패스: 모든 카테고리 생성 (부모 없이)
            for item in CATEGORY_DATA:
                category = ProductCategory.objects.create(
                    id=item["id"],
                    name=item["name"],
                    order=item["order"],
                )
                id_to_instance[item["id"]] = category

            # 두 번째 패스: 부모 관계 설정
            for item in CATEGORY_DATA:
                if item["parent"] is not None:
                    category = id_to_instance[item["id"]]
                    category.parent = id_to_instance[item["parent"]]
                    category.save(update_fields=["parent"])

            self.stdout.write(
                self.style.SUCCESS(
                    f"성공적으로 {len(CATEGORY_DATA)}개의 카테고리를 생성했습니다."
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"카테고리 초기화 중 오류 발생: {str(e)}")
            )
            logger.error(f"카테고리 초기화 오류: {str(e)}")
