from sqlmodel import SQLModel, Field
from pydantic import BaseModel


class User(SQLModel, table=True):
    """Модель пользователя."""

    user_id: int = Field(default=None, primary_key=True)
    email: str
    username: str
    password_hash: str
    role: str = Field(default='customer')


class TokenResponse(BaseModel):
    """Модель возвращаемого токена."""

    access_token: str
    token_type: str
