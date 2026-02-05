import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- НАСТРОЙКИ ---
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"
# Твоя ссылка Przelewy24 (вставь актуальную)
P24_LINK = "https://secure.przelewy24.pl/your_link_here" 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Приветствие на трех языках
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "Cześć! Wyślij mi swoje CV, aby zacząć. 🇵🇱\n"
        "Hello! Send me your CV to get started. 🇬🇧\n"
        "Привіт! Надішліть своє CV, щоб почати. 🇺🇦\n\n"
        "Payment / Płatność / Оплата: /pay"
    )
    await message.answer(text)

# Команда оплаты
@dp.message(Command("pay"))
async def cmd_pay(message: types.Message):
    text = (
        "To proceed with the payment, use the link below:\n"
        "Aby przejść do płatności, skorzystaj z linku:\n\n"
        f"{P24_LINK}"
    )
    await message.answer(text)

# Главная страница для проверки (Health Check)
async def handle_index(request):
    return web.Response(text="BOT ONLINE", content_type='text/html')

async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    await bot.set_webhook(url=f"{APP_URL}/webhook", drop_pending_updates=True)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    print(f"--- SERVER STARTED ON PORT {port} ---")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
