import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = sys.stdout


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def parse_homework_status(homework):
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']

        hw_statuses = {
            'reviewing': f'Работа {homework_name} проверяется',
            'rejected': 'К сожалению в работе нашлись ошибки.',
            'approved': ('Ревьюеру всё понравилось, '
                         'можно приступать к следующему уроку.'),
        }

        if homework_status == 'reviewing':
            return hw_statuses['reviewing']

        if homework_status == 'rejected':
            verdict = hw_statuses['rejected']

        elif homework_status == 'approved':
            verdict = hw_statuses['approved']

        else:
            verdict = f'Результат проверки: {homework_status}'

        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'

    except Exception as e:
        raise KeyError(f'Ошибка парсинга статуса домашнего задания. "{e}"')


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {"PRAKTIKUM_TOKEN"}'}
    data = {'from_date': current_timestamp}

    if current_timestamp is None:
        current_timestamp = int(time.time())

    try:
        homework_statuses = requests.get(
            'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
            headers=headers,
            params=data,
        )
        return homework_statuses.json()

    except requests.exceptions.RequestException as e:
        logging.exception(f'Ошибка: {e}')

    except ValueError as e:
        logging.exception(f'Ошибка: {e}')
        return {}


def send_message(message, bot_client):
    logger.info(message)
    return bot_client.send_message(CHAT_ID, message)


def main():
    # инициализация бота
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logger.debug('Бот успешно запущен')
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)

            homeworks = new_homework.get('homeworks')
            new_timestamp = new_homework.get('current_date')

            if homeworks and new_timestamp:
                try:
                    send_message(parse_homework_status(homeworks[0]), bot)
                    current_timestamp = new_timestamp

                except Exception as e:
                    logger.error(e)
                    bot.send_message(
                        CHAT_ID, f'Бот столкнулся с ошибкой: "{e}"')

        except Exception as e:
            logger.error(e)
            bot.send_message(CHAT_ID, f'Бот столкнулся с ошибкой: "{e}"')

        time.sleep(300)


if __name__ == '__main__':
    main()
