from ninja import NinjaAPI, Router

from accounts.auth import JWTAuth
from accounts import api as v1
from accounts.schemas import OAuthRefreshIn, OAuthTokenOut, RefreshIn, TokenIn
from accounts.tokens import ACCESS_TOKEN_LIFETIME
from projects.api import router as projects_router
from tasks.api import router as tasks_router


auth_v2 = Router(tags=["auth"], auth=None)


@auth_v2.post("/token", response=OAuthTokenOut)
def token(request, payload: TokenIn):
    pair = v1.token(request, payload)
    return {
        "access_token": pair["access"],
        "refresh_token": pair["refresh"],
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_LIFETIME,
    }


@auth_v2.post("/refresh", response=OAuthTokenOut)
def refresh(request, payload: OAuthRefreshIn):
    pair = v1.refresh(request, RefreshIn(refresh=payload.refresh_token))
    return {
        "access_token": pair["access"],
        "refresh_token": pair["refresh"],
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_LIFETIME,
    }


api_v2 = NinjaAPI(
    title="TaskFlow API v2",
    version="2.0",
    auth=JWTAuth(),
    urls_namespace="taskflow-v2",
)
api_v2.add_router("/auth", auth_v2)
api_v2.add_router("/projects", projects_router)
api_v2.add_router("/projects/{project_id}/tasks", tasks_router)
