import asyncio
import logging
import os
import threading
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TOKEN, CRON_SECRET
from storage import add_subscriber, remove_subscriber, get_all_subscribers
from parser import fetch_prices

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== FLASK ПРИЛОЖЕНИЕ ==========
flask_app = Flask(__name__)

@flask_app.route('/health')
def health():
    return "OK", 200

@flask_app.route('/morning_report')
def morning_report_trigger():
    secret = request.args.get('secret')
    if secret != CRON_SECRET:
        logger.warning("Unauthorized access to /morning_report")
        return "Unauthorized", 401
    
    # Запускаем отправку всем подписчикам в отдельном потоке
    threading.Thread(target=run_async_report_to_all, args=("morning",)).start()
    logger.info("Morning report triggered")
    return "OK", 200

@flask_app.route('/afternoon_report')
def afternoon_report_trigger():
    secret = request.args.get('secret')
    if secret != CRON_SECRET:
        logger.warning("Unauthorized access to /afternoon_report")
        return "Unauthorized", 401
    
    threading.Thread(target=run_async_report_to_all, args=("afternoon",)).start()
    logger.info("Afternoon report triggered")
    return "OK", 200

def run_async_report_to_all(report_type):
    """Запускает асинхронную рассылку всем подписчикам"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_report_to_all(report_type))

async def send_report_to_all(report_type):
    """Отправляет отчёт всем подписчикам"""
    subscribers = get_all_subscribers()
    if not subscribers:
        logger.warning("Нет подписчиков, отчёт не отправлен")
        return
    
    prices = fetch_prices()
    if prices:
        title = "🌅 Утренние цены" if report_type == "morning" else "📊 Дневные цены"
        text = f"{title} на нефтепродукты:\n"
        for product, price in prices.items():
            text += f"• {product}: {price} ₽\n"
    else:
        text = "Не удалось получить цены. Проверьте сайт или настройки авторизации."
    
    bot = Bot(token=TOKEN)
    for chat_id in subscribers:
        try:
            await bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"Отчёт отправлен пользователю {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {chat_id}: {e}")

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== ОБРАБОТЧИКИ КОМАНД TELEGRAM ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — подписка на уведомления"""
    chat_id = update.effective_chat.id
    if add_subscriber(chat_id):
        await update.message.reply_text(
            "✅ Вы подписались на уведомления о ценах!\n\n"
            "Каждое утро в 8:00 и день в 13:05 я буду присылать актуальные цены.\n"
            "Чтобы отписаться, используйте команду /stop"
        )
    else:
        await update.message.reply_text("ℹ️ Вы уже подписаны на уведомления.")
    logger.info(f"User {chat_id} subscribed")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stop — отписка от уведомлений"""
    chat_id = update.effective_chat.id
    if remove_subscriber(chat_id):
        await update.message.reply_text(
            "❌ Вы отписались от уведомлений.\n"
            "Чтобы подписаться снова, напишите /start"
        )
    else:
        await update.message.reply_text("ℹ️ Вы и так не были подписаны.")
    logger.info(f"User {chat_id} unsubscribed")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /price — показать текущие цены"""
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
            "❌ Не удалось получить цены. Возможно, сайт временно недоступен."
        )
        logger.warning(f"Failed to fetch prices for /price command from {chat_id}")

# ========== ЗАПУСК БОТА ==========
async def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("price", price))

    logger.info("Telegram bot started")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    while True:
        await asyncio.sleep(1)

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"Flask server started on port {os.environ.get('PORT', '10000')}")

    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
