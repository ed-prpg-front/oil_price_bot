import json
import os
from config import PRICES_FILE

# ---------- Цены (без изменений) ----------
def load_last_prices():
    if os.path.exists(PRICES_FILE):
        with open(PRICES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_prices(prices):
    with open(PRICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)

# ---------- Подписчики (новое) ----------
SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    """Загружает список chat_id подписчиков"""
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_subscribers(subscribers):
    """Сохраняет список подписчиков"""
    with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(subscribers, f, ensure_ascii=False, indent=2)

def add_subscriber(chat_id):
    """Добавляет пользователя в список, если его там ещё нет"""
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)
        return True
    return False

def remove_subscriber(chat_id):
    """Удаляет пользователя из списка"""
    subscribers = load_subscribers()
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers(subscribers)
        return True
    return False

def get_all_subscribers():
    """Возвращает список всех подписчиков"""
    return load_subscribers()
