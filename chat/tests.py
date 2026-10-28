from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from .routing import websocket_urlpatterns


IN_MEMORY_CHANNEL_LAYER = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
}
test_application = URLRouter(websocket_urlpatterns)


class ChatViewTests(TestCase):
    def test_chat_index_is_available(self):
        response = self.client.get(reverse("chat-index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What chat room would you like to enter?")

    def test_room_page_contains_room_name(self):
        response = self.client.get(reverse("chat-room", args=["lobby"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "lobby")


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost"],
    CHANNEL_LAYERS=IN_MEMORY_CHANNEL_LAYER,
)
class ChatConsumerTests(TransactionTestCase):
    async def test_messages_are_broadcast_to_the_same_room(self):
        first = WebsocketCommunicator(test_application, "/ws/chat/lobby/")
        second = WebsocketCommunicator(test_application, "/ws/chat/lobby/")
        first_connected, _ = await first.connect()
        second_connected, _ = await second.connect()
        self.assertTrue(first_connected)
        self.assertTrue(second_connected)

        await first.send_json_to({"message": "hello"})

        self.assertEqual(await first.receive_json_from(), {"message": "hello"})
        self.assertEqual(await second.receive_json_from(), {"message": "hello"})
        await first.disconnect()
        await second.disconnect()

    async def test_messages_are_not_sent_to_other_rooms(self):
        first = WebsocketCommunicator(test_application, "/ws/chat/room_one/")
        second = WebsocketCommunicator(test_application, "/ws/chat/room_two/")
        first_connected, _ = await first.connect()
        second_connected, _ = await second.connect()
        self.assertTrue(first_connected)
        self.assertTrue(second_connected)

        await first.send_json_to({"message": "hello"})
        self.assertEqual(await first.receive_json_from(), {"message": "hello"})

        await second.send_json_to({"message": "world"})
        self.assertEqual(await second.receive_json_from(), {"message": "world"})
        await first.disconnect()
        await second.disconnect()
