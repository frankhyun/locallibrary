from django.contrib.auth.models import User
from ninja.security import HttpBearer

from .tokens import decode_token


class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        claims = decode_token(token, "access")
        return User.objects.filter(id=claims["sub"], is_active=True).first() if claims else None
