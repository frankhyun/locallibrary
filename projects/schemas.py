from ninja import ModelSchema

from .models import Label, Membership, Project


class LabelIn(ModelSchema):
    class Meta:
        model = Label
        fields = ["name", "color"]


class LabelOut(ModelSchema):
    class Meta:
        model = Label
        fields = ["id", "name", "color"]


class ProjectIn(ModelSchema):
    class Meta:
        model = Project
        fields = ["name", "description"]


class ProjectOut(ModelSchema):
    labels: list[LabelOut] = []
    task_count: int = 0
    unassigned_task_count: int = 0

    class Meta:
        model = Project
        fields = ["id", "name", "description", "created_at"]


class MemberIn(ModelSchema):
    username: str
    class Meta:
        model = Membership
        fields = ["role"]


class MemberOut(ModelSchema):
    username: str
    class Meta:
        model = Membership
        fields = ["id", "role"]

    @staticmethod
    def resolve_username(obj):
        return obj.user.username
