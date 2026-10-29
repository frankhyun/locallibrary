from datetime import date

from ninja import ModelSchema, PatchDict, Schema
from pydantic import Field, field_validator, model_validator
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
    title: str = ""
    description: str = ""
    assignee_id: int = 0
    label_ids: list[int] = []
    priority: Priority = Priority.MEDIUM
    due_date: date = date.min


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


class AttachmentOut(ModelSchema):
    url: str
    class Meta:
        model = Attachment
        fields = ["id", "original_name", "created_at"]

    @staticmethod
    def resolve_url(obj, context):
        request = context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url
