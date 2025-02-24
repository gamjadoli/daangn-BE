import logging

from a_apis.CRUD.userCRUD import UserCRUD
from a_apis.models.email_verification import EmailVerification
from a_user.models import User
from ninja.responses import Response

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_verification_email(email: str) -> dict:
        try:
            validate_email(email)
            # 유저의 이메일이 이미 인증되었는지 확인
            if User.objects.filter(
                email=email, is_email_verified=True, is_active=True
            ).exists():
                return Response(
                    status=400,
                    data={
                        "success": False,
                        "message": "이미 인증된 이메일입니다.",
                    },
                )

            # 기존 미인증 코드 삭제
            EmailVerification.objects.filter(email=email, is_verified=False).delete()

            # 새로운 인증 코드 생성
            verification = EmailVerification.objects.create(email=email)

            # 이메일 내용 구성
            subject = "🥕 당마클론 인증번호 안내"
            message = f"인증번호: {verification.verification_code}"
            html_message = f"""
                <html>
                    <body style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: 'Apple SD Gothic Neo', sans-serif;">
                        <h2 style="color: #FF6F0F; margin-bottom: 30px;">🥕 당마클론 이메일 인증</h2>
                        <p style="font-size: 16px;">안녕하세요! 당마클론입니다 :)</p>
                        <p style="font-size: 16px;">회원가입을 위한 인증번호는 다음과 같습니다:</p>
                        <div style="margin: 30px 0;">
                            <h3 style="color: #FF6F0F; font-size: 36px; letter-spacing: 5px; padding: 20px; background-color: #FFF8F3; border: 2px dashed #FF6F0F; border-radius: 10px; margin: 0; display: inline-block;">
                                {verification.verification_code}
                            </h3>
                        </div>
                        <p style="margin-bottom: 40px;">이 인증번호는 30분 동안 유효합니다.</p>

                        <div style="margin-top: 40px; color: #999; font-size: 12px; border-top: 1px solid #EEE; padding-top: 20px;">
                            <p style="margin: 5px 0;">본 메일은 발신전용 메일입니다.</p>
                            <p style="margin: 5px 0;">
                                <a href="#" style="color: #666; text-decoration: none; margin: 0 10px;">이용약관</a>|
                                <a href="#" style="color: #666; text-decoration: none; margin: 0 10px;">개인정보처리방침</a>
                            </p>
                            <p style="margin: 15px 0;">
                                사업자 등록번호: 123-45-67890 | 대표: 전감자<br/>
                                서울특별시 강남구 테헤란로 123 당마클론빌딩
                            </p>
                            <p style="color: #666;">&copy; 2025 당마클론 Inc. All rights reserved.</p>
                        </div>
                    </body>
                </html>
            """

            # 이메일 설정 디버깅
            logger.info(
                f"Email settings: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}"
            )
            logger.info(f"Email user: {settings.EMAIL_HOST_USER}")

            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    html_message=html_message,  # HTML 메시지 추가
                    fail_silently=False,  # 오류를 표시하도록 변경
                )
            except Exception as email_error:
                logger.error(f"Email sending error: {str(email_error)}")
                return {
                    "success": False,
                    "message": f"이메일 전송 실패: {str(email_error)}",
                }

            return {
                "success": True,
                "message": "인증번호가 이메일로 발송되었습니다. 이메일을 확인해주세요.",
            }

        except ValidationError as e:
            return Response(
                status=400,
                data={
                    "success": False,
                    "message": f"이메일 형식이 올바르지 않습니다: {str(e)}",
                },
            )
        except Exception as e:
            logger.error(f"Verification email error: {str(e)}")
            return Response(
                status=500,
                data={
                    "success": False,
                    "message": f"이메일 전송 중 오류가 발생했습니다: {str(e)}",
                },
            )

    @staticmethod
    def verify_email(email: str, code: str) -> tuple[int, dict]:
        verification = UserCRUD.email_verification(email, code)

        if verification.is_expired:
            return 400, {
                "success": False,
                "message": "인증번호가 만료되었습니다. 다시 시도해주세요.",
            }

        verification.is_verified = True
        verification.save()

        return 200, {
            "success": True,
            "message": "이메일 인증이 완료되었습니다.",
        }
