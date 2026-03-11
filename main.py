import sqlite3
import uuid
from contextlib import contextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DB_PATH = "users.db"


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                age INTEGER
            )
            """
        )


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


app = FastAPI(title="User API (SQLite Storage)")

init_db()


class UserCreate(BaseModel):
    name: str
    email: str
    age: Optional[int] = None


class User(UserCreate):
    id: str


def row_to_user(row) -> dict:
    return {"id": row["id"], "name": row["name"], "email": row["email"], "age": row["age"]}


@app.post("/users", response_model=User, status_code=201)
def create_user(user: UserCreate):
    user_id = str(uuid.uuid4())
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (id, name, email, age) VALUES (?, ?, ?, ?)",
                (user_id, user.name, user.email, user.age),
            )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    return {"id": user_id, **user.model_dump()}


@app.get("/users", response_model=list[User])
def list_users():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users").fetchall()
    return [row_to_user(r) for r in rows]


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return row_to_user(row)


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: str, updated: UserCreate):
    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            conn.execute(
                "UPDATE users SET name = ?, email = ?, age = ? WHERE id = ?",
                (updated.name, updated.email, updated.age, user_id),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email already in use")
    return {"id": user_id, **updated.model_dump()}


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str):
    with get_conn() as conn:
        result = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
