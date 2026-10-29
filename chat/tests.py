from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

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
class ChatApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="api-user", password="correct-horse"
        )

    def test_quickstart_endpoints_validate_and_return_data(self):
        self.assertEqual(
            self.client.get("/api/hello?name=Ninja").json(),
            {"message": "Hello, Ninja!"},
        )
        response = self.client.get("/api/add?a=2&b=3")
        self.assertEqual(response.json(), {"result": 5})
        self.assertEqual(self.client.get("/api/add?a=2&b=bad").status_code, 422)

    def test_rooms_are_public_and_writes_require_login(self):
        self.assertEqual(self.client.get("/api/rooms/").status_code, 200)
        self.assertEqual(
            self.client.post(
                "/api/rooms/",
                data={"name": "lobby"},
                content_type="application/json",
            ).status_code,
            401,
        )
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/rooms/",
            data={"name": "lobby", "topic": "General"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        room_id = response.json()["id"]
        response = self.client.post(
            f"/api/rooms/{room_id}/messages",
            data={"content": "hello"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["content"], "hello")


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
