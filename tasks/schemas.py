from datetime import date
from pathlib import Path
from typing import Annotated

from django.core.files.uploadedfile import UploadedFile
from ninja import ModelSchema, PatchDict, Schema
from pydantic import AfterValidator, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from accounts.schemas import UserOut
from projects.schemas import LabelOut
from .models import Attachment, Comment, Priority, Task, TaskStatus


class TaskIn(Schema):
    title: str
    description: str = ""
    assignee_id: int | None = Field(None, description="ID of a project member to assign")
    label_ids: list[int] = []
    priority: Priority = Priority.MEDIUM
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        value = value.strip()
        if not value:
            raise PydanticCustomError("blank", "Title cannot be blank")
        return value

    @model_validator(mode="after")
    def urgent_needs_due_date(self):
        if self.priority == Priority.URGENT and self.due_date is None:
            raise ValueError("Urgent tasks need a due date")
        return self


class TaskUpdate(Schema):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    label_ids: list[int] | None = None
    priority: Priority | None = None
    due_date: date | None = None

    @field_validator("title", "description", "priority", mode="before")
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise PydanticCustomError("not_null", "This field can't be null")
        return value

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        value = value.strip()
        if not value:
            raise PydanticCustomError("blank", "Title can't be blank")
        return value


class TaskOut(ModelSchema):
    assignee: UserOut | None = None
    labels: list[LabelOut] = []

    class Meta:
        model = Task
        fields = ["id", "project", "title", "description", "status", "priority", "due_date", "created_at"]


class StatusIn(Schema):
    status: TaskStatus


class CommentIn(Schema):
    body: str


class CommentOut(ModelSchema):
    author: UserOut
    class Meta:
        model = Comment
        fields = ["id", "body", "created_at"]


MAX_UPLOAD_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".md"}


def check_upload(file: UploadedFile) -> UploadedFile:
    if file.size > MAX_UPLOAD_SIZE:
        raise PydanticCustomError("file_too_large", "Files can be at most 5 MB")
    if Path(file.name).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise PydanticCustomError(
            "file_type", "Only PDF, PNG, JPEG and text files are allowed"
        )
    return file


AttachmentFile = Annotated[UploadedFile, AfterValidator(check_upload)]


class AttachmentIn(Schema):
    name: str = Field("", max_length=200)


class AttachmentOut(ModelSchema):
    name: str
    url: str

    class Meta:
        model = Attachment
        fields = ["id", "created_at"]

    @staticmethod
    def resolve_name(obj):
        return obj.original_name

    @staticmethod
    def resolve_url(obj, context):
        request = context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url
