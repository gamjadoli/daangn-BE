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


@public_router.post("/request-email-verification", response=ErrorResponseSchema)
def request_email_verification(request, data: EmailVerificationRequestSchema):
    """
    이메일 인증 요청 API

    필수 항목: email

    성공: 인증 메일 발송 완료 메시지
    실패: 이메일 주소 오류 메시지
    """
    return EmailService.send_verification_email(data.email)


@public_router.post(
    "/verify-email",
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
def update_profile(request, data: UpdateProfileSchema):
    """
    회원정보 수정 API

    인증 필수: Bearer 토큰 헤더 필요
    필수 항목: 변경할 항목(name, phone 등)

    성공: 정보 수정 완료 메시지
    실패: 유효성 검증 오류 메시지
    """
    return UserService.update_user_profile(request, data)
