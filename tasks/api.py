from datetime import date
from typing import Any, Annotated, Literal

from django.shortcuts import get_object_or_404
from ninja import File, Form, FilterLookup, FilterSchema, PatchDict, Path, Query, Router, Status
from ninja.errors import HttpError, ValidationError
from ninja.pagination import CursorPagination, PageNumberPagination, paginate

from projects.api import project_for
from projects.models import Label, Membership
from .models import ALLOWED_TRANSITIONS, Attachment, Comment, Priority, Task, TaskStatus
from .schemas import (
    AttachmentFile, AttachmentIn, AttachmentOut, CommentIn, CommentOut, StatusIn,
    TaskIn, TaskOut, TaskUpdate,
)

router = Router(tags=["tasks"])


class TaskFilter(FilterSchema):
    status: Annotated[list[TaskStatus] | None, FilterLookup("status__in")] = None
    assignee: Annotated[str | None, FilterLookup("assignee__username")] = None
    label: Annotated[str | None, FilterLookup("labels__name")] = None
    due_before: Annotated[date | None, FilterLookup("due_date__lt")] = None
    search: Annotated[
        str | None, FilterLookup(["title__icontains", "description__icontains"])
    ] = None


TaskOrdering = Literal[
    "created_at", "-created_at", "due_date", "-due_date", "priority", "-priority"
]


@router.get("/", response=list[TaskOut])
@paginate(PageNumberPagination, page_size=20)
def list_tasks(
    request, project_id: Path[int], filters: Query[TaskFilter],
    ordering: TaskOrdering = "created_at",
):
    project = project_for(request.auth, project_id)
    return filters.filter(
        project.tasks.select_related("assignee").prefetch_related("labels")
    ).order_by(ordering, "id")


@router.post("/", response={201: TaskOut})
def create_task(request, project_id: Path[int], payload: TaskIn):
    project = project_for(request.auth, project_id)
    if payload.assignee_id is not None and not Membership.objects.filter(
        project=project, user_id=payload.assignee_id
    ).exists():
        raise HttpError(400, "Assignee must be a project member")
    if payload.label_ids and Label.objects.filter(
        project=project, id__in=payload.label_ids
    ).count() != len(payload.label_ids):
        raise HttpError(400, "Labels must belong to this project")
    task = Task.objects.create(
        project=project,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date,
        assignee_id=payload.assignee_id,
    )
    task.labels.set(Label.objects.filter(project=project, id__in=payload.label_ids))
    return Status(201, task)


@router.get("/{task_id}", response=TaskOut)
def get_task(request, project_id: Path[int], task_id: int):
    project_for(request.auth, project_id)
    return get_object_or_404(Task, id=task_id, project_id=project_id)


@router.patch("/{task_id}", response=TaskOut)
def update_task(request, project_id: Path[int], task_id: int, payload: PatchDict[TaskUpdate]):
    project_for(request.auth, project_id)
    task = get_object_or_404(Task, id=task_id, project_id=project_id)
    for key, value in payload.items():
        if key == "assignee_id":
            if value is not None and not Membership.objects.filter(
                project_id=project_id, user_id=value
            ).exists():
                raise HttpError(400, "Assignee must be a project member")
            task.assignee_id = value
        elif key == "label_ids":
            if value is None or Label.objects.filter(
                project_id=project_id, id__in=value
            ).count() != len(value):
                raise HttpError(400, "Labels must belong to this project")
            task.labels.set(Label.objects.filter(project_id=project_id, id__in=value))
        else:
            setattr(task, key, value)
    if task.priority == Priority.URGENT and task.due_date is None:
        raise HttpError(400, "Urgent tasks need a due date")
    task.save()
    return task


@router.post("/{task_id}/status", response=TaskOut, summary="Change task status")
def change_status(request, project_id: Path[int], task_id: int, payload: StatusIn):
    """Move a task through the allowed workflow transitions."""
    project_for(request.auth, project_id)
    task = get_object_or_404(Task, id=task_id, project_id=project_id)
    if payload.status not in ALLOWED_TRANSITIONS[task.status]:
        raise HttpError(409, f"Can't move a task from {task.status} to {payload.status}")
    task.status = payload.status
    task.save(update_fields=["status"])
    return task


@router.get("/{task_id}/comments", response=list[CommentOut])
@paginate(CursorPagination, ordering=("id",), page_size=20)
def list_comments(request, project_id: Path[int], task_id: int):
    project_for(request.auth, project_id)
    return Comment.objects.filter(task_id=task_id).select_related("author")


@router.post("/{task_id}/comments", response={201: CommentOut})
def add_comment(request, project_id: Path[int], task_id: int, payload: CommentIn):
    project_for(request.auth, project_id)
    task = get_object_or_404(Task, id=task_id, project_id=project_id)
    return Status(201, Comment.objects.create(task=task, author=request.auth, body=payload.body))


@router.put("/{task_id}/comments/{comment_id}", response=CommentOut)
def update_comment(request, project_id: Path[int], task_id: int, comment_id: int, payload: CommentIn):
    project = project_for(request.auth, project_id)
    comment = get_object_or_404(Comment, id=comment_id, task_id=task_id)
    if comment.author_id != request.auth.id:
        raise HttpError(403, "Only the comment author may edit it")
    comment.body = payload.body
    comment.save(update_fields=["body"])
    return comment


@router.delete("/{task_id}/comments/{comment_id}", response={204: None})
def delete_comment(request, project_id: Path[int], task_id: int, comment_id: int):
    project = project_for(request.auth, project_id)
    comment = get_object_or_404(Comment, id=comment_id, task_id=task_id)
    if comment.author_id != request.auth.id and not project.memberships.filter(
        user=request.auth, role__in=[Membership.Role.OWNER, Membership.Role.ADMIN]
    ).exists():
        raise HttpError(403, "You do not have permission to delete this comment")
    comment.delete()
    return Status(204, None)


@router.get("/{task_id}/attachments", response=list[AttachmentOut])
def list_attachments(request, project_id: Path[int], task_id: int):
    project_for(request.auth, project_id)
    return Attachment.objects.filter(task_id=task_id)


@router.post("/{task_id}/attachments", response={201: AttachmentOut})
def add_attachment(
    request, project_id: Path[int], task_id: int,
    details: Form[AttachmentIn], file: File[Any],
):
    project_for(request.auth, project_id)
    task = get_object_or_404(Task, id=task_id, project_id=project_id)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError([{
            "type": "file_too_large",
            "loc": ["file"],
            "msg": "Files can be at most 5 MB",
            "input": file.name,
        }])
    if not file.name.lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".txt", ".md")):
        raise ValidationError([{
            "type": "file_type",
            "loc": ["file"],
            "msg": "Only PDF, PNG, JPEG and text files are allowed",
            "input": file.name,
        }])
    attachment = Attachment.objects.create(
        task=task,
        uploaded_by=request.auth,
        file=file,
        original_name=details.name or file.name,
    )
    return Status(201, attachment)


@router.delete("/{task_id}/attachments/{attachment_id}", response={204: None})
def delete_attachment(request, project_id: Path[int], task_id: int, attachment_id: int):
    project = project_for(request.auth, project_id)
    attachment = get_object_or_404(Attachment, id=attachment_id, task_id=task_id)
    allowed = attachment.uploaded_by_id == request.auth.id or project.memberships.filter(
        user=request.auth, role__in=[Membership.Role.OWNER, Membership.Role.ADMIN]
    ).exists()
    if not allowed:
        raise HttpError(403, "You do not have permission to delete this attachment")
    if attachment.file:
        attachment.file.delete(save=False)
    attachment.delete()
    return Status(204, None)
