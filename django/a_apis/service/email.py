from a_apis.CRUD.userCRUD import UserCRUD
from a_apis.models.email_verification import EmailVerification
from a_user.models import User
from ninja.responses import Response

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email


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
            subject = "이메일 인증번호 안내"
            message = f"""
                안녕하세요.
                
                회원가입을 위한 인증번호는 다음과 같습니다:
                
                인증번호: {verification.verification_code}
                
                이 인증번호는 30분 동안 유효합니다.
            """
            html_message = f"""
                <html>
                    <body>
                        <h2>이메일 인증번호 안내</h2>
                        <p>안녕하세요.</p>
                        <p>회원가입을 위한 인증번호는 다음과 같습니다:</p>
                        <h3 style="color: #4A90E2; font-size: 24px; letter-spacing: 3px;">
                            {verification.verification_code}
                        </h3>
                        <p>이 인증번호는 30분 동안 유효합니다.</p>
                    </body>
                </html>
            """

            # 이메일 전송
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=True,
            )

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
