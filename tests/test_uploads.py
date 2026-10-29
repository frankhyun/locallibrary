from django.core.files.uploadedfile import SimpleUploadedFile


def test_upload_uses_display_name(alice, project, client_for):
    task = project.tasks.create(title="T")
    response = client_for(alice).post(
        f"/projects/{project.id}/tasks/{task.id}/attachments",
        FILES={"file": SimpleUploadedFile("notes.txt", b"notes")},
        data={"name": "Meeting notes"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Meeting notes"


def test_upload_rejects_file_type(alice, project, client_for):
    task = project.tasks.create(title="T")
    response = client_for(alice).post(
        f"/projects/{project.id}/tasks/{task.id}/attachments",
        FILES={"file": SimpleUploadedFile("setup.exe", b"bad")},
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "file_type"


def test_upload_rejects_large_file(alice, project, client_for):
    task = project.tasks.create(title="T")
    response = client_for(alice).post(
        f"/projects/{project.id}/tasks/{task.id}/attachments",
        FILES={"file": SimpleUploadedFile("large.txt", b"x" * (5 * 1024 * 1024 + 1))},
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "file_too_large"
