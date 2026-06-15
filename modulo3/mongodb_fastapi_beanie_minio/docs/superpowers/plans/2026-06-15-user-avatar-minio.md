# User Avatar Upload via MinIO — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add API endpoints to upload, stream and delete a user's avatar, storing the image bytes in MinIO (async via aioboto3) and the metadata embedded in the MongoDB `User` document.

**Architecture:** Layered — route (`rotas/users.py`) → storage service (`storage.py`) → MinIO. The route never touches S3 directly. Avatar metadata lives in an embedded Pydantic model on `User`. Image bytes are proxied through the API (MinIO stays private).

**Tech Stack:** FastAPI, Beanie 2.x (pymongo `AsyncMongoClient`), MongoDB, aioboto3 (S3 client for MinIO), pytest + pytest-asyncio + httpx for tests.

**Prerequisites for running tests:** a local MongoDB reachable at `mongodb://localhost:27017` (tests use a separate `blog_test` database and clean up after themselves). MinIO is NOT needed for tests — the storage layer is monkeypatched.

---

## File Structure

- Modify `pyproject.toml` — add `aioboto3` runtime dep + test deps + pytest config.
- Modify `.env-exemplo` and `.env` — add MinIO variables.
- Modify `modelos.py` — add embedded `Avatar` model + `avatar` field on `User`.
- Create `storage.py` — async MinIO/S3 helpers (`ensure_bucket`, `upload_avatar`, `download_avatar`, `delete_avatar`).
- Modify `main.py` — call `ensure_bucket()` in the `lifespan` startup.
- Modify `rotas/users.py` — add `POST/GET/DELETE /users/{user_id}/avatar`.
- Create `tests/conftest.py` — async test client fixture with Beanie init + monkeypatched storage.
- Create `tests/test_avatar.py` — endpoint tests.

---

## Task 1: Dependencies and configuration

**Files:**
- Modify: `pyproject.toml`
- Modify: `.env-exemplo`
- Modify: `.env`

- [ ] **Step 1: Add dependencies and pytest config to `pyproject.toml`**

Replace the `[project]` dependencies block and append config so the file reads:

```toml
[project]
name = "mongodb-fastapi-beanie"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "beanie>=2.0.1",
    "fastapi-pagination>=0.15.5",
    "fastapi[standard]>=0.128.0",
    "aioboto3>=13.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Install dependencies**

Run: `uv sync`
Expected: resolves and installs `aioboto3`, `pytest`, `pytest-asyncio`, `httpx`.

- [ ] **Step 3: Add MinIO variables to `.env-exemplo`**

File content becomes:

```
DATABASE_URL="mongodb://localhost:27017"
DBNAME="blog"
MINIO_ENDPOINT_URL="http://localhost:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin"
MINIO_BUCKET="avatars"
MINIO_REGION="us-east-1"
```

- [ ] **Step 4: Add the same MinIO variables to `.env`**

Append to `.env` (keep existing two lines, fill in your real credentials):

```
MINIO_ENDPOINT_URL="http://localhost:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin"
MINIO_BUCKET="avatars"
MINIO_REGION="us-east-1"
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock .env-exemplo
git commit -m "chore: add aioboto3, test deps and MinIO config"
```

---

## Task 2: Avatar model and storage layer

**Files:**
- Modify: `modelos.py`
- Create: `storage.py`
- Modify: `main.py:7-11` (lifespan)

- [ ] **Step 1: Add the `Avatar` model and `avatar` field in `modelos.py`**

At the top, extend the imports to include `datetime`:

```python
from beanie import Document, Link
from beanie.odm.fields import PydanticObjectId
from pydantic import Field
from pydantic import BaseModel
from datetime import datetime
```

Add the `Avatar` model immediately above the `User` class:

```python
class Avatar(BaseModel):
    object_key: str
    content_type: str
    size: int
    original_filename: str | None = None
    uploaded_at: datetime
```

Add the `avatar` field to `User`:

```python
class User(Document):
    name: str | None = None
    email: str | None = None
    avatar: Avatar | None = None

    class Settings:
        name = "users"
```

- [ ] **Step 2: Create `storage.py`**

```python
import os
import logging

import aioboto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

MINIO_ENDPOINT_URL = os.getenv("MINIO_ENDPOINT_URL")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "avatars")
MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")

logger = logging.getLogger(__name__)

_session = aioboto3.Session()


def _client():
    return _session.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT_URL,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name=MINIO_REGION,
    )


async def ensure_bucket() -> None:
    async with _client() as s3:
        try:
            await s3.head_bucket(Bucket=MINIO_BUCKET)
            logger.info(f"MinIO bucket '{MINIO_BUCKET}' already exists")
        except ClientError:
            await s3.create_bucket(Bucket=MINIO_BUCKET)
            logger.info(f"MinIO bucket '{MINIO_BUCKET}' created")


async def upload_avatar(object_key: str, data: bytes, content_type: str) -> None:
    async with _client() as s3:
        await s3.put_object(
            Bucket=MINIO_BUCKET,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )


async def download_avatar(object_key: str) -> tuple[bytes, str]:
    async with _client() as s3:
        resp = await s3.get_object(Bucket=MINIO_BUCKET, Key=object_key)
        content_type = resp.get("ContentType", "application/octet-stream")
        data = await resp["Body"].read()
        return data, content_type


async def delete_avatar(object_key: str) -> None:
    async with _client() as s3:
        await s3.delete_object(Bucket=MINIO_BUCKET, Key=object_key)
```

- [ ] **Step 3: Wire `ensure_bucket()` into the lifespan in `main.py`**

Update the imports and `lifespan` function. Imports:

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from rotas import home, users, posts, tags
from database import init_db, close_db
from storage import ensure_bucket
from fastapi_pagination import add_pagination
```

Lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await ensure_bucket()
    yield
    await close_db()
```

- [ ] **Step 4: Verify the app imports cleanly**

Run: `uv run python -c "import main; import storage; from modelos import Avatar; print('ok')"`
Expected: prints `ok` with no import errors.

- [ ] **Step 5: Commit**

```bash
git add modelos.py storage.py main.py
git commit -m "feat: add Avatar model and MinIO storage layer"
```

---

## Task 3: Upload endpoint (POST /users/{user_id}/avatar)

**Files:**
- Modify: `rotas/users.py`
- Create: `tests/conftest.py`
- Create: `tests/test_avatar.py`

- [ ] **Step 1: Create the test fixture `tests/conftest.py`**

```python
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from pymongo import AsyncMongoClient
from beanie import init_beanie

import storage
from modelos import User, Post, Comment
from main import app


@pytest_asyncio.fixture
async def client(monkeypatch):
    mongo = AsyncMongoClient("mongodb://localhost:27017")
    db = mongo["blog_test"]
    await init_beanie(database=db, document_models=[User, Post, Comment])
    await User.delete_all()

    store: dict[str, tuple[bytes, str]] = {}

    async def fake_upload(object_key, data, content_type):
        store[object_key] = (data, content_type)

    async def fake_download(object_key):
        return store[object_key]

    async def fake_delete(object_key):
        store.pop(object_key, None)

    monkeypatch.setattr(storage, "upload_avatar", fake_upload)
    monkeypatch.setattr(storage, "download_avatar", fake_download)
    monkeypatch.setattr(storage, "delete_avatar", fake_delete)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    await User.delete_all()
    mongo.close()
```

Note: the fixture initializes Beanie directly (the ASGI transport does not run the app `lifespan`), so MinIO is never contacted in tests.

- [ ] **Step 2: Write the failing upload tests in `tests/test_avatar.py`**

```python
async def _create_user(client):
    resp = await client.post("/users/", json={"name": "Ana", "email": "ana@x.com"})
    assert resp.status_code == 200
    return resp.json()["_id"]


async def test_upload_avatar_valid(client):
    user_id = await _create_user(client)
    files = {"file": ("pic.png", b"\x89PNG\r\n\x1a\n", "image/png")}
    resp = await client.post(f"/users/{user_id}/avatar", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["avatar"]["content_type"] == "image/png"
    assert body["avatar"]["object_key"] == f"avatars/{user_id}.png"
    assert body["avatar"]["size"] == 8
    assert body["avatar"]["original_filename"] == "pic.png"


async def test_upload_avatar_unsupported_type(client):
    user_id = await _create_user(client)
    files = {"file": ("note.txt", b"hello", "text/plain")}
    resp = await client.post(f"/users/{user_id}/avatar", files=files)
    assert resp.status_code == 400


async def test_upload_avatar_too_large(client):
    user_id = await _create_user(client)
    big = b"\x00" * (5 * 1024 * 1024 + 1)
    files = {"file": ("big.png", big, "image/png")}
    resp = await client.post(f"/users/{user_id}/avatar", files=files)
    assert resp.status_code == 413


async def test_upload_avatar_user_not_found(client):
    files = {"file": ("pic.png", b"\x89PNG", "image/png")}
    resp = await client.post("/users/64b8f0000000000000000000/avatar", files=files)
    assert resp.status_code == 404
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_avatar.py -v`
Expected: FAIL — endpoint `POST /users/{user_id}/avatar` returns 405/404 (route not defined yet).

- [ ] **Step 4: Implement the upload endpoint in `rotas/users.py`**

Update the imports at the top of the file:

```python
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from beanie import PydanticObjectId
from fastapi_pagination import Page
from fastapi_pagination.ext.beanie import apaginate
from datetime import datetime, timezone

import storage
from modelos import User, Avatar
```

Add these module-level constants just below the `router = APIRouter(...)` block:

```python
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB
```

Add the endpoint (place it after `create_user`):

```python
@router.post("/{user_id}/avatar", response_model=User)
async def upload_user_avatar(
    user_id: PydanticObjectId, file: UploadFile = File(...)
) -> User:
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    data = await file.read()
    if len(data) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    extension = ALLOWED_TYPES[file.content_type]
    object_key = f"avatars/{user_id}{extension}"

    try:
        await storage.upload_avatar(object_key, data, file.content_type)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Storage error") from exc

    user.avatar = Avatar(
        object_key=object_key,
        content_type=file.content_type,
        size=len(data),
        original_filename=file.filename,
        uploaded_at=datetime.now(timezone.utc),
    )
    await user.save()
    return user
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_avatar.py -v`
Expected: the 4 upload tests PASS.

- [ ] **Step 6: Commit**

```bash
git add rotas/users.py tests/conftest.py tests/test_avatar.py
git commit -m "feat: add user avatar upload endpoint"
```

---

## Task 4: Download endpoint (GET /users/{user_id}/avatar)

**Files:**
- Modify: `rotas/users.py`
- Modify: `tests/test_avatar.py`

- [ ] **Step 1: Write the failing download tests in `tests/test_avatar.py`**

Append:

```python
async def test_download_avatar(client):
    user_id = await _create_user(client)
    files = {"file": ("pic.png", b"\x89PNG\r\n\x1a\n", "image/png")}
    await client.post(f"/users/{user_id}/avatar", files=files)

    resp = await client.get(f"/users/{user_id}/avatar")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content == b"\x89PNG\r\n\x1a\n"


async def test_download_avatar_missing(client):
    user_id = await _create_user(client)
    resp = await client.get(f"/users/{user_id}/avatar")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_avatar.py::test_download_avatar -v`
Expected: FAIL — GET route not defined (405/404).

- [ ] **Step 3: Implement the download endpoint in `rotas/users.py`**

Add after `upload_user_avatar`:

```python
@router.get("/{user_id}/avatar")
async def get_user_avatar(user_id: PydanticObjectId) -> StreamingResponse:
    user = await User.get(user_id)
    if not user or not user.avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    try:
        data, content_type = await storage.download_avatar(user.avatar.object_key)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Storage error") from exc

    return StreamingResponse(iter([data]), media_type=content_type)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_avatar.py -v`
Expected: download tests PASS, all previous tests still PASS.

- [ ] **Step 5: Commit**

```bash
git add rotas/users.py tests/test_avatar.py
git commit -m "feat: add user avatar download (streaming) endpoint"
```

---

## Task 5: Delete endpoint (DELETE /users/{user_id}/avatar)

**Files:**
- Modify: `rotas/users.py`
- Modify: `tests/test_avatar.py`

- [ ] **Step 1: Write the failing delete tests in `tests/test_avatar.py`**

Append:

```python
async def test_delete_avatar(client):
    user_id = await _create_user(client)
    files = {"file": ("pic.png", b"\x89PNG\r\n\x1a\n", "image/png")}
    await client.post(f"/users/{user_id}/avatar", files=files)

    resp = await client.delete(f"/users/{user_id}/avatar")
    assert resp.status_code == 200
    assert resp.json()["avatar"] is None

    # subsequent download is now 404
    resp = await client.get(f"/users/{user_id}/avatar")
    assert resp.status_code == 404


async def test_delete_avatar_missing(client):
    user_id = await _create_user(client)
    resp = await client.delete(f"/users/{user_id}/avatar")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_avatar.py::test_delete_avatar -v`
Expected: FAIL — DELETE route not defined (405/404).

- [ ] **Step 3: Implement the delete endpoint in `rotas/users.py`**

Add after `get_user_avatar`:

```python
@router.delete("/{user_id}/avatar", response_model=User)
async def delete_user_avatar(user_id: PydanticObjectId) -> User:
    user = await User.get(user_id)
    if not user or not user.avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    try:
        await storage.delete_avatar(user.avatar.object_key)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Storage error") from exc

    user.avatar = None
    await user.save()
    return user
```

- [ ] **Step 4: Run the full test suite**

Run: `uv run pytest tests/ -v`
Expected: all tests PASS (upload, download, delete, and validation cases).

- [ ] **Step 5: Commit**

```bash
git add rotas/users.py tests/test_avatar.py
git commit -m "feat: add user avatar delete endpoint"
```

---

## Self-Review Notes

- **Spec coverage:** Avatar model (Task 2), MinIO config/.env (Task 1), storage layer with ensure_bucket/upload/download/delete (Task 2), startup bucket creation (Task 2), POST/GET/DELETE endpoints (Tasks 3–5), validations 400/413/404 and 502 storage errors (Tasks 3–5), tests for all cases incl. missing-avatar 404 (Tasks 3–5). All spec sections mapped.
- **Route ordering:** the avatar routes use the `/{user_id}/avatar` prefix and do not collide with the existing `/{user_id}` routes (distinct path suffix), so FastAPI matching is unambiguous.
- **Storage import style:** routes call `storage.upload_avatar(...)` via the module, which is what the test `monkeypatch.setattr(storage, ...)` patches — names stay consistent across tasks.
- **Type consistency:** `Avatar` fields (`object_key`, `content_type`, `size`, `original_filename`, `uploaded_at`) are used identically in the model, the upload endpoint, and the assertions in tests.
