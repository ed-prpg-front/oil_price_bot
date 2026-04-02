import pytz;

import os

TOKEN = os.getenv("TOKEN")

#Адрес страницы с ценами

TARGET_URL = "https://new.trade.tatneft.ru/promo/production/58";

#Московский часовой пояс

MOSCOW_TZ = pytz.timezone("Europe/Moscow");

CHAT_ID_FILE = os.getenv("CHAT_ID_FILE", "chat_id.txt")
PRICES_FILE = os.getenv("PRICES_FILE", "prices.json")
