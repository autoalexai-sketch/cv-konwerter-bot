import os
import asyncio
import subprocess
from datetime import datetime
from flask import Flask, render_template, request, send_file
from aiogram import Bot, Dispatcher, types

app = Flask(__name__)
# Используем /tmp для записи, так как в Docker контейнерах Fly.io 
# основная файловая система может быть только для чтения
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/outputs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://cv-konwerter-bot.fly.dev/webhook"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@app.route('/')
def index():
    return "CV Converter Online", 200

@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    # Используем синхронный мост для Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    update = types.Update.model_validate(request.json, context={"bot": bot})
    loop.run_until_complete(dp.feed_update(bot, update))
    return "OK", 200

@dp.message()
async def handle_message(message: types.Message):
    if message.text == '/start':
        await message.answer("Cześć! Wyślij мне файл .docx, и я сделаю из него PDF.")
        return

    if message.document:
        # Проверяем расширение
        if not message.document.file_name.endswith(('.docx', '.doc')):
            await message.answer("Ошибка: Я принимаю только файлы Word (.docx/.doc)")
            return

        status_msg = await message.answer("⏳ Скачиваю файл...")
        
        # Генерируем пути
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{message.document.file_name}")
        output_dir = app.config['OUTPUT_FOLDER']
        
        # 1. Скачиваем файл из Telegram
        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, input_path)
        
        await status_msg.edit_text("⚙️ Конвертирую в PDF (LibreOffice)...")
        
        try:
            # 2. Запускаем конвертацию
            subprocess.run([
                'soffice', '--headless', 
                '-env:UserInstallation=file:///tmp/.libreoffice',
                '--convert-to', 'pdf', 
                '--outdir', output_dir, 
                input_path
            ], check=True)

            output_path = input_path.rsplit('.', 1)[0] + '.pdf'

            # 3. Отправляем результат пользователю
            await status_msg.edit_text("✅ Готово! Отправляю...")
            await message.answer_document(types.FSInputFile(output_path))
            
            # Чистим за собой (опционально)
            os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка при конвертации: {str(e)}")

# Эта функция скажет Телеграму, куда слать данные
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    # Принудительно устанавливаем вебхук перед запуском сервера
    asyncio.run(on_startup())
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
