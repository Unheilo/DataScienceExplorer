from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from auth.authenticate import authenticate_cookie
from auth.hash_password import create_hash, verify_hash
from auth.jwt_handler import create_access_token
from database.database import get_session
from models.user import TokenResponse, User
from services import logs as LogService
from services import user as UserService

user_route = APIRouter(tags=['User'])


@user_route.post('/signup')
async def signup(
    username: str,
    email: str,
    password: str,
    session=Depends(get_session)
):
    """
    Проверяет, что пользователь с таким e-mail не зарегистрирован,
    хэширует пароль и создает нового пользователя в БД
    """
    hashed_password = create_hash(password)
    process_response = UserService.create_user(
        username,
        email,
        hashed_password,
        session
    )
    if process_response == {'error': 'Email already in use'}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use"
        )
    if process_response == {'success': 'Successfully created'}:
        return {"message": "User successfully registered!"}


@user_route.post("/signin", response_model=TokenResponse)
async def sign_user_in(
    email: str,
    password: str,
    session=Depends(get_session)
) -> dict:
    """
    Проверяет, что пользователь с таким e-mail и паролем зарегистрирован.
    Если пользователь зарегистрирован, возвращает JWT-токен.
    """
    user_exist = UserService.get_user_by_email(email, session)

    if user_exist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist"
        )

    if verify_hash(password, user_exist.password_hash):
        access_token = create_access_token(str(user_exist.user_id))
        return {"access_token": access_token, "token_type": "Bearer"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid details passed."
    )


@user_route.get("/auth/{token}")
async def auth(token: str):
    """
    Выполняет аутентификацию пользователя на основании токена
    """
    result = await authenticate_cookie(token)
    return result


@user_route.get('/get_all_users', response_model=List[User])
async def get_all_users(session=Depends(get_session)) -> list:
    """Возвращает список всех зарегистрированных пользователей"""
    return UserService.get_all_users(session)


@user_route.get('/get_history/{token}')
async def get_history(token: str, session=Depends(get_session)):
    """Возвращает историю успешных запросов пользователя"""
    user_id = int(await authenticate_cookie(token))
    history = LogService.get_history(user_id, session)
    return [
        {
            "request_id": req.request_id,
            "vacancy_name": req.vacancy_name,
            "vacancy_description": req.vacancy_description,
            "salary_from": req.salary_from,
            "salary_to": req.salary_to,
            "timestamp": req.timestamp
        }
        for req in history
    ]
