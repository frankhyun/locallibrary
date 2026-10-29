from django.contrib.auth.models import User
from ninja import ModelSchema, Schema


class UserOut(ModelSchema):
    display_name: str
    class Meta:
        model = User
        fields = ["id", "username"]

    @staticmethod
    def resolve_display_name(user):
        return user.get_full_name() or user.username


class SignupIn(Schema):
    username: str
    password: str


class TokenIn(Schema):
    username: str
    password: str


class RefreshIn(Schema):
    refresh: str


class TokenOut(Schema):
    access: str
    refresh: str
