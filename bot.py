import asyncio
import logging
import os
import threading
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TOKEN, CRON_SECRET
from storage import load_chat_id, save_chat_id
from parser import fetch_prices

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== FLASK ПРИЛОЖЕНИЕ ДЛЯ HTTP-ЗАПРОСОВ ==========
flask_app = Flask(__name__)

@flask_app.route('/health')
def health():
    """Эндпоинт для Keep‑Alive (cron-job.org стучится сюда каждые 5 минут)"""
    return "OK", 200

@flask_app.route('/morning_report')
def morning_report_trigger():
    """Эндпоинт для утреннего отчёта (вызывается cron-job.org в 8:00 МСК)"""
    secret = request.args.get('secret')
    if secret != CRON_SECRET:
        logger.warning("Unauthorized access to /morning_report")
        return "Unauthorized", 401

    chat_id = load_chat_id()
    if not chat_id:
        logger.warning("Morning report triggered, but no chat_id found")
        return "No chat_id", 200

    # Запускаем отправку в отдельном потоке, чтобы не блокировать Flask
    threading.Thread(target=run_async_report, args=(chat_id, "morning")).start()
    logger.info("Morning report triggered successfully")
    return "OK", 200

@flask_app.route('/afternoon_report')
def afternoon_report_trigger():
    """Эндпоинт для дневного отчёта (вызывается cron-job.org в 13:05 МСК)"""
    secret = request.args.get('secret')
    if secret != CRON_SECRET:
        logger.warning("Unauthorized access to /afternoon_report")
        return "Unauthorized", 401

    chat_id = load_chat_id()
    if not chat_id:
        logger.warning("Afternoon report triggered, but no chat_id found")
        return "No chat_id", 200

    threading.Thread(target=run_async_report, args=(chat_id, "afternoon")).start()
    logger.info("Afternoon report triggered successfully")
    return "OK", 200

def run_async_report(chat_id, report_type):
    """Вспомогательная функция для запуска асинхронной отправки"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_report(chat_id, report_type))

async def send_report(chat_id, report_type):
    """Функция, которая получает цены и отправляет сообщение"""
    bot = Bot(token=TOKEN)
    prices = fetch_prices()

    if prices:
        title = "🌅 Утренние цены" if report_type == "morning" else "📊 Дневные цены"
        text = f"{title} на нефтепродукты:\n"
        for product, price in prices.items():
            text += f"• {product}: {price} ₽\n"
        await bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"{report_type.capitalize()} report sent to {chat_id}")
    else:
        text = "Не удалось получить цены. Проверьте сайт или настройки авторизации."
        await bot.send_message(chat_id=chat_id, text=text)
        logger.warning(f"Failed to fetch prices for {report_type} report")

def run_flask():
    """Запуск Flask-сервера в отдельном потоке"""
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== ОБРАБОТЧИКИ КОМАНД TELEGRAM ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — сохраняем chat_id и приветствуем"""
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    await update.message.reply_text(
        "Привет! Я бот для отслеживания цен на нефтепродукты.\n\n"
        "Каждое утро в 8:00 и день в 13:05 я буду присылать тебе актуальные цены на АИ‑92 и АИ‑95.\n\n"
        "Также ты можешь в любой момент узнать цены командой /price."
    )
    logger.info(f"User {chat_id} started the bot")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /price — показывает текущие цены прямо сейчас"""
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ Получаю цены, подождите...")
    prices = fetch_prices()
    if prices:
        text = "💰 Текущие цены на нефтепродукты:\n"
        for product, price in prices.items():
            text += f"• {product}: {price} ₽\n"
        await update.message.reply_text(text)
        logger.info(f"Sent /price response to {chat_id}")
    else:
        await update.message.reply_text(
            "❌ Не удалось получить цены. Возможно, сайт временно недоступен или требуется авторизация."
        )
        logger.warning(f"Failed to fetch prices for /price command from {chat_id}")

# ========== ЗАПУСК БОТА ==========
async def run_bot():
    """Запускает Telegram-бота в режиме polling"""
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))

    logger.info("Telegram bot started")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Держим бота активным
    while True:
        await asyncio.sleep(1)

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask server started on port " + os.environ.get('PORT', '10000'))

    # Запускаем асинхронного бота
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
