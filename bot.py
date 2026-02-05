import asyncio
import os
import subprocess
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- CONFIGURATION ---
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"
# Wstaw tutaj swój link z Google Apps Script (ten z /exec)
FEEDBACK_URL = "https://script.google.com/macros/s/AKfycby...ВАШ_ID.../exec"
PRZELEWY24_LINK = "https://secure.przelewy24.pl/..." # Tu wstaw link do płatności

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
            body { font-family: 'Inter', Arial, sans-serif; text-align: center; padding: 50px; background: #f8f9fa; color: #212529; }
            .card { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); display: inline-block; max-width: 450px; border: 1px solid #eee; }
            h1 { color: #0088cc; font-size: 28px; }
            p { font-size: 16px; line-height: 1.5; color: #6c757d; }
            .btn { background: #0088cc; color: white; padding: 16px 32px; text-decoration: none; border-radius: 12px; font-weight: 600; display: inline-block; margin-top: 25px; transition: 0.2s; }
            .btn:hover { background: #0077b5; transform: translateY(-2px); }
            .lang { margin-top: 15px; font-size: 12px; color: #adb5bd; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📄 CV Konwerter Bot</h1>
            <p>Konwertuj swoje CV z Word (DOCX) do PDF w kilka sekund bezpośrednio na Telegramie.</p>
            <p>Bezpiecznie, szybko i profesjonalnie.</p>
            <a href="https://t.me/cv_konwerter_bot" class="btn">🚀 Rozpocznij w Telegram</a>
            <div class="lang">PL | EN | UA | EU Support</div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

# --- KEYBOARDS ---
def get_rating_kb(user_id):
    buttons = [
        [
            InlineKeyboardButton(text="⭐️ 5", url=f"{FEEDBACK_URL}?rating=5&user={user_id}"),
            InlineKeyboardButton(text="⭐️ 4", url=f"{FEEDBACK_URL}?rating=4&user={user_id}")
        ],
        [
            InlineKeyboardButton(text="⭐️ 3", url=f"{FEEDBACK_URL}?rating=3&user={user_id}"),
            InlineKeyboardButton(text="⭐️ 2", url=f"{FEEDBACK_URL}?rating=2&user={user_id}"),
            InlineKeyboardButton(text="⭐️ 1", url=f"{FEEDBACK_URL}?rating=1&user={user_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "👋 **Witaj! / Welcome! / Віitamy!**\n\n"
        "🇵🇱 Wyślij mi swoje CV w formacie Word (.docx), a ja zmienię je w PDF.\n"
        "🇬🇧 Send me your Word CV (.docx) and I will convert it to PDF.\n"
        "🇺🇦 Надішліть мені своє резюме у форматі Word (.docx), і я перетворю його на PDF.\n\n"
        "💎 Premium: /premium"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.document)
async def handle_docs(message: Message):
    if not message.document.file_name.lower().endswith(('.doc', '.docx')):
        await message.answer("❌ Proszę wysłać plik .docx / Please send a .docx file")
        return

    wait_msg = await message.answer("⏳ Przetwarzanie... / Processing... / Обробка...")
    
    input_path = f"cv_{message.from_user.id}.docx"
    output_path = f"cv_{message.from_user.id}.pdf"

    try:
        file = await bot.get_file(message.document.file_id)
        await bot.download_file(file.file_path, input_path)
        
        # Real conversion using LibreOffice
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', input_path], check=True)
        
        pdf = FSInputFile(output_path)
        caption = (
            "✅ **Gotowe! / Done! / Готово!**\n\n"
            "🇵🇱 Oceń jakość konwersji:\n"
            "🇬🇧 Rate the conversion quality:\n"
            "🇺🇦 Оцініть якість конвертації:"
        )
        await message.answer_document(
            document=pdf, 
            caption=caption, 
            reply_markup=get_rating_kb(message.from_user.id),
            parse_mode="Markdown"
        )
    except Exception:
        await message.answer("❌ Error / Błąd / Помилка")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        await wait_msg.delete()

@dp.message(Command("premium"))
async def cmd_premium(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Kup Premium (9.99 PLN)", url=PRZELEWY24_LINK)]
    ])
    await message.answer("💎 **Premium Access**\n\nPL: Odblokuj profesjonalne szablony CV.\nEN: Unlock professional CV templates.", reply_markup=kb)

# --- SERVER ENGINE ---
async def main():
    app = web.Application()
    app.router.add_get('/', handle_index) # Aktywuje stronę WWW
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=f"{APP_URL}/webhook")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
