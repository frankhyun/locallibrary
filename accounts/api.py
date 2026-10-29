from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from ninja import Router, Status
from ninja.errors import HttpError

from .schemas import RefreshIn, SignupIn, TokenIn, TokenOut, UserOut
from .tokens import create_token_pair, decode_token

router = Router(tags=["auth"], auth=None)


@router.post("/signup", response={201: UserOut})
def signup(request, payload: SignupIn):
    if User.objects.filter(username=payload.username).exists():
        raise HttpError(409, "Username is already taken")
    try:
        validate_password(payload.password)
    except ValidationError as error:
        raise HttpError(400, error.messages) from error
    return Status(201, User.objects.create_user(payload.username, password=payload.password))


@router.post("/token", response=TokenOut)
def token(request, payload: TokenIn):
    user = authenticate(username=payload.username, password=payload.password)
    if not user:
        raise HttpError(401, "Invalid credentials")
    return create_token_pair(user.id)


@router.post("/refresh", response=TokenOut)
def refresh(request, payload: RefreshIn):
    claims = decode_token(payload.refresh, "refresh")
    if not claims:
        raise HttpError(401, "Invalid refresh token")
    return create_token_pair(int(claims["sub"]))
