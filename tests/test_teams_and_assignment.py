import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_task_with_assignee(client: AsyncClient, auth_headers: dict):
    """Test creating a task with an assignee."""
    # Register a second user
    user2_data = {
        "email": "user2@example.com",
        "password": "strongpassword123",
        "full_name": "User Two",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=user2_data)
    assert reg_resp.status_code == 201
    user2_id = reg_resp.json()["id"]

    # Create task assigned to User Two
    resp = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Assigned Task",
            "description": "Task assigned to User Two",
            "assignee_id": user2_id,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Assigned Task"
    assert data["assignee_id"] == user2_id


@pytest.mark.asyncio
async def test_create_task_invalid_assignee(client: AsyncClient, auth_headers: dict):
    """Test creating a task with a non-existent assignee returns 404."""
    resp = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Invalid Assignee Task",
            "assignee_id": 9999,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert resp.json()["message"] == "Assignee user not found."


@pytest.mark.asyncio
async def test_task_authorization_flow(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict
):
    """Test full authorization flow for task owner, assignee, and third-party."""
    # Register a third user (User 3)
    user3_data = {
        "email": "user3@example.com",
        "password": "strongpassword123",
        "full_name": "User Three",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=user3_data)
    assert reg_resp.status_code == 201
    user3_id = reg_resp.json()["id"]

    # Log in User 3 to get their auth headers
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user3_data["email"], "password": user3_data["password"]},
    )
    user3_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # User 1 (auth_headers) creates a task assigned to User 2 (other_auth_headers)
    user2_profile_resp = await client.get("/api/v1/auth/me", headers=other_auth_headers)
    user2_id = user2_profile_resp.json()["id"]

    create_resp = await client.post(
        "/api/v1/tasks",
        json={"title": "Shared Task", "assignee_id": user2_id},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    # 1. Assignee (User 2) can view details of the task
    get_resp = await client.get(f"/api/v1/tasks/{task_id}", headers=other_auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Shared Task"

    # 2. Assignee (User 2) can update the task
    update_resp = await client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Updated Shared Task"},
        headers=other_auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated Shared Task"

    # 3. Third-party (User 3) cannot view the task
    third_get_resp = await client.get(f"/api/v1/tasks/{task_id}", headers=user3_headers)
    assert third_get_resp.status_code == 404

    # 4. Third-party (User 3) cannot update the task
    third_update_resp = await client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Hack Attempt"},
        headers=user3_headers,
    )
    assert third_update_resp.status_code == 404

    # 5. Assignee (User 2) cannot delete the task (forbidden)
    delete_resp = await client.delete(
        f"/api/v1/tasks/{task_id}", headers=other_auth_headers
    )
    assert delete_resp.status_code == 403
    assert delete_resp.json()["message"] == "Only the task owner can delete this task."

    # 6. Owner (User 1) can delete the task
    owner_delete_resp = await client.delete(
        f"/api/v1/tasks/{task_id}", headers=auth_headers
    )
    assert owner_delete_resp.status_code == 200


@pytest.mark.asyncio
async def test_get_assigned_tasks(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict
):
    """Test fetching tasks assigned to the current user."""
    # Get User 2 ID
    user2_profile = await client.get("/api/v1/auth/me", headers=other_auth_headers)
    user2_id = user2_profile.json()["id"]

    # User 1 creates two tasks: one assigned to User 2, one not assigned
    await client.post(
        "/api/v1/tasks",
        json={"title": "Task Assigned to User 2", "assignee_id": user2_id},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/tasks",
        json={"title": "Task Owned by User 1 only"},
        headers=auth_headers,
    )

    # Fetch User 2's assigned tasks
    assigned_resp = await client.get(
        "/api/v1/tasks/assigned", headers=other_auth_headers
    )
    assert assigned_resp.status_code == 200
    assigned_tasks = assigned_resp.json()
    assert len(assigned_tasks) == 1
    assert assigned_tasks[0]["title"] == "Task Assigned to User 2"


@pytest.mark.asyncio
async def test_teams_crud_and_membership(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict
):
    """Test team lifecycle management and access controls."""
    # 1. Create a Team
    create_resp = await client.post(
        "/api/v1/teams",
        json={"name": "Engineering Team", "description": "Devs group"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    team_id = create_resp.json()["id"]
    assert create_resp.json()["name"] == "Engineering Team"
    # Owner should be in the members list
    assert len(create_resp.json()["members"]) == 1
    assert create_resp.json()["members"][0]["role"] == "owner"

    # Get User 2 ID
    user2_profile = await client.get("/api/v1/auth/me", headers=other_auth_headers)
    user2_id = user2_profile.json()["id"]

    # 2. Add User 2 to Team
    add_resp = await client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"user_id": user2_id, "role": "member"},
        headers=auth_headers,
    )
    assert add_resp.status_code == 201
    assert add_resp.json()["user_id"] == user2_id
    assert add_resp.json()["role"] == "member"

    # 3. Retrieve Team (as member User 2)
    view_resp = await client.get(f"/api/v1/teams/{team_id}", headers=other_auth_headers)
    assert view_resp.status_code == 200
    assert view_resp.json()["name"] == "Engineering Team"

    # 4. Modify member role (to admin)
    update_role_resp = await client.put(
        f"/api/v1/teams/{team_id}/members/{user2_id}?role=admin",
        headers=auth_headers,
    )
    assert update_role_resp.status_code == 200
    assert update_role_resp.json()["role"] == "admin"

    # 5. Non-member cannot view the team
    # Register User 3
    user3_data = {
        "email": "user3_team@example.com",
        "password": "strongpassword123",
        "full_name": "User Three",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=user3_data)
    assert reg_resp.status_code == 201
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user3_data["email"], "password": user3_data["password"]},
    )
    user3_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    view_non_member_resp = await client.get(
        f"/api/v1/teams/{team_id}", headers=user3_headers
    )
    assert view_non_member_resp.status_code == 403

    # 6. Remove member
    remove_resp = await client.delete(
        f"/api/v1/teams/{team_id}/members/{user2_id}",
        headers=auth_headers,
    )
    assert remove_resp.status_code == 204
