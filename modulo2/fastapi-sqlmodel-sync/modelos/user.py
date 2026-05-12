from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
from .profile import Profile
if TYPE_CHECKING:
	from .post import Post
	from .comment import Comment

class UserBase(SQLModel):
	id: int | None = Field(default=None, primary_key=True)
	name: str
	email: str

class User(UserBase, table=True):
    profile: Profile = Relationship(back_populates="user")
    posts: list["Post"] = Relationship(back_populates="user")
    comments: list["Comment"] = Relationship(back_populates="user")
