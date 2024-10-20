from fastapi import Depends, HTTPException, status
from auth.jwt_handler import verify_access_token
from services.auth.cookieauth import OAuth2PasswordBearerWithCookie

oauth2_scheme_cookie = OAuth2PasswordBearerWithCookie(tokenUrl="/home/token")


async def authenticate_cookie(token: str = Depends(oauth2_scheme_cookie)
                              ) -> str:
    """
    Выполняет аутентификацию пользователя на основании токена

    Args:
        token (str): OAuth2 токен

    Returns:
        str: идентификатор пользователя,
        совпадает с полем user_id в таблице User

    Raises:
        HTTPException: Если токен некорректен или истёк срок действия
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sign in for access"
            )
    token = token.removeprefix('Bearer ')
    decoded_token = verify_access_token(token)
    return decoded_token["user"]
