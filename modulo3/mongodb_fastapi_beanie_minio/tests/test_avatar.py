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
