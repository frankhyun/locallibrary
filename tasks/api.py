from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import get_object_or_404
from ninja import File, Form, Path, Query, Router, Status
from ninja.errors import HttpError
from ninja.pagination import paginate
from ninja import FilterLookup, FilterSchema
from typing import Annotated, Any

from projects.api import visible_projects
from projects.models import Label
from .models import ALLOWED_TRANSITIONS, Attachment, Comment, Priority, Task
from .schemas import (
    AttachmentOut, CommentIn, CommentOut, StatusIn, TaskIn, TaskOut, TaskUpdate,
)
from ninja import PatchDict

router = Router(tags=["tasks"])


def project_for(request, project_id):
    return get_object_or_404(visible_projects(request.auth), id=project_id)


class TaskFilter(FilterSchema):
    status: str | None = None
    assignee_id: int | None = None
    search: Annotated[str | None, FilterLookup("title__icontains")] = None
    ordering: str = "created_at"
    overdue: bool | None = None


@router.get("/", response=list[TaskOut])
@paginate
def list_tasks(request, project_id: Path[int], filters: Query[TaskFilter]):
    project_for(request, project_id)
    queryset = Task.objects.filter(project_id=project_id).select_related("assignee").prefetch_related("labels")
    queryset = filters.filter(queryset)
    if filters.overdue:
        from django.utils import timezone
        queryset = queryset.filter(due_date__lt=timezone.localdate()).exclude(status="done")
    ordering = filters.ordering.lstrip("-")
    if ordering not in {"created_at", "due_date", "priority", "title"}:
        raise HttpError(400, "Invalid ordering")
    return queryset.order_by(("-" if filters.ordering.startswith("-") else "") + ordering)


@router.post("/", response={201: TaskOut})
def create_task(request, project_id: Path[int], payload: TaskIn):
    project_for(request, project_id)
    task = Task.objects.create(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date,
        assignee_id=payload.assignee_id,
    )
    task.labels.set(Label.objects.filter(project_id=project_id, id__in=payload.label_ids))
    return Status(201, task)


@router.get("/{task_id}", response=TaskOut)
def get_task(request, project_id: Path[int], task_id: int):
    project_for(request, project_id)
    return get_object_or_404(Task, id=task_id, project_id=project_id)


@router.patch("/{task_id}", response=TaskOut)
def update_task(request, project_id: Path[int], task_id: int, payload: PatchDict[TaskUpdate]):
    project_for(request, project_id)
    task = get_object_or_404(Task, id=task_id, project_id=project_id)
    for key, value in payload.items():
        if key == "assignee_id":
            task.assignee_id = value
        elif key == "label_ids":
            task.labels.set(Label.objects.filter(project_id=project_id, id__in=value))
        else:
            setattr(task, key, value)
    if task.priority == Priority.URGENT and task.due_date is None:
        raise HttpError(400, "Urgent tasks need a due date")
    task.save()
    return task


@router.post("/{task_id}/status", response=TaskOut)
def change_status(request, project_id: Path[int], task_id: int, payload: StatusIn):
    project_for(request, project_id)
    task = get_object_or_404(Task, id=task_id, project_id=project_id)
    if payload.status not in ALLOWED_TRANSITIONS[task.status]:
        raise HttpError(409, f"Can't move a task from {task.status} to {payload.status}")
    task.status = payload.status
    task.save(update_fields=["status"])
    return task


@router.get("/{task_id}/comments", response=list[CommentOut])
@paginate
def list_comments(request, project_id: Path[int], task_id: int):
    project_for(request, project_id)
    return Comment.objects.filter(task_id=task_id).select_related("author").order_by("created_at")


@router.post("/{task_id}/comments", response={201: CommentOut})
def add_comment(request, project_id: Path[int], task_id: int, payload: CommentIn):
    project_for(request, project_id)
    task = get_object_or_404(Task, id=task_id, project_id=project_id)
    return Status(201, Comment.objects.create(task=task, author=request.auth, content=payload.content))


@router.put("/{task_id}/comments/{comment_id}", response=CommentOut)
def update_comment(request, project_id: Path[int], task_id: int, comment_id: int, payload: CommentIn):
    project_for(request, project_id)
    comment = get_object_or_404(Comment, id=comment_id, task_id=task_id, author=request.auth)
    comment.content = payload.content
    comment.save(update_fields=["content"])
    return comment


@router.delete("/{task_id}/comments/{comment_id}", response={204: None})
def delete_comment(request, project_id: Path[int], task_id: int, comment_id: int):
    project_for(request, project_id)
    get_object_or_404(Comment, id=comment_id, task_id=task_id, author=request.auth).delete()
    return Status(204, None)


@router.get("/{task_id}/attachments", response=list[AttachmentOut])
def list_attachments(request, project_id: Path[int], task_id: int):
    project_for(request, project_id)
    return Attachment.objects.filter(task_id=task_id)


@router.post("/{task_id}/attachments", response={201: AttachmentOut})
def add_attachment(
    request, project_id: Path[int], task_id: int,
    file: File[Any], description: Form[str] = "",
):
    project_for(request, project_id)
    task = get_object_or_404(Task, id=task_id, project_id=project_id)
    if file.size > 10 * 1024 * 1024:
        raise HttpError(413, "File is too large")
    attachment = Attachment.objects.create(
        task=task, uploaded_by=request.auth, file=file, original_name=file.name
    )
    return Status(201, attachment)


@router.delete("/{task_id}/attachments/{attachment_id}", response={204: None})
def delete_attachment(request, project_id: Path[int], task_id: int, attachment_id: int):
    project_for(request, project_id)
    get_object_or_404(Attachment, id=attachment_id, task_id=task_id).delete()
    return Status(204, None)
