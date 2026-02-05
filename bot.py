import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- CONFIG ---
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"
FEEDBACK_URL = "https://script.google.com/macros/s/AKfycbxUki3AIpxF6AeCZc4XgmZ7CbUcIU8cA96S0AZsVJ6umlgJz-wz6pKNa2v3Q9-ttr2z/exec"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- WEB HANDLERS ---
async def handle_index(request):
    # Этот ответ увидит Fly.io при проверке (Health Check)
    return web.Response(text="<h1>CV Bot is Running</h1>", content_type='text/html')

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🇵🇱 Witaj! Wyślij mi plik Word.\n🇬🇧 Welcome! Send me a Word file.")

# --- SERVER STARTUP ---
async def on_startup(bot: Bot):
    await bot.set_webhook(f"{APP_URL}/webhook")

def main():
    app = web.Application()
    
    # Регистрация путей
    app.router.add_get("/", handle_index)
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    # Принудительно слушаем 0.0.0.0 и порт 8080
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
