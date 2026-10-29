def test_create_project(alice, client_for):
    response = client_for(alice).post("/projects/", json={"name": "New", "description": "x"})
    assert response.status_code == 201
    assert response.json()["name"] == "New"


def test_list_only_my_projects(alice, carol, project, client_for):
    assert len(client_for(alice).get("/projects/").json()) == 1
    assert client_for(carol).get("/projects/").json() == []


def test_non_member_gets_404(carol, project, client_for):
    assert client_for(carol).get(f"/projects/{project.id}").status_code == 404


def test_member_cannot_delete(bob, project, client_for):
    assert client_for(bob).delete(f"/projects/{project.id}").status_code == 403


def test_owner_can_update(alice, project, client_for):
    response = client_for(alice).put(
        f"/projects/{project.id}", json={"name": "Updated", "description": "x"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"
