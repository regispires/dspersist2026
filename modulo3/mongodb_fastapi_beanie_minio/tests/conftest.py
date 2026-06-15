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
    await mongo.close()
