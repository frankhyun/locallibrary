from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from ninja import Router, Status
from ninja.errors import HttpError

from .models import Membership, Project
from .schemas import LabelIn, LabelOut, MemberIn, MemberOut, ProjectIn, ProjectOut

router = Router(tags=["projects"])


def visible_projects(user):
    return Project.objects.filter(memberships__user=user).distinct()


@router.get("/", response=list[ProjectOut])
def list_projects(request):
    return visible_projects(request.auth).prefetch_related("labels").annotate(
        task_count=Count("tasks", distinct=True),
        unassigned_task_count=Count("tasks", filter=Q(tasks__assignee__isnull=True), distinct=True),
    ).order_by("id")


@router.post("/", response={201: ProjectOut})
def create_project(request, payload: ProjectIn):
    project = Project.objects.create(name=payload.name, description=payload.description)
    Membership.objects.create(project=project, user=request.auth, role=Membership.Role.OWNER)
    return Status(201, project)


@router.get("/{project_id}", response=ProjectOut)
def get_project(request, project_id: int):
    return get_object_or_404(visible_projects(request.auth), id=project_id)


@router.put("/{project_id}", response=ProjectOut)
def update_project(request, project_id: int, payload: ProjectIn):
    project = get_object_or_404(visible_projects(request.auth), id=project_id)
    project.name, project.description = payload.name, payload.description
    project.save(update_fields=["name", "description"])
    return project


@router.delete("/{project_id}", response={204: None})
def delete_project(request, project_id: int):
    get_object_or_404(visible_projects(request.auth), id=project_id).delete()
    return Status(204, None)


@router.post("/{project_id}/labels", response={201: LabelOut})
def create_label(request, project_id: int, payload: LabelIn):
    project = get_object_or_404(visible_projects(request.auth), id=project_id)
    return Status(201, project.labels.create(name=payload.name, color=payload.color))


@router.get("/{project_id}/members", response=list[MemberOut])
def list_members(request, project_id: int):
    project = get_object_or_404(visible_projects(request.auth), id=project_id)
    return project.memberships.select_related("user").all()


@router.post("/{project_id}/members", response={201: MemberOut})
def add_member(request, project_id: int, payload: MemberIn):
    project = get_object_or_404(visible_projects(request.auth), id=project_id)
    from django.contrib.auth.models import User
    user = get_object_or_404(User, username=payload.username)
    membership, created = Membership.objects.get_or_create(
        project=project, user=user, defaults={"role": payload.role}
    )
    if not created:
        raise HttpError(409, "User is already a member")
    return Status(201, membership)
