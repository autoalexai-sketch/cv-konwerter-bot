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
# Twoja sprawdzona linka do tabeli (z końcówką /exec)
FEEDBACK_URL = "https://script.google.com/macros/s/AKfycbxUki3AIpxF6AeCZc4XgmZ7CbUcIU8cA96S0AZsVJ6umlgJz-wz6pKNa2v3Q9-ttr2z/exec"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- LANDING PAGE (Naprawia błąd 404) ---
async def handle_index(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CV Konwerter Bot</title>
        <style>
            body { font-family: sans-serif; text-align: center; padding: 50px; background: #f8f9fa; }
            .card { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); display: inline-block; }
            .btn { background: #0088cc; color: white; padding: 15px 30px; text-decoration: none; border-radius: 12px; font-weight: bold; display: inline-block; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📄 CV Konwerter Bot</h1>
            <p>Konwertuj Word do PDF w Telegramie (PL/EN/UA)</p>
            <a href="https://t.me/cv_konwerter_bot" class="btn">🚀 Otwórz w Telegram</a>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

# --- КЛАВИАТУРА С РЕЙТИНГОМ (Для таблицы) ---
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
    await message.answer(
        "👋 **Witaj! / Welcome! / Вітаємо!**\n\n"
        "🇵🇱 Wyślij mi plik .docx, aby otrzymać PDF.\n"
        "🇬🇧 Send me a .docx file to get a PDF.\n"
        "🇺🇦 Надішліть файл .docx, щоб отримати PDF.",
        parse_mode="Markdown"
    )

@dp.message(F.document)
async def handle_docs(message: Message):
    if not message.document.file_name.lower().endswith(('.doc', '.docx')):
        return await message.answer("❌ Proszę wysłać plik Word (.docx)")

    wait_msg = await message.answer("⏳ Processing...")
    
    input_path = f"file_{message.from_user.id}.docx"
    output_path = f"file_{message.from_user.id}.pdf"

    try:
        file = await bot.get_file(message.document.file_id)
        await bot.download_file(file.file_path, input_path)
        
        # Konwertujemy plik (wymaga LibreOffice na serwerze)
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', input_path], check=True)
        
        pdf = FSInputFile(output_path)
        await message.answer_document(
            document=pdf, 
            caption="✅ Done! Oceń jakość:", 
            reply_markup=get_rating_kb(message.from_user.id)
        )
    except Exception:
        await message.answer("❌ Error during conversion.")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        await wait_msg.delete()

# --- ENGINE (Исправляет ошибку порта на Fly.io) ---
async def main():
    app = web.Application()
    
    # Сначала регистрируем главную страницу
    app.router.add_get('/', handle_index)
    
    # Затем регистрируем вебхук
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    # Удаляем старый вебхук и ставим новый
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=f"{APP_URL}/webhook")
    
    # Запуск сервера
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Важно: используем порт из окружения Fly.io
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    print(f"Server starting on port {port}...")
    await site.start()
    
    # Бесконечный цикл ожидания
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
