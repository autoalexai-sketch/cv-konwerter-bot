import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Главная страница (Index)
async def handle_index(request):
    return web.Response(text="BOT ONLINE", content_type='text/html')

async def main():
    app = web.Application()
    # Это лечит 404
    app.router.add_get('/', handle_index)
    
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    # Установка вебхука
    await bot.set_webhook(url=f"{APP_URL}/webhook")

    # ЗАПУСК: Правильный асинхронный метод для Fly.io
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    await site.start()
    print(f"--- SERVER STARTED ON PORT {port} ---")
    
    # Бесконечный цикл, чтобы бот не выключался
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
