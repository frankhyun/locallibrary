import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Message, Room


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.room = await self.get_or_create_room(self.room_name)

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        saved = await self.save_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "message": saved},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"message": event["message"]}))

    @database_sync_to_async
    def get_or_create_room(self, name):
        room, _ = Room.objects.get_or_create(name=name)
        return room

    @database_sync_to_async
    def save_message(self, text):
        message = Message.objects.create(
            room=self.room,
            user=self.scope.get("user") if self.scope.get("user", None) and self.scope["user"].is_authenticated else None,
            text=text,
        )
        return message.text
