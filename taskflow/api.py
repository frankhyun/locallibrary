from ninja import NinjaAPI

from accounts.auth import JWTAuth


api = NinjaAPI(title="TaskFlow API", auth=JWTAuth(), urls_namespace="taskflow")
api.add_router("/auth", "accounts.api.router")
api.add_router("/projects", "projects.api.router")
api.add_router("/projects/{project_id}/tasks", "tasks.api.router")
