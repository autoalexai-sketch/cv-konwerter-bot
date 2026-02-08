import asyncio
import os
import logging
from aiohttp import ClientSession, FormData
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message):
    await message.answer("🇪🇺 Cześć! 👋 Wyślij .docx → PDF!")

@dp.message(F.document)
async def handle_doc(message):
    doc = message.document
    if not doc.file_name or not doc.file_name.lower().endswith('.docx'):
        await message.reply("📄 Tylko .docx!")
        return
    
    await message.reply("⏳ Konwertuję...")
    
    # Скачать файл
    file_info = await bot.get_file(doc.file_id)
    async with ClientSession() as session:
        file_content = await session.get(
            f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        )
        doc_bytes = await file_content.read()
    
    # Сохранить временно
    temp_file = Path(f"/tmp/{doc.file_id}.docx")
    temp_file.write_bytes(doc_bytes)
    
    # Конвертировать
    form_data = FormData()
    form_data.add_field('file', temp_file.read_bytes(), filename=doc.file_name)
    
    async with ClientSession() as session:
        pdf_response = await session.post(
            "https://cv-konwerter-web-docker.onrender.com/convert",
            data=form_data
        )
        pdf_bytes = await pdf_response.read()
    
    # Отправить PDF
    await message.reply_document(
        BufferedInputFile(pdf_bytes, filename="cv.pdf"),
        caption="✅ Gotowe! 📄"
    )
    
    # Удалить временный файл
    temp_file.unlink(missing_ok=True)

async def main():
    logger.info("🚀 Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

