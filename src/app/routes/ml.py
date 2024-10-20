import json
import uuid

import pika
from fastapi import APIRouter, HTTPException, status

from auth.authenticate import authenticate_cookie
from rabbit.connection import connection_params

ml_route = APIRouter(tags=['MlService'])


@ml_route.post('/process_request/')
async def process_request(token: str, specializations: str, text: str, experience: str, employment: str, area: str, schedule: str):
    """
    Выполняет аутентификацию пользователя на основании токена.
    Формирует запрос и направляет его в очередь 'ML_queue' RabbitMQ,
    создает очередь с уникальным идентификатором для ответа от модели.
    После появления в уникальной очереди ответа - возвращает его.

    Args:
        token (str): токен, идентифицирующий пользователя;
        specializations(str): специализация по hh;
        text(str): описание вакансии;
        experience(str): опыт;
        'employment': employment;
        'area': area,
        'schedule': schedule
    Returns:
        list: ответ от ML сервиса

    Raises:
        HTTPException:
        - 500 Forbidden: Если модель вернула некорректный ответ.
    """
    user_id = int(await authenticate_cookie(token))
    message = {
        'user_id': user_id,
        'specializations': specializations,
        'text': text,
        'experience': experience,
        'employment': employment,
        'area': area,
        'schedule': schedule
    }

    req_id = str(uuid.uuid4())
    response_queue = f'response_queue_{req_id}'

    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.queue_declare(queue=response_queue, exclusive=True)

    def on_response(ch, method, properties, body):
        if properties.correlation_id == req_id:
            global response
            response = json.loads(body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            ch.stop_consuming()

    channel.basic_consume(
        queue=response_queue,
        on_message_callback=on_response,
        auto_ack=False
    )

    channel.basic_publish(
        exchange='',
        routing_key='ML_queue',
        body=json.dumps(message),
        properties=pika.BasicProperties(
            reply_to=response_queue,
            correlation_id=req_id
        )
    )

    # Начало ожидания ответа
    channel.start_consuming()
    print('Message sent, waiting for response from worker')
    connection.close()

    # Обработка сообщений от model.user.process_request
    if response == {'error': 'Model failed'}:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Model failed'
        )
    return response

# @ml_route.post('/process_request/')
# async def process_request(token: str, name: str, description: str):
#     """
#     Выполняет аутентификацию пользователя на основании токена.
#     Формирует запрос и направляет его в очередь 'ML_queue' RabbitMQ,
#     создает очередь с уникальным идентификатором для ответа от модели.
#     После появления в уникальной очереди ответа - возвращает его.
#
#     Args:
#         token (str): токен, идентифицирующий пользователя;
#         name (str): название вакансии;
#         description (str): описание вакансии;
#
#     Returns:
#         list: ответ от ML сервиса
#
#     Raises:
#         HTTPException:
#         - 500 Forbidden: Если модель вернула некорректный ответ.
#     """
#     user_id = int(await authenticate_cookie(token))
#     message = {
#         'user_id': user_id,
#         'name': name,
#         'description': description
#     }
#
#     req_id = str(uuid.uuid4())
#     response_queue = f'response_queue_{req_id}'
#
#     connection = pika.BlockingConnection(connection_params)
#     channel = connection.channel()
#     channel.queue_declare(queue=response_queue, exclusive=True)
#
#     def on_response(ch, method, properties, body):
#         if properties.correlation_id == req_id:
#             global response
#             response = json.loads(body)
#             ch.basic_ack(delivery_tag=method.delivery_tag)
#             ch.stop_consuming()
#
#     channel.basic_consume(
#         queue=response_queue,
#         on_message_callback=on_response,
#         auto_ack=False
#     )
#
#     channel.basic_publish(
#         exchange='',
#         routing_key='ML_queue',
#         body=json.dumps(message),
#         properties=pika.BasicProperties(
#             reply_to=response_queue,
#             correlation_id=req_id
#         )
#     )
#
#     # Начало ожидания ответа
#     channel.start_consuming()
#     print('Message sent, waiting for response from worker')
#     connection.close()
#
#     # Обработка сообщений от model.user.process_request
#     if response == {'error': 'Model failed'}:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail='Model failed'
#         )
#     return response
