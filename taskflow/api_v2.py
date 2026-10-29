from ninja import NinjaAPI

from accounts.auth import JWTAuth
from projects.api import router as projects_router
from tasks.api import router as tasks_router


api_v2 = NinjaAPI(
    title="TaskFlow API v2",
    version="2.0",
    auth=JWTAuth(),
    urls_namespace="taskflow-v2",
)
api_v2.add_router("/projects", projects_router)
api_v2.add_router("/projects/{project_id}/tasks", tasks_router)
