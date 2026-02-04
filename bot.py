import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- НАСТРОЙКИ ---
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev" 
TABLE_URL = "https://docs.google.com/spreadsheets/d/1X_8Yc5V6L_Dk9S-fSInC9M2-r5vR9R5vR9R5vR9R5vR/edit" # Ваша ссылка

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРА С РЕЙТИНГОМ ---
def get_rating_kb():
    buttons = [
        [InlineKeyboardButton(text="⭐️ 5", url=TABLE_URL), InlineKeyboardButton(text="⭐️ 4", url=TABLE_URL)],
        [InlineKeyboardButton(text="⭐️ 3", url=TABLE_URL), InlineKeyboardButton(text="⭐️ 2", url=TABLE_URL), InlineKeyboardButton(text="⭐️ 1", url=TABLE_URL)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("👋 Привет! Пришли мне CV в формате Word, и я сконвертирую его в PDF.")

@dp.message()
async def handle_docs(message: Message):
    if message.document:
        # Имитируем работу и выдаем кнопки рейтинга
        await message.answer("✅ **Done!**\n\nПожалуйста, оцените качество конвертации:", 
                             reply_markup=get_rating_kb(), 
                             parse_mode="Markdown")

# --- ЗАПУСК WEBHOOK (Fly.io) ---
async def main():
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=f"{APP_URL}/webhook")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()
    print("Бот запущен на Fly.io!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
