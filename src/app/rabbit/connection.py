import pika

# Параметры подключения
connection_params = pika.ConnectionParameters(
    host='rabbit',          # Адрес RabbitMQ сервера
    port=5672,              # Порт по умолчанию для RabbitMQ
    virtual_host='/',       # Виртуальный хост (обычно '/')
    credentials=pika.PlainCredentials(
        username='rmuser',  # Имя пользователя
        password='rmpass',  # Пароль
    ),
    heartbeat=30,
    blocked_connection_timeout=2
)
