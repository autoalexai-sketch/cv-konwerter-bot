import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"
P24_LINK = "https://secure.przelewy24.pl/your_actual_link" # ВСТАВЬ СВОЮ ССЫЛКУ

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ЛОГИКА БОТА ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Cześć! Wyślij mi swoje CV (PDF/DOCX), а я помогу перевести его или подготовить к оплате.\n"
        "🇬🇧 Send me your CV to translate it.\n"
        "💳 Оплата / Płatność: /pay"
    )

@dp.message(Command("pay"))
async def cmd_pay(message: types.Message):
    await message.answer(f"🔗 Link do płatności Przelewy24:\n{P24_LINK}")

# Функция перевода (заглушка для логики перевода)
@dp.message(F.document)
async def handle_docs(message: types.Message):
    await message.answer("📄 Документ получен! Начинаю перевод на польский/английский... (процесс запущен)")
    # Здесь будет логика обработки файла (библиотека python-docx и т.д.)

# --- ВЕБ-ИНТЕРФЕЙС (САЙТ) ---

async def handle_index(request):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CV Konwerter Bot</title>
        <style>
            body { font-family: sans-serif; text-align: center; padding-top: 50px; background: #f4f4f9; }
            .card { background: white; padding: 20px; border-radius: 10px; display: inline-block; shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; }
            p { color: #7f8c8d; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🤖 CV Konwerter Bot</h1>
            <p>Статус: <span style="color: green;">Online</span></p>
            <p>Бот готов к работе на европейском рынке.</p>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

# --- ЗАПУСК ---

async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    await bot.set_webhook(url=f"{APP_URL}/webhook", drop_pending_updates=True)

    # ВАЖНО: Фикс для Fly.io (явное указание хоста 0.0.0.0)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port) 
    await site.start()
    
    print(f"✅ Сервер запущен на порту {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
