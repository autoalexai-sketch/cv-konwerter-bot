import os
import asyncio
import subprocess
import shutil
from datetime import datetime
from flask import Flask, render_template, request, send_file
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Используем /tmp, так как на Fly.io это обычно доступная для записи область
BASE_TMP = "/tmp/cv_bot"
UPLOAD_FOLDER = os.path.join(BASE_TMP, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_TMP, 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ЛОГИКА БОТА ---

@dp.message()
async def handle_message(message: types.Message):
    if message.text == '/start':
        await message.answer("Cześć! Отправь мне .docx, и я сделаю из него PDF.")
        return

    if message.document:
        if not message.document.file_name.lower().endswith(('.docx', '.doc')):
            await message.answer("❌ Ошибка: Нужен файл Word (.docx/.doc)")
            return

        status_msg = await message.answer("⏳ Обработка...")
        
        # Безопасное имя файла
        orig_name = secure_filename(message.document.file_name)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        input_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{orig_name}")
        
        # Скачивание
        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, input_path)
        
        try:
            # Конвертация
            subprocess.run([
                'soffice', '--headless', 
                '-env:UserInstallation=file:///tmp/.libreoffice',
                '--convert-to', 'pdf', 
                '--outdir', OUTPUT_FOLDER, 
                input_path
            ], check=True, timeout=30)

            # Ищем готовый PDF (LibreOffice меняет расширение)
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(OUTPUT_FOLDER, f"{base_name}.pdf")

            if os.path.exists(output_path):
                await message.answer_document(FSInputFile(output_path), caption="✅ Твой PDF готов!")
                await status_msg.delete()
                # Удаляем файлы сразу после отправки
                os.remove(input_path)
                os.remove(output_path)
            else:
                raise Exception("Файл PDF не был создан")

        except Exception as e:
            print(f"Error: {e}")
            await message.answer(f"❌ Ошибка конвертации. Попробуй другой файл.")

# --- FLASK ROUTES ---

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    update = types.Update.model_validate(request.json, context={"bot": bot})
    # Запускаем обработку в фоновом цикле событий
    asyncio.run(dp.feed_update(bot, update))
    return "OK", 200

@app.route('/health')
def health():
    return "OK", 200

@app.route('/')
def index():
    return "CV Converter Bot is Running", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
