from ninja import NinjaAPI
from ninja.security import django_auth

from chat.api import router as chat_router
from accounts.schemas import TokenOut
from accounts.tokens import create_token_pair
from profiles.api import router as profile_router


api = NinjaAPI(auth=django_auth)


@api.get("/hello", auth=None)
def hello(request, name: str = "world"):
    return {"message": f"Hello, {name}!"}


@api.get("/add", auth=None)
def add(request, a: int, b: int):
    return {"result": a + b}


api.add_router("/rooms", chat_router)
api.add_router("/me", profile_router)


@api.post("/taskflow-token", response=TokenOut)
def taskflow_token(request):
    """Trade your login session for a TaskFlow token pair."""
    return create_token_pair(request.auth.id)
