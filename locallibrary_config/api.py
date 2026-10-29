from ninja import NinjaAPI
from ninja.security import django_auth

from chat.api import router as chat_router


api = NinjaAPI(auth=django_auth)


@api.get("/hello", auth=None)
def hello(request, name: str = "world"):
    return {"message": f"Hello, {name}!"}


@api.get("/add", auth=None)
def add(request, a: int, b: int):
    return {"result": a + b}


api.add_router("/rooms", chat_router)
