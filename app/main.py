import os
import sqlite3
import time
from typing import Any

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from pydantic import BaseModel

INSTANCE_NAME = os.getenv("INSTANCE_NAME", "backend")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
DB_PATH = os.getenv("DB_PATH", "app.db")

app = FastAPI(title="Lab07 Login + CRUD")

def hello_text() -> str:
    # INSTANCE_NAME esperado: backend-1/backend-2/backend-3 (pero soporta otros)
    suffix = INSTANCE_NAME.split("-")[-1]
    if suffix.isdigit():
        return f"Hola mundo {suffix}"
    return f"Hola mundo ({INSTANCE_NAME})"


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          description TEXT NOT NULL,
          created_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def create_token(username: str) -> str:
    now = int(time.time())
    payload = {"sub": username, "iat": now, "exp": now + 60 * 60}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def require_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return str(sub)


class LoginIn(BaseModel):
    username: str
    password: str


class ItemIn(BaseModel):
    name: str
    description: str


class ItemOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: int
    instance: str


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "instance": INSTANCE_NAME}

@app.get("/hello")
def hello() -> dict[str, Any]:
    return {"message": hello_text(), "instance": INSTANCE_NAME}


@app.post("/login")
def login(payload: LoginIn) -> dict[str, Any]:
    if payload.username != ADMIN_USER or payload.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")
    return {"token": create_token(payload.username), "instance": INSTANCE_NAME}


# --- Rutas /api (para servir frontend en / y API en /api) ---
@app.get("/api/health")
def health_api() -> dict[str, Any]:
    return health()


@app.get("/api/hello")
def hello_api() -> dict[str, Any]:
    return hello()


@app.post("/api/login")
def login_api(payload: LoginIn) -> dict[str, Any]:
    return login(payload)


@app.get("/items", response_model=list[ItemOut])
def list_items(_: str = Depends(require_user)) -> list[ItemOut]:
    conn = db()
    rows = conn.execute("SELECT id, name, description, created_at FROM items ORDER BY id").fetchall()
    return [
        ItemOut(
            id=int(r["id"]),
            name=str(r["name"]),
            description=str(r["description"]),
            created_at=int(r["created_at"]),
            instance=INSTANCE_NAME,
        )
        for r in rows
    ]

@app.get("/api/items", response_model=list[ItemOut])
def list_items_api(user: str = Depends(require_user)) -> list[ItemOut]:
    return list_items(user)


@app.post("/items", response_model=ItemOut, status_code=201)
def create_item(payload: ItemIn, _: str = Depends(require_user)) -> ItemOut:
    conn = db()
    created_at = int(time.time())
    cur = conn.execute(
        "INSERT INTO items (name, description, created_at) VALUES (?, ?, ?)",
        (payload.name, payload.description, created_at),
    )
    conn.commit()
    item_id = int(cur.lastrowid)
    return ItemOut(
        id=item_id,
        name=payload.name,
        description=payload.description,
        created_at=created_at,
        instance=INSTANCE_NAME,
    )

@app.post("/api/items", response_model=ItemOut, status_code=201)
def create_item_api(payload: ItemIn, user: str = Depends(require_user)) -> ItemOut:
    return create_item(payload, user)


@app.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int, _: str = Depends(require_user)) -> ItemOut:
    conn = db()
    row = conn.execute(
        "SELECT id, name, description, created_at FROM items WHERE id = ?",
        (item_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return ItemOut(
        id=int(row["id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        created_at=int(row["created_at"]),
        instance=INSTANCE_NAME,
    )

@app.get("/api/items/{item_id}", response_model=ItemOut)
def get_item_api(item_id: int, user: str = Depends(require_user)) -> ItemOut:
    return get_item(item_id, user)


@app.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemIn, _: str = Depends(require_user)) -> ItemOut:
    conn = db()
    row = conn.execute(
        "SELECT id, created_at FROM items WHERE id = ?",
        (item_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    conn.execute(
        "UPDATE items SET name = ?, description = ? WHERE id = ?",
        (payload.name, payload.description, item_id),
    )
    conn.commit()
    return ItemOut(
        id=item_id,
        name=payload.name,
        description=payload.description,
        created_at=int(row["created_at"]),
        instance=INSTANCE_NAME,
    )

@app.put("/api/items/{item_id}", response_model=ItemOut)
def update_item_api(item_id: int, payload: ItemIn, user: str = Depends(require_user)) -> ItemOut:
    return update_item(item_id, payload, user)


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, _: str = Depends(require_user)) -> Response:
    conn = db()
    cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return Response(status_code=204)


@app.delete("/api/items/{item_id}", status_code=204)
def delete_item_api(item_id: int, user: str = Depends(require_user)) -> Response:
    return delete_item(item_id, user)

