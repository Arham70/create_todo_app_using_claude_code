# User API — FastAPI + File System Storage

A simple REST API built with **FastAPI** that stores user data on the file system (JSON file) — no database required.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users` | Create a new user |
| `GET` | `/users` | List all users |
| `GET` | `/users/{id}` | Get a user by ID |
| `PUT` | `/users/{id}` | Update a user |
| `DELETE` | `/users/{id}` | Delete a user |

## User Schema

```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "age": 30
}
```

## Run

```bash
pip install fastapi uvicorn
uvicorn main:app --reload
```

API docs available at: http://127.0.0.1:8000/docs

## Storage

User data is stored in `data/users.json` as a JSON array. Each user gets a UUID on creation.

## Test

```bash
pip install pytest httpx
pytest test_main.py -v
```
