from ninja import NinjaAPI

from accounts.auth import JWTAuth


api = NinjaAPI(
    title="TaskFlow API",
    version="1.0",
    description="Track the tasks of your team's projects, members, labels, comments and attachments.",
    auth=JWTAuth(),
    urls_namespace="taskflow",
)


@api.get("/health", auth=None, include_in_schema=False)
def health(request):
    return {"status": "ok"}


api.add_router("/auth", "accounts.api.router")
api.add_router("/projects", "projects.api.router")
api.add_router("/projects/{project_id}/tasks", "tasks.api.router")
