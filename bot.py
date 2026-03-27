import asyncio;
import  logging;
from telegram import Bot;
from telegram.ext import Application,CommandHandler,ContextTypes;
from config import MOSCOW_TZ,TOKEN;

from parser import fetch_prices;
from storage import load_last_prices,save_prices,load_chat_id,save_chat_id;
from scheduler import setup_scheduler;

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger= logging.getLogger(__name__);

async def start (update,context):
    chat_id = update.effective_chat.id;
    save_chat_id(chat_id);
    await update.message.reply_text (
        "Привет,АРА! Я буду присылать тебе цены на нефтепродукты каждый день в 8.00 и отчет об изменениях в 13.05 (каждый день по МСК)"
        )
    
async def morning_report (bot,context):
    chat_id = load_chat_id
    if not chat_id:
        logger.warning('Утренний отчет не отправлен')
        return
    prices = fetch_prices();

    if prices:
        save_prices(prices)

        text = 'Доброе утро! Текущие цены на нефтепродукты: \n';
        for product, price in price.items:
            text+=f"{product}: {price}Р \n";

        await bot.send.message (chat_id = chat_id, text = text);
    else:
        await bot.send.message ("Не удалось получить цены утром. Проверьте сайт.")

async def afternoon_check(bot: Bot, context: ContextTypes.DEFAULT_TYPE):
    """Сравнивает текущие цены с утренними и отправляет отчёт об изменениях."""
    chat_id = load_chat_id()
    if not chat_id:
        logger.warning("Нет сохранённого chat_id, дневной отчёт не отправлен.")
        return

    old_prices = load_last_prices()   # цены, сохранённые утром
    new_prices = fetch_prices()

    if not new_prices:
        await bot.send_message(chat_id=chat_id, text="Не удалось получить свежие цены после 13:00.")
        return

    # Сохраняем новые цены (перезаписываем старые)
    save_prices(new_prices)

    # Сравниваем
    changes = []
    for product, new_price in new_prices.items():
        old_price = old_prices.get(product)
        if old_price is not None and old_price != new_price:
            diff = new_price - old_price
            arrow = "🔺" if diff > 0 else "🔻"
            changes.append(f"{product}: {old_price} ₽ → {new_price} ₽ {arrow} ({diff:+.2f})")
        elif old_price is None:
            changes.append(f"{product}: появилась цена {new_price} ₽ (новая позиция)")

    # Проверяем, не исчезли ли какие-то продукты (если в старом списке были, а в новом нет)
    for product in old_prices:
        if product not in new_prices:
            changes.append(f"{product}: пропала из списка")

    if changes:
        text = "📊 Изменения цен после биржевых торгов (13:00 МСК):\n" + "\n".join(changes)
    else:
        text = "✅ Цены на нефтепродукты не изменились после биржевых торгов."

    await bot.send_message(chat_id=chat_id, text=text)

# --- Действия после инициализации приложения ---
async def post_init(application: Application):
    """Запускает планировщик после старта бота."""
    loop = asyncio.get_event_loop()
    setup_scheduler(application, loop)

# --- Точка входа ---
def main():
    # Создаём приложение
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    # Добавляем обработчик команды /start
    app.add_handler(CommandHandler("start", start))

    # Запускаем бота (polling – постоянный опрос сервера Telegram)
    logger.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
