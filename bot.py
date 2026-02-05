import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- CONFIGURATION ---
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"
# URL z Google Apps Script (z Twoim ID)
FEEDBACK_URL = "https://script.google.com/macros/s/AKfycbxUki3AIpxF6AeCZc4XgmZ7CbUcIU8cA96S0AZsVJ6umlgJz-wz6pKNa2v3Q9-ttr2z/exec"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- LANDING PAGE (WWW) ---
async def handle_index(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CV Konwerter Bot</title>
        <style>
            body { font-family: 'Inter', sans-serif; text-align: center; padding: 50px; background: #f8f9fa; }
            .card { background: white; padding: 40px; border-radius: 20px; shadow: 0 10px 30px rgba(0,0,0,0.1); display: inline-block; }
            .btn { background: #0088cc; color: white; padding: 15px 30px; text-decoration: none; border-radius: 12px; font-weight: bold; display: inline-block; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📄 CV Konwerter Bot</h1>
            <p>Konwertuj pliki Word do PDF bezpośrednio w Telegramie.</p>
            <a href="https://t.me/cv_konwerter_bot" class="btn">🚀 Otwórz w Telegram</a>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

# --- BOT LOGIC (MULTILANGUAGE) ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "👋 **Witaj! / Welcome! / Вітаємо!**\n\n"
        "🇵🇱 Wyślij mi plik .docx, aby otrzymać PDF.\n"
        "🇬🇧 Send me a .docx file to get a PDF.\n"
        "🇺🇦 Надішліть файл .docx, щоб отримати PDF."
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.document)
async def handle_docs(message: Message):
    # Tutaj logika konwersji...
    await message.answer("✅ Done! / Gotowe! / Готово!")

# --- SERVER ENGINE ---
async def main():
    app = web.Application()
    # To naprawia błąd 404 - dodaje stronę główną
    app.router.add_get('/', handle_index)
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    await bot.set_webhook(url=f"{APP_URL}/webhook")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
