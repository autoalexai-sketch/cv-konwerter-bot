import os
import asyncio
import subprocess
import unicodedata
import re
from datetime import datetime
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile

app = Flask(__name__)

# Папки для временных файлов
BASE_TMP = "/tmp/cv_bot"
UPLOAD_FOLDER = os.path.join(BASE_TMP, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_TMP, 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def smart_secure_filename(filename):
    """Поддержка Unicode: сохраняет буквы PL, UA, EN и убирает только опасные символы."""
    name, ext = os.path.splitext(filename)
    # NFC нормализация важна для корректного отображения имен в Telegram
    name = unicodedata.normalize('NFC', name)
    # Убираем только спецсимволы, которые запрещены в файловых системах
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip() or "cv_document"
    return f"{name}{ext}"

@dp.message()
async def handle_message(message: types.Message):
    # Команда /start на трех языках
    if message.text == '/start':
        welcome_text = (
            "🇵🇱 Cześć! Wyślij mi plik .docx, а ja go skonwertuję na PDF.\n"
            "🇺🇦 Привіт! Надішліть мені файл .docx, і я конвертую його в PDF.\n"
            "🇬🇧 Hi! Send me a .docx file, and I will convert it to PDF."
        )
        await message.answer(welcome_text)
        return

    if message.document:
        file_name = message.document.file_name
        if not file_name.lower().endswith(('.docx', '.doc')):
            await message.answer("❌ Format error! (PL: Błędny format / UA: Невірний формат)")
            return

        # Уведомление о начале работы
        status_msg = await message.answer("⏳ Processing... (Konwertuję / Конвертую)")
        
        # Генерация пути с поддержкой Unicode
        safe_name = smart_secure_filename(file_name)
        timestamp = datetime.now().strftime('%H%M%S')
        input_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{safe_name}")
        
        try:
            # 1. Скачивание
            file_info = await bot.get_file(message.document.file_id)
            await bot.download_file(file_info.file_path, input_path)
            
            # 2. Конвертация
            subprocess.run([
                'soffice', '--headless', 
                '-env:UserInstallation=file:///tmp/.libreoffice',
                '--convert-to', 'pdf', 
                '--outdir', OUTPUT_FOLDER, 
                input_path
            ], check=True, timeout=40)

            # 3. Отправка
            output_name = os.path.splitext(os.path.basename(input_path))[0] + '.pdf'
            output_path = os.path.join(OUTPUT_FOLDER, output_name)

            if os.path.exists(output_path):
                await message.answer_document(
                    FSInputFile(output_path), 
                    caption=f"✅ Done! (Gotowe / Готово)"
                )
                await status_msg.delete()
                # Удаление временных файлов
                os.remove(input_path)
                os.remove(output_path)
            else:
                raise Exception("Conversion failed")

        except Exception as e:
            print(f"Error during conversion: {e}")
            await message.answer("❌ Error! (Błąd / Помилка)")

# --- СТАНДАРТНЫЕ МАРШРУТЫ FLASK ---
@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    update = types.Update.model_validate(request.json, context={"bot": bot})
    asyncio.run(dp.feed_update(bot, update))
    return "OK", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
