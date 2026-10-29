from django.shortcuts import get_object_or_404
from ninja import Query, Router, Status
from ninja.errors import HttpError
from ninja.pagination import paginate

from .models import Message, Room
from .schemas import ConflictOut, MessageIn, MessageOut, RoomFilter, RoomIn, RoomOut


router = Router(tags=["chat"])


@router.get("/", response=list[RoomOut], auth=None)
@paginate
def list_rooms(request, filters: Query[RoomFilter]):
    return filters.filter(Room.objects.all())


@router.post("/", response={201: RoomOut, 409: ConflictOut})
def create_room(request, payload: RoomIn):
    existing = Room.objects.filter(name=payload.name).first()
    if existing:
        return Status(
            409,
            {
                "message": "A room with that name already exists",
                "existing_id": existing.id,
            },
        )
    return Status(201, Room.objects.create(name=payload.name))


@router.get("/{room_id}", response=RoomOut, auth=None)
def get_room(request, room_id: int):
    return get_object_or_404(Room, id=room_id)


@router.get("/{room_id}/messages", response=list[MessageOut], auth=None)
@paginate
def list_messages(request, room_id: int):
    room = get_object_or_404(Room, id=room_id)
    return room.messages.select_related("user").all()


@router.put("/{room_id}", response=RoomOut)
def update_room(request, room_id: int, payload: RoomIn):
    room = get_object_or_404(Room, id=room_id)
    if Room.objects.exclude(id=room.id).filter(name=payload.name).exists():
        raise HttpError(409, "A room with that name already exists")
    room.name = payload.name
    room.save(update_fields=["name"])
    return room


@router.delete("/{room_id}", response={204: None})
def delete_room(request, room_id: int):
    get_object_or_404(Room, id=room_id).delete()


@router.post("/{room_id}/messages", response={201: MessageOut})
def post_message(request, room_id: int, payload: MessageIn):
    room = get_object_or_404(Room, id=room_id)
    message = Message.objects.create(room=room, user=request.auth, text=payload.text)
    return Status(201, message)
