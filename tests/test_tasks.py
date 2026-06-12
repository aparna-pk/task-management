import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers: dict):
    """Test creating a task for authenticated user."""
    response = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Complete tests",
            "description": "Write all task endpoint unit tests",
            "status": "todo",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Complete tests"
    assert data["description"] == "Write all task endpoint unit tests"
    assert data["status"] == "todo"
    assert "id" in data
    assert "owner_id" in data


@pytest.mark.asyncio
async def test_get_tasks(client: AsyncClient, auth_headers: dict, other_auth_headers: dict):
    """Test retrieving tasks owned by current user."""
    # Create task for User 1
    await client.post(
        "/api/v1/tasks",
        json={"title": "User 1 Task", "status": "todo"},
        headers=auth_headers,
    )

    # Create task for User 2 (other_user)
    await client.post(
        "/api/v1/tasks",
        json={"title": "User 2 Task", "status": "todo"},
        headers=other_auth_headers,
    )

    # Fetch User 1's tasks
    response = await client.get("/api/v1/tasks", headers=auth_headers)
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "User 1 Task"


@pytest.mark.asyncio
async def test_get_single_task(client: AsyncClient, auth_headers: dict):
    """Test fetching details of a task."""
    # Create task
    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Single Task", "status": "in_progress"},
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Fetch details
    response = await client.get(
        f"/api/v1/tasks/{task_id}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Single Task"
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_get_another_user_task_returns_404(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict
):
    """Test that fetching another user's task returns 404."""
    # Create task as User 1
    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "User 1 Secret Task", "status": "todo"},
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Try to fetch as User 2 (other_user)
    response = await client.get(
        f"/api/v1/tasks/{task_id}", headers=other_auth_headers
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Task not found or you do not have access to it."


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, auth_headers: dict):
    """Test updating details of a task."""
    # Create task
    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Update Me", "status": "todo"},
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Update
    response = await client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": "I am Updated", "status": "done"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "I am Updated"
    assert data["status"] == "done"


@pytest.mark.asyncio
async def test_update_another_user_task_returns_404(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict
):
    """Test that updating another user's task returns 404."""
    # Create task as User 1
    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "User 1 Secret Task", "status": "todo"},
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Try to update as User 2
    response = await client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Hack Attempt"},
        headers=other_auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Task not found or you do not have access to it."


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, auth_headers: dict):
    """Test deleting a task."""
    # Create task
    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Delete Me", "status": "todo"},
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Delete
    response = await client.delete(
        f"/api/v1/tasks/{task_id}", headers=auth_headers
    )
    assert response.status_code == 200

    # Ensure it's gone
    check_response = await client.get(
        f"/api/v1/tasks/{task_id}", headers=auth_headers
    )
    assert check_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_another_user_task_returns_404(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict
):
    """Test that deleting another user's task returns 404."""
    # Create task as User 1
    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "User 1 Secret Task", "status": "todo"},
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Try to delete as User 2
    response = await client.delete(
        f"/api/v1/tasks/{task_id}", headers=other_auth_headers
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Task not found or you do not have access to it."
