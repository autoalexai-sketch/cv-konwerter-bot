import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- CONFIG ---
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ЭТОТ БЛОК УБИРАЕТ ОШИБКУ 404 ---
async def handle_index(request):
    return web.Response(
        text="<h1>CV Konwerter Bot: Online</h1><p>Status: PL/EN/UA support active.</p>", 
        content_type='text/html'
    )

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🇵🇱 Witaj! Prześlij plik Word.\n🇬🇧 Welcome! Send a Word file.")

# --- ЗАПУСК СЕРВЕРА ---
async def main():
    app = web.Application()
    
    # 1. Сначала добавляем главную страницу (индекс)
    app.router.add_get('/', handle_index)
    
    # 2. Затем добавляем обработчик Telegram (вебхук)
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    # Установка вебхука в Telegram
    await bot.set_webhook(url=f"{APP_URL}/webhook", drop_pending_updates=True)
    
    # 3. Настройка порта для Fly.io
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Fly.io требует слушать 0.0.0.0
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    print(f"Starting server on port {port}...")
    await site.start()
    
    # Держим процесс запущенным
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
