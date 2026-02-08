import asyncio
import os
import time
import re
import logging
from pathlib import Path
from aiohttp import ClientSession, FormData, ClientTimeout
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

# Логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
    exit(1)

WEB_APP_URL = os.getenv("WEB_APP_URL", "https://cv-konwerter-web-docker.onrender.com")
FILE_SIZE_LIMIT = 15 * 1024 * 1024  # 15MB

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Rate limit
user_limits = {}
RATE_LIMIT_COUNT = 5
RATE_LIMIT_WINDOW = 60

temp_dir = Path("/tmp/cv_bot")
temp_dir.mkdir(exist_ok=True)

MESSAGES = {
    'start': "🇪🇺 Cześć! 👋 Wyślij .doc/.docx → PDF gotowy!\nℹ️ /help - pomoc",
    'processing': "⏳ Konwertuję...",
    'success': "✅ Gotowe! 📄",
    'rate_limit': "⚠️ Za dużo plików. Poczekaj minutę.",
    'wrong_format': "📄 Tylko .doc/.docx",
    'file_too_big': "📄 Plik za duży (max 15MB)",
    'error': "😅 Błąd. Spróbuj ponownie."
}

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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(MESSAGES['start'])

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("📄 Wyślij .doc lub .docx → PDF gotowy w sekundy!")

@dp.message(F.document)
async def handle_docs(message: types.Message):
    user_id = message.from_user.id
    
    # Rate limit
    if not check_user_limit(user_id):
        await message.reply(MESSAGES['rate_limit'])
        return
    
    doc = message.document
    
    # Проверка формата
    if not doc.file_name or not doc.file_name.lower().endswith(('.doc', '.docx')):
        await message.reply(MESSAGES['wrong_format'])
        return
    
    # Проверка размера
    if doc.file_size and doc.file_size > FILE_SIZE_LIMIT:
        await message.reply(MESSAGES['file_too_big'])
        return
    
    processing_msg = await message.reply(MESSAGES['processing'])
    input_path = None
    
    try:
        # Скачиваем файл
        file = await bot.get_file(doc.file_id)
        file_path = file.file_path
        
        async with ClientSession(timeout=ClientTimeout(total=30)) as session:
            async with session.get(f"https://api.telegram.org/file/bot{API_TOKEN}/{file_path}") as resp:
                content = await resp.read()
                safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', doc.file_name)[:100]
                input_path = temp_dir / f"{user_id}_{int(time.time())}_{safe_filename}"
                input_path.write_bytes(content)
        
        # Конвертируем
        async with ClientSession(timeout=ClientTimeout(total=60)) as session:
            data = FormData()
            data.add_field('file', open(input_path, 'rb'), filename=safe_filename)
            
            async with session.post(
                f"{WEB_APP_URL}/convert", 
                data=data,
                timeout=ClientTimeout(total=60)
            ) as resp:
                pdf_content = await resp.read()
        
        # Отправляем PDF
        await processing_msg.delete()
        await message.answer_document(
            BufferedInputFile(pdf_content, filename=f"cv_{int(time.time())}.pdf"),
            caption=MESSAGES['success']
        )
        
    except Exception as e:
        logger.error(f"Error user {user_id}: {e}")
        await processing_msg.edit_text(MESSAGES['error'])
    finally:
        if input_path and input_path.exists():
            input_path.unlink()

async def main():
    logger.info("🚀 Bot starting - 100% POLLING MODE!")
    logger.info("✅ NO WEBHOOK!")
    
    # ЧИСТЫЙ POLLING - БЕЗ WEBHOOK
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

