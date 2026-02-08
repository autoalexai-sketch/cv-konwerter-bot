import asyncio
import os
import logging
from aiohttp import ClientSession, FormData
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
    exit(1)

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
    
    try:
        # 1. Скачать .docx с TELEGRAM
        file_info = await bot.get_file(doc.file_id)
        async with ClientSession() as session:
            async with session.get(
                f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
            ) as file_resp:
                if file_resp.status != 200:
                    await message.reply("❌ Błąd pobierania pliku!")
                    return
                doc_bytes = await file_resp.read()
        
        # 2. Сохранить во временный файл (БИНАРНЫЙ РЕЖИМ!)
        temp_docx = f"/tmp/{doc.file_id}.docx"
        with open(temp_docx, "wb") as f:
            f.write(doc_bytes)
        
        # 3. Отправить на Render.com с ПРАВИЛЬНЫМИ HEADERS
        form = FormData()
        with open(temp_docx, "rb") as f:
            form.add_field(
                'file',
                f,
                filename=doc.file_name,
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        
        async with ClientSession() as session:
            async with session.post(
                "https://cv-konwerter-web-docker.onrender.com/convert",
                data=form
            ) as pdf_resp:
                if pdf_resp.status != 200:
                    await message.reply(f"❌ Błąd konwersji: HTTP {pdf_resp.status}")
                    logger.error(f"Render.com error: {pdf_resp.status}")
                    return
                
                pdf_bytes = await pdf_resp.read()
        
        # 4. Отправить РАБОЧИЙ PDF
        await message.reply_document(
            BufferedInputFile(pdf_bytes, filename="cv.pdf"),
            caption="✅ Gotowe! 📄"
        )
        
        logger.info(f"✅ Konwersja OK: {doc.file_name} → cv.pdf")
    
    except Exception as e:
        logger.error(f"❌ DEBUG ERROR: {e}")
        logger.error(f"📊 PDF Response status: {pdf_resp.status}")
        logger.error(f"📊 PDF Response headers: {pdf_resp.headers}")
        logger.error(f"📊 Doc size: {len(doc_bytes)} bytes")
        await message.reply("❌ Wystąpił błąd konwersji!")
    
    finally:
        # 5. Удалить временный файл
        if os.path.exists(temp_docx):
            os.unlink(temp_docx)

async def main():
    logger.info("🚀 Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
