import asyncio
import logging
import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TOKEN, MOSCOW_TZ
from storage import load_last_prices, save_prices, load_chat_id, save_chat_id
from parser import fetch_prices
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Bot is running!", 200

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    await update.message.reply_text(
        "Привет! Я буду присылать тебе цены на нефтепродукты каждое утро в 8:00 и "
        "отчёт об изменениях после биржевых торгов (около 13:05 МСК)."
    )

async def morning_report(app):
    print("DEBUG: morning_report started")
    chat_id = load_chat_id()
    print(f"DEBUG: chat_id = {chat_id}")
    if not chat_id:
        print("DEBUG: no chat_id, exiting")
        return
    print("DEBUG: calling fetch_prices()")
    prices = fetch_prices()
    print(f"DEBUG: prices = {prices}")
    if prices:
        save_prices(prices)
        text = "🌅 Доброе утро! Текущие цены на нефтепродукты:\n"
        for product, price in prices.items():
            text += f"• {product}: {price} ₽\n"
        print("DEBUG: sending message with prices")
        await app.bot.send_message(chat_id=chat_id, text=text)
        print("DEBUG: message sent")
    else:
        print("DEBUG: no prices, sending error message")
        await app.bot.send_message(chat_id=chat_id, text="Не удалось получить цены утром. Проверьте сайт.")
        print("DEBUG: error message sent")

async def afternoon_check(app):
    chat_id = load_chat_id()
    if not chat_id:
        logger.warning("Нет сохранённого chat_id, дневной отчёт не отправлен.")
        return
    old_prices = load_last_prices()
    new_prices = fetch_prices()
    if not new_prices:
        await app.bot.send_message(chat_id=chat_id, text="Не удалось получить свежие цены после 13:00.")
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
        text = "📊 Изменения цен после биржевых торгов (13:05 МСК):\n" + "\n".join(changes)
    else:
        text = "✅ Цены на нефтепродукты не изменились после биржевых торгов."
    await app.bot.send_message(chat_id=chat_id, text=text)

async def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # СОЗДАЁМ ПЛАНИРОВЩИК
    scheduler = BackgroundScheduler(timezone=MOSCOW_TZ)
    scheduler.add_job(
        morning_report,
        CronTrigger(hour=8, minute=0, timezone=MOSCOW_TZ),
        args=[application]
    )
    scheduler.add_job(
        afternoon_check,
        CronTrigger(hour=15, minute=40, timezone=MOSCOW_TZ),
        args=[application]
    )
    scheduler.start()

    logger.info("Бот запущен...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    asyncio.run(run_bot())

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    prices = fetch_prices()
    if prices:
        text = "\n".join([f"{p}: {pr} ₽" for p, pr in prices.items()])
    else:
        text = "Не удалось получить цены (требуется авторизация?)"
    await update.message.reply_text(text)

# В run_bot() добавить:
application.add_handler(CommandHandler("price", price))
