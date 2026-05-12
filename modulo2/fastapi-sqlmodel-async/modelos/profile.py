from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import User

class Profile(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True, foreign_key="user.id")
	bio: str
	user: "User" = Relationship(back_populates="profile")
