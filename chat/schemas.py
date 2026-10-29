from datetime import datetime
from typing import Annotated

from django.db.models import Q
from ninja import FilterLookup, FilterSchema, ModelSchema, Schema

from .models import Message, Room


class RoomIn(ModelSchema):
    class Meta:
        model = Room
        fields = ["name"]


class RoomOut(ModelSchema):
    class Meta:
        model = Room
        fields = ["id", "name", "created_at"]


class MessageIn(ModelSchema):
    class Meta:
        model = Message
        fields = ["text"]


class MessageOut(ModelSchema):
    author: str | None = None

    class Meta:
        model = Message
        fields = ["id", "text", "created_at", "user"]
        fields_optional = ["user"]

    @staticmethod
    def resolve_author(obj):
        return obj.user.get_username() if obj.user else None


class RoomFilter(FilterSchema):
    search: Annotated[str | None, FilterLookup("name__icontains")] = None
    recent: bool | None = None

    def filter_recent(self, value: bool) -> Q:
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=30)
        return Q(created_at__gte=cutoff) if value else Q(created_at__lt=cutoff)


class ConflictOut(Schema):
    message: str
    existing_id: int
