import asyncio
import logging
import os
import threading
import time
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TOKEN, MOSCOW_TZ, TARGET_URL
from storage import load_last_prices, save_prices, load_chat_id, save_chat_id
from parser import fetch_prices
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# --- Настройка логирования ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Flask приложение для поддержки активности Render ---
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Bot is running!", 200

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    """Запуск Flask-сервера в отдельном потоке."""
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- Обработчики команд бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    await update.message.reply_text(
        "Привет! Я буду присылать тебе цены на нефтепродукты каждое утро в 8:00 и "
        "отчёт об изменениях после биржевых торгов (около 13:05 МСК)."
    )

async def morning_report(context: ContextTypes.DEFAULT_TYPE):
    chat_id = load_chat_id()
    if not chat_id:
        logger.warning("Нет сохранённого chat_id, утренний отчёт не отправлен.")
        return
    prices = fetch_prices()
    if prices:
        save_prices(prices)
        text = "🌅 Доброе утро! Текущие цены на нефтепродукты:\n"
        for product, price in prices.items():
            text += f"• {product}: {price} ₽\n"
        await context.bot.send_message(chat_id=chat_id, text=text)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Не удалось получить цены утром. Проверьте сайт.")

async def afternoon_check(context: ContextTypes.DEFAULT_TYPE):
    chat_id = load_chat_id()
    if not chat_id:
        logger.warning("Нет сохранённого chat_id, дневной отчёт не отправлен.")
        return
    old_prices = load_last_prices()
    new_prices = fetch_prices()
    if not new_prices:
        await context.bot.send_message(chat_id=chat_id, text="Не удалось получить свежие цены после 13:00.")
        return
    save_prices(new_prices)
    changes = []
    for product, new_price in new_prices.items():
        old_price = old_prices.get(product)
        if old_price is not None and old_price != new_price:
            diff = new_price - old_price
            arrow = "🔺" if diff > 0 else "🔻"
            changes.append(f"{product}: {old_price} ₽ → {new_price} ₽ {arrow} ({diff:+.2f})")
        elif old_price is None:
            changes.append(f"{product}: появилась цена {new_price} ₽ (новая позиция)")
    for product in old_prices:
        if product not in new_prices:
            changes.append(f"{product}: пропала из списка")
    if changes:
        text = "📊 Изменения цен после биржевых торгов (13:00 МСК):\n" + "\n".join(changes)
    else:
        text = "✅ Цены на нефтепродукты не изменились после биржевых торгов."
    await context.bot.send_message(chat_id=chat_id, text=text)

# --- Основная функция для запуска бота и планировщика ---
async def run_bot():
    """Запускает Telegram-бота с планировщиком."""
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    # Настройка планировщика задач
    scheduler = BackgroundScheduler(timezone=MOSCOW_TZ)
    scheduler.add_job(
        lambda: asyncio.create_task(morning_report(application.bot, None)),
        CronTrigger(hour=8, minute=0, timezone=MOSCOW_TZ)
    )
    scheduler.add_job(
        lambda: asyncio.create_task(afternoon_check(application.bot, None)),
        CronTrigger(hour=13, minute=5, timezone=MOSCOW_TZ)
    )
    scheduler.start()
    
    # Запуск бота в режиме polling
    logger.info("Бот запущен...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Держим бота активным
    while True:
        await asyncio.sleep(1)

# --- Точка входа ---
if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке для поддержания активности на Render
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем асинхронного бота
    asyncio.run(run_bot())
