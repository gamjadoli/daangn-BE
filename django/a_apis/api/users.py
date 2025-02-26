from a_apis.auth.bearer import AuthBearer
from a_apis.models import EmailVerification
from a_apis.schema.users import *

# from a_apis.service.common_parser import CommonParser
from a_apis.service.email import EmailService
from a_apis.service.users import UserService
from ninja import Router

router = Router(auth=AuthBearer())
public_router = Router()


@public_router.post("/login", response=AuthResponseSchema)
def login(request, data: LoginSchema):
    """
    로그인 엔드포인트

        Args:
            request: HTTP 요청 객체
            data: 로그인 데이터 (LoginSchema)

        Returns:
            AuthResponseSchema: 로그인 결과 및 토큰 정보
    """
    return UserService.login_user(request, data)


@public_router.post("/signup", response=AuthResponseSchema)
def signup(request, data: SignupSchema):
    """
    회원가입 엔드포인트

    Args:
        request: HTTP 요청 객체
        data: 회원가입 데이터 (SignupSchema)

    Returns:
        AuthResponseSchema: 회원가입 결과 및 토큰 정보
    """
    return UserService.signup(data)


@router.get("/me", response=AuthResponseSchema)
def get_user(request):
    """
    사용자 정보 조회 엔드포인트

    Args:
        request: HTTP 요청 객체

    Returns:
        AuthResponseSchema: 사용자 정보 및 토큰 정보
    """
    return UserService.get_user(request)


@public_router.post("/refresh", response=TokenResponseSchema)
def refresh_token(request, data: RefreshTokenSchema):
    """
    토큰 갱신 엔드포인트

    Args:
        request: HTTP 요청 객체
        data: 토큰 데이터 (RefreshTokenSchema)

    Returns:
        TokenResponseSchema: 토큰 정보
    """
    return UserService.refresh_token(data.refresh)


@public_router.post("/request-email-verification", response=ErrorResponseSchema)
def request_email_verification(request, data: EmailVerificationRequestSchema):
    """
    이메일 인증 요청 엔드포인트

    Args:
        request: HTTP 요청 객체
        data: 이메일 인증 요청 데이터 (EmailVerificationRequestSchema)

    Returns:
        dict: 이메일 인증 요청 결과
    """
    return EmailService.send_verification_email(data.email)


@public_router.post(
    "/verify-email",
    response={
        200: ErrorResponseSchema,
        400: ErrorResponseSchema,
        500: ErrorResponseSchema,
    },
    # parser=CommonParser(),
)
def verify_email(request, data: EmailVerificationSchema):
    """
    이메일 인증번호 확인 엔드포인트

    Args:
        request: HTTP 요청 객체
        data: 이메일과 인증번호 데이터

    Returns:
        dict: 이메일 인증 확인 결과
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
    회원 탈퇴 엔드포인트
    """
    return UserService.withdraw_user(request)


@public_router.post("/logout", response=ErrorResponseSchema)
def logout(request, data: LogoutSchema):
    """
    로그아웃 엔드포인트 (리프래쉬토큰만 받아서 블랙리스트에 추가)
    args:
        data: 로그아웃 데이터 (LogoutSchema)
    returns:
        dict: 로그아웃 결과
    """
    return UserService.logout_user(data)


@router.put("/update-profile", response=ErrorResponseSchema)
def update_profile(request, data: UpdateProfileSchema):
    """
    회원 정보 수정 엔드포인트

    Args:
        request: HTTP 요청 객체
        data: 회원 정보 수정 데이터 (UpdateProfileSchema)

    Returns:
        dict: 회원 정보 수정 결과
    """
    return UserService.update_user_profile(request, data)
