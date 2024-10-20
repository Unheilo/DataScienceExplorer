import time
from pytz import timezone
from datetime import datetime
from fastapi import HTTPException, status
from jose import jwt, JWTError

from database.database import get_settings

# Получение секретного ключа из .env
settings = get_settings()
SECRET_KEY = settings.SECRET_KEY

# Установка московского часового пояса
mtz = timezone('Europe/Moscow')


def create_access_token(user: str) -> str:
    """
    Создает токен с данными

    Args:
        user (str): идентификатор пользователя, который
        совпадает с полем user_id в таблице User

    Returns:
        str: Закодированный по алгоритму HS256 токен
    """
    payload = {"user": user,
               "expires": time.time() + 3600}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_access_token(token: str) -> dict:
    """
    Выполняет верификацию токена

    Args:
        token (str): OAuth2 токен

    Возвращает:
        dict: Словарь с данными токена, а именно: идентификатор пользователя,
        который совпадает с полем user_id в таблице User

    Raises:
        HTTPException: Если токен некорректен, не содержит срока действия или
                       срок действия истек.
                        Возможные статусы HTTP ошибок:
                        - 400 Bad Request: Если токен некорректен или не
                        содержит срока действия.
                        - 403 Forbidden: Если срок действия токена истек.
    """
    try:
        data = jwt.decode(token,
                          SECRET_KEY,
                          algorithms=["HS256"])
        expire = data.get("expires")
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied"
            )
        if datetime.now(tz=mtz) > datetime.fromtimestamp(expire, tz=mtz):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token expired!"
            )
        return data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
