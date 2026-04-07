import pytz;

import os

TOKEN = os.getenv("TOKEN")
CRON_SECRET = os.getenv("CRON_SECRET", "default_secret_change_me")

#Адрес страницы с ценами

#TARGET_URL = "https://new.trade.tatneft.ru/promo/api/v1/products-categories?ascending=true&order=name";

#Московский часовой пояс

MOSCOW_TZ = pytz.timezone("Europe/Moscow");

CHAT_ID_FILE = os.getenv("CHAT_ID_FILE", "chat_id.txt")
PRICES_FILE = os.getenv("PRICES_FILE", "prices.json")
