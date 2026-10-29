from django.contrib.auth.models import User
from ninja import ModelSchema, Schema

from .models import Profile


class ProfileOut(ModelSchema):
    class Meta:
        model = Profile
        fields = ["display_name", "bio"]


class MeOut(ModelSchema):
    profile: ProfileOut

    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ProfileIn(Schema):
    display_name: str
    bio: str = ""
