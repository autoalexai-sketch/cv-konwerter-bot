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
# Ваша подтвержденная ссылка (image_a28869)
FEEDBACK_URL = "https://script.google.com/macros/s/AKfycbxUki3AIpxF6AeCZc4XgmZ7CbUcIU8cA96S0AZsVJ6umlgJz-wz6pKNa2v3Q9-ttr2z/exec"
# Ссылка на оплату (замените на вашу актуальную)
PRZELEWY24_LINK = "https://secure.przelewy24.pl/"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- LANDING PAGE / HEALTH CHECK (Убирает 404) ---
async def handle_index(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <title>CV Konwerter Bot</title>
        <style>
            body { font-family: sans-serif; text-align: center; padding: 50px; background: #f8f9fa; }
            .card { background: white; padding: 40px; border-radius: 20px; display: inline-block; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            .btn { background: #0088cc; color: white; padding: 15px 30px; text-decoration: none; border-radius: 10px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📄 CV Konwerter Bot</h1>
            <p>Konwertuj Word do PDF bezpośrednio w Telegramie.</p>
            <a href="https://t.me/cv_konwerter_bot" class="btn">🚀 Otwórz w Telegram</a>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

# --- KEYBOARD FOR RATING (image_a37101) ---
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
        "👋 **Witaj! / Welcome! / Вітаємо!**\n\n"
        "🇵🇱 Wyślij mi plik .docx, aby otrzymać PDF.\n"
        "🇬🇧 Send me a .docx file to get a PDF.\n"
        "🇺🇦 Надішліть файл .docx, щоб отримати PDF.\n\n"
        "💎 Premium: /premium"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.document)
async def handle_docs(message: Message):
    if not message.document.file_name.lower().endswith(('.doc', '.docx')):
        return await message.answer("❌ Proszę wysłać plik .docx")

    wait_msg = await message.answer("⏳ Processing... / Przetwarzanie...")
    input_path = f"file_{message.from_user.id}.docx"
    output_path = f"file_{message.from_user.id}.pdf"

    try:
        file = await bot.get_file(message.document.file_id)
        await bot.download_file(file.file_path, input_path)
        # Реальная конвертация через установленный LibreOffice
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', input_path], check=True)
        
        pdf = FSInputFile(output_path)
        await message.answer_document(
            document=pdf, 
            caption="✅ Done! / Gotowe!\n\nProszę ocenić jakość:", 
            reply_markup=get_rating_kb(message.from_user.id)
        )
    except Exception as e:
        await message.answer(f"❌ Error during conversion.")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        await wait_msg.delete()

@dp.message(Command("premium"))
async def cmd_premium(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Kup Premium (Przelewy24)", url=PRZELEWY24_LINK)]
    ])
    await message.answer("💎 **Premium Access**\n\nOdblokuj profesjonalne szablony CV.", reply_markup=kb)

# --- WEB SERVER ENGINE ---
async def main():
    app = web.Application()
    # Регистрация главной страницы для устранения 404
    app.router.add_get('/', handle_index)
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    await bot.set_webhook(url=f"{APP_URL}/webhook", drop_pending_updates=True)
    
    runner = web.AppRunner(app)
    await runner.setup()
    # КРИТИЧЕСКИ ВАЖНО: 0.0.0.0 и порт из переменной окружения
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    print(f"Server is running on port {port}")
    await site.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
