# Task Management & Team Collaboration API

A modern, production-ready backend API for task management and team collaboration built with **FastAPI**, **SQLAlchemy 2.0 (Async)**, and **PostgreSQL**. The project features user authentication, team organization, task ownership/assignments, and a role-based permission system.

---

## 🚀 Key Features

*   **User Management & Security**: 
    *   Secure user registration and login.
    *   JWT-based authentication (`Bearer` token) with password hashing using `bcrypt`.
*   **Team Collaboration**:
    *   Create teams and manage members.
    *   Assign team roles: `owner`, `admin`, and `member`.
    *   Granular permissions (e.g., only owners can update team-wide roles, only owners/admins can invite members).
*   **Task Management**:
    *   Create, view, update, and delete tasks.
    *   Assign tasks to users.
    *   Filtering tasks by `status`, `priority`, exact `due_date`, or due date ranges (`due_before`, `due_after`).
    *   Sorting by creation date (`latest`, `oldest`) and task priority (`HIGH` -> `MEDIUM` -> `LOW`).
*   **Strict Access Control & Authorization**:
    *   **Tasks**: A user can access/update tasks if they are the **owner** or the **assignee**.
    *   **Task Deletion**: Only the task **owner** can delete a task.
    *   **Teams**: Users can only interact with teams they are members of.
*   **Robust Testing**:
    *   Fully functional in-memory SQLite (`aiosqlite`) test database.
    *   Integration test suites covering security edge cases, filters, and role-based permissions.

---

## 🛠️ Technology Stack

*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous operations)
*   **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Using standard `Mapped[...]` types)
*   **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
*   **Database**: PostgreSQL (Production/Dev), SQLite (Testing)
*   **Security**: PyJWT (JSON Web Tokens), Passlib (Bcrypt hashing)
*   **Validation**: Pydantic v2

---

## 📂 Project Structure

```text
task-management/
├── alembic/                # Database migration scripts
├── app/
│   ├── api/
│   │   ├── v1/             # Versioned API routes (auth, tasks, teams)
│   │   │   ├── api.py      # Router registry
│   │   │   ├── auth.py     # Login, registration, profile
│   │   │   ├── tasks.py    # Task endpoints
│   │   │   └── teams.py    # Team and member endpoints
│   │   └── deps.py         # Shared dependencies (Auth/DB Session injection)
│   ├── core/               # Configuration, security, exceptions, and logger setup
│   ├── models/             # SQLAlchemy ORM models (user, task, team)
│   ├── repositories/       # Generic BaseRepository and entity queries
│   ├── schemas/            # Pydantic schemas for data validation
│   ├── services/           # Service layer encapsulating business logic
│   └── main.py             # FastAPI App initialization & middleware configuration
├── tests/                  # Pytest async unit and integration tests
├── requirements.txt        # Python dependency manifest
├── run.py                  # Entrypoint to run the development server
└── alembic.ini             # Alembic configuration
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Set Up Virtual Environment
Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables Setup
Create a `.env` file in the root directory (refer to `.env.example`):
```env
PROJECT_NAME="Task Management API"
API_V1_STR="/api/v1"
SECRET_KEY="your-super-secret-key-change-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# PostgreSQL Configuration
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=task_db

LOG_LEVEL=INFO
```

### 5. Running Database Migrations
Apply the existing database schema to your database instance:
```bash
alembic upgrade head
```

---

## 🏃 Running the Application

Start the local Uvicorn development server:
```bash
python run.py
```
By default, the server runs on `http://127.0.0.1:8000`.

### API Documentation
FastAPI automatically generates interactive documentation for developers:
*   **Swagger UI**: `http://127.0.0.1:8000/api/v1/docs`
*   **ReDoc**: `http://127.0.0.1:8000/api/v1/redoc`

---

## 🧪 Running Tests

Tests run against an isolated in-memory SQLite database. Run them using:
```bash
# Set PYTHONPATH to root and run pytest
# Windows (PowerShell)
$env:PYTHONPATH="."
.\venv\Scripts\pytest

# macOS/Linux
PYTHONPATH=. pytest
```

---

## 📝 API Endpoints Summary

### Authentication (`/api/v1/auth`)
*   `POST /auth/register`: Create a new user account.
*   `POST /auth/login`: Authenticate credentials, returns a JWT token.
*   `GET /auth/me`: View active user profile (JWT required).

### Tasks (`/api/v1/tasks`)
*   `POST /tasks`: Create a task (can optionally assign to another user).
*   `GET /tasks`: List tasks owned by you.
*   `GET /tasks/assigned`: List tasks assigned to you.
*   `GET /tasks/{task_id}`: View specific task details (authorized for owner or assignee).
*   `PUT /tasks/{task_id}`: Update task details (authorized for owner or assignee).
*   `DELETE /tasks/{task_id}`: Delete a task (authorized **only** for the owner).

### Teams (`/api/v1/teams`)
*   `POST /teams`: Create a team (creator becomes `owner`).
*   `GET /teams`: View teams you belong to.
*   `GET /teams/{team_id}`: View team details and members.
*   `PUT /teams/{team_id}`: Update team name/description (requires `owner` or `admin`).
*   `DELETE /teams/{team_id}`: Delete team (requires `owner`).
*   `POST /teams/{team_id}/members`: Invite/Add user to team (requires `owner` or `admin`).
*   `PUT /teams/{team_id}/members/{user_id}`: Edit member roles (requires `owner`).
*   `DELETE /teams/{team_id}/members/{user_id}`: Remove member, or leave the team.