import asyncio
import os
import time
import re
import logging
from pathlib import Path
from aiohttp import web, ClientSession, FormData, ClientTimeout
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import BufferedInputFile

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Конфигурация
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не задан!")
    exit(1)

APP_URL = os.getenv("APP_URL", "https://cv-konwerter-bot.fly.dev")
P24_LINK = os.getenv("P24_LINK", "https://przelewy24.pl/payment/YOUR_LINK_HERE")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://cv-konwerter-web-docker.onrender.com")
FILE_SIZE_LIMIT = int(os.getenv("FILE_SIZE_LIMIT", "15")) * 1024 * 1024
RATE_LIMIT_COUNT = int(os.getenv("RATE_LIMIT_COUNT", "5"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Защита от спама
user_limits = {}

# Временная папка
temp_dir = Path("/tmp/cv_bot")
temp_dir.mkdir(parents=True, exist_ok=True)

# Мультиязычные тексты
MESSAGES = {
    'pl': {
        'start': "🇪🇺 Cześć! 👋 Konwertuję CV z Word → idealny PDF\n\n📄 Wyślij plik .doc lub .docx → PDF gotowy w kilka sekund\n\nℹ️ /help - pomoc",
        'processing': "⏳ Konwertuję do PDF...",
        'success': "✅ Gotowe! Twój PDF 📄",
        'rate_limit': "⚠️ Zbyt wiele plików. Spróbuj ponownie za minutę.",
        'wrong_format': "📄 Tylko pliki .doc lub .docx.",
        'file_too_big': "📄 Plik zbyt duży (maks. {limit} MB).",
        'error': "😅 Błąd konwersji. Spróbuj ponownie."
    },
    'en': {
        'start': "🇪🇺 Hi! 👋 Converting CV from Word → PDF\n\n📄 Send .doc or .docx → PDF ready in seconds\n\nℹ️ /help - help",
        'processing': "⏳ Converting to PDF...",
        'success': "✅ Done! Your PDF 📄",
        'rate_limit': "⚠️ Too many files. Try again in a minute.",
        'wrong_format': "📄 Only .doc or .docx files please.",
        'file_too_big': "📄 File too big (max {limit} MB).",
        'error': "😅 Conversion failed. Try again."
    }
}

def get_message(key: str, lang: str = 'en', **kwargs) -> str:
    lang = lang[:2]
    msg = MESSAGES.get(lang, MESSAGES['en']).get(key, key)
    return msg.format(**kwargs)

def sanitize_filename(filename: str) -> str:
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return safe_name[:100] or "file"

def check_user_limit(user_id: int) -> bool:
    now = time.time()
    if user_id not in user_limits:
        user_limits[user_id] = (now, 1)
        return True
    
    last_time, count = user_limits[user_id]
    if now - last_time > RATE_LIMIT_WINDOW:
        user_limits[user_id] = (now, 1)
        return True
    
    if count >= RATE_LIMIT_COUNT:
        return False
    
    user_limits[user_id] = (last_time, count + 1)
    return True

# Команды
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = message.from_user.language_code or 'en'
    await message.answer(get_message('start', lang))

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    lang = message.from_user.language_code or 'en'
    await message.answer("ℹ️ Send .doc or .docx → Get PDF\nFiles auto-deleted after 24h")

# Обработка файлов
@dp.message(F.document)
async def handle_docs(message: types.Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code or 'en'
    
    if not check_user_limit(user_id):
        await message.reply(get_message('rate_limit', lang))
        return
    
    doc = message.document
    
    if not doc.file_name or not doc.file_name.lower().endswith(('.doc', '.docx')):
        await message.reply(get_message('wrong_format', lang))
        return
    
    if doc.file_size and doc.file_size > FILE_SIZE_LIMIT:
        mb_limit = FILE_SIZE_LIMIT / (1024 * 1024)
        await message.reply(get_message('file_too_big', lang, limit=mb_limit))
        return
    
    processing_msg = await message.reply(get_message('processing', lang))
    input_path = None
    
    try:
        file = await bot.get_file(doc.file_id)
        file_path = file.file_path
        
async with ClientSession(timeout=ClientTimeout(total=60)) as session:
    data = FormData()
    with open(input_path, 'rb') as f:
        data.add_field('file', f.read(), filename=safe_filename, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    
    async with session.post(f"{WEB_APP_URL}/convert", data=data, timeout=ClientTimeout(total=60)) as resp:
        if resp.status != 200:
            raise Exception(f"PDF service error: {resp.status}")
        pdf_content = await resp.read()
      
        await processing_msg.delete()
        await message.answer_document(
            BufferedInputFile(pdf_content, filename=f"cv_{int(time.time())}.pdf"),
            caption=get_message('success', lang)
        )
        
    except Exception as e:
        logger.error(f"Error for user {user_id}: {e}")
        await processing_msg.edit_text(get_message('error', lang))
    finally:
        if input_path and input_path.exists():
            input_path.unlink()

# Health check для Fly.io
async def handle_health(request):
    return web.Response(text="OK", status=200)

async def handle_index(request):
    return web.Response(text="CV Konwerter Bot OK")

# Главная функция - POLLING MODE
async def main():
    logger.info("🚀 Bot starting - POLLING MODE!")
    logger.info("⚠️ WEBHOOK ОТКЛЮЧЁН!")
    
    # Запуск минимального web-сервера для health checks Fly.io
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/health', handle_health)
    
    # Запуск polling в фоне + web-сервер
    await asyncio.gather(
        dp.start_polling(bot),
        web._run_app(app, host='0.0.0.0', port=8080)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown")
