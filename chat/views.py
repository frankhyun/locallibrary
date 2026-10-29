from django.shortcuts import render

from .models import Room

def index(request):
    return render(request, "chat/index.html")


def room(request, room_name):
    room, _ = Room.objects.get_or_create(name=room_name)
    return render(
        request,
        "chat/room.html",
        {"room_name": room_name, "room_messages": room.messages.all()},
    )
