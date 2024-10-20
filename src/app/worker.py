import pika
import pandas as pd
import joblib
import json

from database.database import get_session
from services import user as UserService
from rabbit.connection import connection_params
from catboost import CatBoostRegressor

# Загрузка модели
# with open('./mlsys/model_from.pkl', 'rb') as file:
#     model_from = joblib.load(file)
#
# with open('./mlsys/model_to.pkl', 'rb') as file:
#     model_to = joblib.load(file)


model = CatBoostRegressor()
model.load_model('./mlsys/cb_super')

# Установка соединения
connection = pika.BlockingConnection(connection_params)

# Создание канала
channel = connection.channel()

queue_name = 'ML_queue'

# Создание очереди
channel.queue_declare(queue=queue_name)


# Функция, которая будет вызвана при получении сообщения
def callback(ch, method, properties, body):

    # Обработка полученного запроса
    body = json.loads(body)
    with next(get_session()) as session:
        process_response = UserService.process_request(body['user_id'],
                                                       body['specializations'],
                                                       body['text'],
                                                       body['experience'],
                                                       body['employment'],
                                                       body['area'],
                                                       body['schedule'],
                                                       model,
                                                       session)

    # Отправка ответа в качестве ответа в канал
    # c уникальным идентификатором
    response_channel = connection.channel()
    response_channel.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        body=json.dumps(process_response),
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id
            )
    )
    response_channel.close()
    # Ручное подтверждение обработки сообщения
    ch.basic_ack(delivery_tag=method.delivery_tag)



def start_worker():
    # Подписка на очередь и установка обработчика сообщений
    channel.basic_consume(queue=queue_name,
                          on_message_callback=callback,
                          auto_ack=False)
    # Начало потребления сообщений
    print('Waiting for messages')
    channel.start_consuming()


if __name__ == '__main__':
    start_worker()
