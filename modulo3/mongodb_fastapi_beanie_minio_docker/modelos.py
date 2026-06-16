from beanie import Document, Link
from beanie.odm.fields import PydanticObjectId
from pydantic import Field
from pydantic import BaseModel
from datetime import datetime


class Avatar(BaseModel):
    object_key: str
    content_type: str
    size: int
    original_filename: str | None = None
    uploaded_at: datetime


class User(Document):
    name: str | None = None
    email: str | None = None
    avatar: Avatar | None = None

    class Settings:
        name = "users"


class Comment(Document):
    user: Link[User]
    content: str

    class Settings:
        name = "comments"

class CommentParam(BaseModel):
    user: PydanticObjectId
    content: str

class Post(Document):
    title: str
    content: str
    user: Link[User]
    comments: list[Link[Comment]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    class Settings:
        name = "posts"
        indexes = ["tags"]

class PostCreate(BaseModel):
    title: str
    content: str
    user: PydanticObjectId = Field(..., description="ID do usuário")
    tags: list[str] = Field(default_factory=list)