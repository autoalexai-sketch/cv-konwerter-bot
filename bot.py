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
    # Регистрируем главную страницу ПЕРВОЙ
    app.router.add_get('/', handle_index)
    
    # Настройка вебхука
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    await bot.set_webhook(url=f"{APP_URL}/webhook")

    # ЗАПУСК: Слушаем на 0.0.0.0 и порту 8080
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    
    print("SERVER STARTED ON PORT 8080")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
