import asyncio
import os
import logging
from aiohttp import ClientSession, FormData, ClientTimeout
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

temp_dir = Path("/tmp")
temp_dir.mkdir(exist_ok=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🇪🇺 Cześć! Wyślij .docx → PDF!")

@dp.message(F.document)
async def doc_handler(message: types.Message):
    doc = message.document
    if not doc.file_name.endswith('.docx'):
        return await message.reply("📄 Tylko .docx!")
    
    await message.reply("⏳ Konwertuję...")
    
    try:
        # Скачать файл
        file = await bot.get_file(doc.file_id)
        async with ClientSession() as session:
            content = await session.get(
                f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
            )
            doc_bytes = await content.read()
        
        # Сохранить временно
        input_file = temp_dir / f"doc_{doc.file_id}.docx"
        input_file.write_bytes(doc_bytes)
        
        # Отправить на конвертер
        form = FormData()
        form.add_field('file', input_file.read_bytes(), filename=doc.file_name)
        
        async with ClientSession() as session:
            resp = await session.post(
                "https://cv-konwerter-web-docker.onrender.com/convert",
                data=form
            )
            pdf_bytes = await resp.read()
        
        # Отправить PDF
        await message.reply_document(
            BufferedInputFile(pdf_bytes, filename="cv.pdf"),
            caption="✅ Gotowe!"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.reply("😅 Błąd!")
    
    finally:
        if input_file.exists():
            input_file.unlink()

async def main():
    logger.info("🚀 Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
