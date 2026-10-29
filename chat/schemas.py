from typing import Annotated

from django.db.models import Q
from ninja import FilterLookup, FilterSchema, ModelSchema, Schema

from .models import Message, Room


class RoomIn(ModelSchema):
    class Meta:
        model = Room
        fields = ["name", "topic"]


class RoomOut(ModelSchema):
    class Meta:
        model = Room
        fields = ["id", "name", "topic", "created_at"]


class MessageIn(ModelSchema):
    class Meta:
        model = Message
        fields = ["content"]


class MessageOut(ModelSchema):
    room: RoomOut
    author: int | None = None

    class Meta:
        model = Message
        fields = ["id", "content", "created_at"]

    @staticmethod
    def resolve_author(obj):
        return obj.author_id


class RoomFilter(FilterSchema):
    search: Annotated[str | None, FilterLookup("name__icontains")] = None
    topic: Annotated[str | None, FilterLookup("topic__icontains")] = None
    recent: bool | None = None

    def filter_recent(self, value: bool) -> Q:
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=30)
        return Q(created_at__gte=cutoff) if value else Q(created_at__lt=cutoff)


class ConflictOut(Schema):
    message: str
    existing_id: int
