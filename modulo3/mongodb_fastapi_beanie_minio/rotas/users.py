from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from beanie import PydanticObjectId
from fastapi_pagination import Page
from fastapi_pagination.ext.beanie import apaginate
from datetime import datetime, timezone

import storage
from modelos import User, Avatar

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB


@router.get("/", response_model=Page[User])
async def get_users() -> Page[User]:
    return await apaginate(User.find_all()) # equivalente a User.find({})


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: PydanticObjectId) -> User:
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=User)
async def create_user(user: User) -> User:
    await user.insert()
    return user


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


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: PydanticObjectId, user_data: dict) -> User:
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Atualiza apenas campos presentes no dict
    for key, value in user_data.items():
        setattr(user, key, value)

    await user.save()
    return user


@router.delete("/{user_id}")
async def delete_user(user_id: PydanticObjectId) -> dict:
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user.delete()
    return {"message": "User deleted"}
