from a_apis.auth.bearer import AuthBearer
from a_apis.models import EmailVerification
from a_apis.schema.users import *
from a_apis.service.email import EmailService
from a_apis.service.users import UserService
from ninja import Router
from ninja.files import UploadedFile

router = Router(auth=AuthBearer())
public_router = Router()


@public_router.post("/login", response=AuthResponseSchema)
def login(request, data: LoginSchema):
    """
    로그인 API

    필수 항목: email, password

    성공: 사용자 정보와 인증 토큰 반환
    실패: 이메일/비밀번호 오류 메시지
    """
    return UserService.login_user(request, data)


@public_router.post(
    "/signup", response={200: AuthResponseSchema, 400: ErrorResponseSchema}
)
def signup(request, data: SignupSchema):
    """
    회원가입 API

    필수 항목: email, password, name, latitude, longitude

    성공: 사용자 정보와 인증 토큰 반환
    실패: 이메일 중복, 좌표 오류 등의 메시지
    """
    result = UserService.signup(data)
    if not result["success"]:
        return 400, result
    return 200, result


@router.get("/me", response=AuthResponseSchema)
def get_user(request):
    """
    내 정보 조회 API

    인증 필수: Bearer 토큰 헤더 필요

    성공: 현재 로그인한 사용자 정보 반환
    실패: 권한 오류 메시지
    """
    return UserService.get_user(request)


@public_router.post("/refresh", response=TokenResponseSchema)
def refresh_token(request, data: RefreshTokenSchema):
    """
    토큰 갱신 API

    필수 항목: refresh (리프레시 토큰)

    성공: 새로운 액세스/리프레시 토큰 반환
    실패: 토큰 만료 또는 유효하지 않은 토큰 메시지
    """
    return UserService.refresh_token(data.refresh)


@public_router.post("/email-verifications", response=ErrorResponseSchema)
def request_email_verification(request, data: EmailVerificationRequestSchema):
    """
    이메일 인증 요청 API

    필수 항목: email

    성공: 인증 메일 발송 완료 메시지
    실패: 이메일 주소 오류 메시지
    """
    return EmailService.send_verification_email(data.email)


@public_router.put(
    "/email-verifications",
    response={
        200: ErrorResponseSchema,
        400: ErrorResponseSchema,
        500: ErrorResponseSchema,
    },
)
def verify_email(request, data: EmailVerificationSchema):
    """
    이메일 인증 확인 API

    필수 항목: email, code(인증번호)

    성공: 인증 완료 메시지
    실패: 유효하지 않은 인증번호 또는 처리 오류 메시지
    """
    try:
        return EmailService.verify_email(data.email, data.code)

    except EmailVerification.DoesNotExist:
        return 500, {
            "success": False,
            "message": "유효하지 않은 인증번호입니다.",
        }
    except Exception as e:
        return 500, {
            "success": False,
            "message": f"처리 중 오류가 발생했습니다: {str(e)}",
        }


@router.delete("/withdraw", response=ErrorResponseSchema)
def withdraw(request):
    """
    회원 탈퇴 API

    인증 필수: Bearer 토큰 헤더 필요

    성공: 탈퇴 완료 메시지
    실패: 권한 오류 메시지
    """
    return UserService.withdraw_user(request)


@public_router.post("/logout", response=ErrorResponseSchema)
def logout(request, data: LogoutSchema):
    """
    로그아웃 API

    필수 항목: refresh (리프레시 토큰)

    성공: 로그아웃 완료 메시지
    실패: 유효하지 않은 토큰 메시지
    """
    return UserService.logout_user(data)


@router.put("/update-profile", response=ErrorResponseSchema)
def update_profile(
    request, data: UpdateProfileSchema, profile_image: UploadedFile = None
):
    """
    회원정보 수정 API

    인증 필수: Bearer 토큰 헤더 필요

    변경 가능 항목:
    - nickname: 닉네임 변경 (선택사항)
    - phone_number: 휴대폰 번호 변경 (선택사항)
    - profile_image: 프로필 이미지 변경 (파일 업로드, 선택사항)
    - remove_profile_image: 프로필 이미지 삭제 여부 (Boolean, 선택사항, 기본값: false)

    프로필 이미지 처리:
    1. profile_image 전송: 새 이미지로 교체
    2. remove_profile_image=true: 프로필 이미지 삭제
    3. 둘 다 전송하지 않음: 기존 이미지 유지

    두 옵션이 함께 전송된 경우 remove_profile_image가 우선 적용됩니다.

    성공: 정보 수정 완료 메시지
    실패: 유효성 검증 오류 메시지
    """
    return UserService.update_user_profile(request, data, profile_image)


@router.put("/change-password", response=ErrorResponseSchema)
def change_password(request, data: PasswordChangeSchema):
    """
    비밀번호 변경 API

    인증 필수: Bearer 토큰 헤더 필요

    필수 항목:
    - current_password: 현재 비밀번호
    - new_password: 새 비밀번호

    성공: 비밀번호 변경 완료 메시지
    실패: 현재 비밀번호 불일치 또는 기타 오류 메시지
    """
    return UserService.change_user_password(request, data)


@router.get(
    "/{user_id}/profile",
    response={200: UserProfileResponseSchema, 400: ErrorResponseSchema},
)
def get_user_profile(request, user_id: int):
    """
    특정 사용자 프로필 조회 API

    **인증 필요**: Bearer 토큰으로 인증된 사용자만 다른 사용자의 프로필을 조회할 수 있습니다.

    **응답 데이터**:
    - 기본 사용자 정보 (이메일, 닉네임 등)
    - 현재 판매 중인 상품 수
    - 받은 매너 평가 통계 (긍정/부정 개수)
    - 가장 많이 받은 매너 평가 상위 3개
    - 받은 거래후기 총 개수
    - 최근 거래후기 3개 (작성자 정보 포함)

    성공: 사용자 프로필 정보 반환
    실패: 오류 메시지
    """
    result = UserService.get_user_profile(user_id)

    if not result["success"]:
        return 400, result
    return 200, result


@router.get(
    "/{user_id}/manner-ratings/detail",
    response={200: MannerRatingsDetailResponseSchema, 400: ErrorResponseSchema},
)
def get_user_manner_ratings_detail(request, user_id: int):
    """
    특정 사용자가 받은 매너평가 상세 조회 API (긍정/부정 구분)

    **인증 필요**: Bearer 토큰으로 인증된 사용자만 다른 사용자의 매너평가를 상세 조회할 수 있습니다.

    **응답 데이터**:
    - 긍정적 매너평가: 항목별 받은 횟수와 총 개수
    - 부정적 매너평가: 항목별 받은 횟수와 총 개수

    **매너평가 항목**:
    긍정적: 시간 약속을 잘 지켜요, 응답이 빨라요, 친절하고 매너가 좋아요, 상품 상태가 설명과 일치해요, 가격 제안에 대해 긍정적이에요
    부정적: 약속시간을 안 지켜요, 응답이 느려요, 불친절해요, 상품 상태가 설명과 달라요, 가격 흥정이 너무 심해요

    성공: 매너평가 상세 정보 반환
    실패: 오류 메시지
    """
    result = UserService.get_user_manner_ratings_detail(user_id)

    if not result["success"]:
        return 400, result
    return 200, result


@router.get(
    "/{user_id}/reviews/detail",
    response={200: ReviewsDetailResponseSchema, 400: ErrorResponseSchema},
)
def get_user_reviews_detail(request, user_id: int, page: int = 1, page_size: int = 10):
    """
    특정 사용자가 받은 거래후기 상세 조회 API (페이지네이션 포함)

    **인증 필요**: Bearer 토큰으로 인증된 사용자만 다른 사용자의 거래후기를 상세 조회할 수 있습니다.

    **쿼리 파라미터**:
    - page: 페이지 번호 (기본값: 1)
    - page_size: 페이지 크기 (기본값: 10, 최대: 50)

    **응답 데이터**:
    - 받은 거래후기 목록 (최신순)
    - 후기 작성자 정보 (닉네임, 역할, 동네)
    - 거래 상품명, 거래 날짜, 후기 내용
    - 페이지네이션 정보 (총 개수, 현재 페이지, 총 페이지 수)

    성공: 거래후기 상세 정보 반환
    실패: 오류 메시지
    """
    # 페이지 크기 제한
    if page_size > 50:
        page_size = 50
    if page_size < 1:
        page_size = 10

    result = UserService.get_user_reviews_detail(user_id, page, page_size)

    if not result["success"]:
        return 400, result
    return 200, result
