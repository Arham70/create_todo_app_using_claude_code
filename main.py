import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"

DATA_DIR.mkdir(exist_ok=True)
if not USERS_FILE.exists():
    USERS_FILE.write_text("[]")

app = FastAPI(title="User API (File System Storage)")


class UserCreate(BaseModel):
    name: str
    email: str
    age: Optional[int] = None


class User(UserCreate):
    id: str


def load_users() -> list[dict]:
    return json.loads(USERS_FILE.read_text())


def save_users(users: list[dict]) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2))


@app.post("/users", response_model=User, status_code=201)
def create_user(user: UserCreate):
    users = load_users()
    if any(u["email"] == user.email for u in users):
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = {"id": str(uuid.uuid4()), **user.model_dump()}
    users.append(new_user)
    save_users(users)
    return new_user


@app.get("/users", response_model=list[User])
def list_users():
    return load_users()


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: str):
    users = load_users()
    for user in users:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: str, updated: UserCreate):
    users = load_users()
    for i, user in enumerate(users):
        if user["id"] == user_id:
            if any(u["email"] == updated.email and u["id"] != user_id for u in users):
                raise HTTPException(status_code=400, detail="Email already in use")
            users[i] = {"id": user_id, **updated.model_dump()}
            save_users(users)
            return users[i]
    raise HTTPException(status_code=404, detail="User not found")


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str):
    users = load_users()
    new_users = [u for u in users if u["id"] != user_id]
    if len(new_users) == len(users):
        raise HTTPException(status_code=404, detail="User not found")
    save_users(new_users)
