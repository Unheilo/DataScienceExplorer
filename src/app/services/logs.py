from models.logs import Request


def log_request(request: Request, session) -> None:
    """Записывает в БД запрос от пользователя и ответ модели."""
    session.add(request)
    session.commit()
    session.refresh(request)


def get_history(user_id: int, session) -> list[Request]:
    """Возвращает историю успешных запросов пользователя."""
    req_history = (
        session.query(Request)
        .where(Request.user_id == user_id)
        .all()
    )
    return req_history
