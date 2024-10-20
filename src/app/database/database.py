from sqlmodel import SQLModel, Session, create_engine

from database.config import get_settings

engine = create_engine(
    url=get_settings().DATABASE_URL_psycopg,
    echo=False,
    pool_size=5,
    max_overflow=10
)


def get_session():
    """
    Возвращает генератор объекта Session, что обеспечивает закрытие
    сессии связи с БД после окончания использования Session.
    """
    with Session(engine) as session:
        yield session


def init_db():
    """Инициализирует базу данных."""
    # раскомментировать для отладки:
    # SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
