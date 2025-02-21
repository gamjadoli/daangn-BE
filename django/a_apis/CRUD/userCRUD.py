from a_apis.models import EmailVerification


class UserCRUD:
    @staticmethod
    def email_verification(email: str, code: str) -> EmailVerification:
        return EmailVerification.objects.get(
            email=email, verification_code=code, is_verified=False
        )
