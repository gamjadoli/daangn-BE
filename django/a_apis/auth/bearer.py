from ninja.security import HttpBearer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            AccessToken(token)
            return token
        except TokenError:
            return None
