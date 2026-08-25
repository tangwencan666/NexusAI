from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ResourceSchema


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=100)
    hashed_password: str | None = Field(default=None, max_length=255)


class UserRead(ResourceSchema):
    email: EmailStr
    username: str
    is_active: bool
    is_superuser: bool
