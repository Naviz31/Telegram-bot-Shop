from dotenv import load_dotenv
import os

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем значение переменных окружения
TG_TOKEN = os.getenv("TG_TOKEN")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
MANAGERS_ID = os.getenv("MANAGERS_ID")
ADMINS_ID = os.getenv("ADMINS_ID")
METHOD_MAIL_RUSSIAN = os.getenv("METHOD_MAIL_RUSSIAN") # True - Почта России предлагается как метод доставки, False - нет
METHOD_SDEK = os.getenv("METHOD_SDEK") # True - СДЭК предлагается как метод доставки, False - нет
METHOD_YANDEX = os.getenv("METHOD_YANDEX") # True - Яндекс Доставка предлагается как метод доставки, False - нет

######################################################
#          Данный для работы с Почтой России         #
#              Через otpravka.pochta.ru              #
######################################################

INDEX_FROM = os.getenv("INDEX_FROM")
LOGIN_MAIL = os.getenv("LOGIN_MAIL")
PASSWORD_MAIL = os.getenv("PASSWORD_MAIL")
TOKEN_MAIL = os.getenv("TOKEN_MAIL")

# Преобразуем в список int
if MANAGERS_ID:
    MANAGERS_ID = [int(id.strip()) for id in MANAGERS_ID.split(",")]
else:
    MANAGERS_ID = []