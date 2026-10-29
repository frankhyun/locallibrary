from datetime import date

import pytest
from django.db.models import QuerySet

from tasks.models import Priority, Task, TaskStatus


def test_create_task(alice, bob, project, client_for):
    response = client_for(alice).post(
        f"/projects/{project.id}/tasks/",
        json={"title": "  Launch  ", "assignee_id": bob.id, "priority": 3},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Launch"


def test_blank_title(alice, project, client_for):
    assert client_for(alice).post(
        f"/projects/{project.id}/tasks/", json={"title": "  "}
    ).status_code == 422


def test_urgent_task_needs_due_date(alice, project, client_for):
    assert client_for(alice).post(
        f"/projects/{project.id}/tasks/", json={"title": "Urgent", "priority": 4}
    ).status_code == 422


def test_assignee_must_be_member(alice, carol, project, client_for):
    assert client_for(alice).post(
        f"/projects/{project.id}/tasks/", json={"title": "T", "assignee_id": carol.id}
    ).status_code == 400


def test_non_member_cannot_see_tasks(carol, project, client_for):
    assert client_for(carol).get(f"/projects/{project.id}/tasks/").status_code == 404


def test_patch_changes_only_sent_fields(alice, project, client_for):
    task = project.tasks.create(title="T", description="old")
    response = client_for(alice).patch(
        f"/projects/{project.id}/tasks/{task.id}", json={"description": "new"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "T"


@pytest.mark.parametrize(
    "old,new,status_code",
    [
        (TaskStatus.TODO, TaskStatus.IN_PROGRESS, 200),
        (TaskStatus.IN_PROGRESS, TaskStatus.DONE, 200),
        (TaskStatus.TODO, TaskStatus.DONE, 409),
        (TaskStatus.DONE, TaskStatus.TODO, 409),
    ],
)
def test_status_transitions(alice, project, client_for, old, new, status_code):
    task = project.tasks.create(title="T", status=old)
    response = client_for(alice).post(
        f"/projects/{project.id}/tasks/{task.id}/status", json={"status": new}
    )
    assert response.status_code == status_code


@pytest.mark.parametrize(
    "query",
    ["status=todo", "assignee=alice", "label=bug", "due_before=2026-12-01", "search=needle"],
)
def test_task_filters(alice, project, client_for, query):
    project.tasks.create(title="Needle task", description="needle")
    response = client_for(alice).get(f"/projects/{project.id}/tasks/?{query}")
    assert response.status_code == 200
