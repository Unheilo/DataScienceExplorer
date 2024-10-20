from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class SalaryData(BaseModel):
    """Модель ответа ML сервиса."""

    salary: int

# class SalaryData(BaseModel):
#     """Модель ответа ML сервиса."""
#
#     salary_from: int
#     salary_to: int


class Request(SQLModel, table=True):
    """Модель запроса."""

    request_id: int = Field(default=None, primary_key=True)
    user_id: int = Field(default=None, foreign_key="user.user_id")
    vacancy_name: str
    vacancy_description: str
    salary_from: int
    salary_to: int
    timestamp: datetime
