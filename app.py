from flask import Flask, render_template, request, send_file
import os
import asyncio
import subprocess
from datetime import datetime
from aiogram import Bot, Dispatcher, types

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Инициализация бота
API_TOKEN = os.getenv("BOT_TOKEN", "8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 1. ГЛАВНАЯ СТРАНИЦА САЙТА
@app.route('/')
def index():
    return render_template('index.html')

# 2. ЭНДПОИНТ ДЛЯ ТЕЛЕГРАМА (WEBHOOK)
@app.route('/webhook', methods=['POST'])
async def telegram_webhook():
    if request.method == "POST":
        update = types.Update.model_validate(request.json, context={"bot": bot})
        await dp.feed_update(bot, update)
        return "OK", 200

# 3. HEALTH CHECK ДЛЯ FLY.IO
@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

# 4. КОНВЕРТАЦИЯ ФАЙЛОВ ЧЕРЕЗ САЙТ
@app.route('/convert', methods=['POST'])
def convert():
    file = request.files.get('file')
    if file and file.filename.endswith(('.docx', '.doc')):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{timestamp}.docx')
        file.save(input_path)
        try:
            subprocess.run([
                'soffice', '--headless', 
                '-env:UserInstallation=file:///tmp/.libreoffice', 
                '--convert-to', 'pdf', 
                '--outdir', app.config['OUTPUT_FOLDER'], 
                input_path
            ], check=True)
            
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{timestamp}.pdf')
            return send_file(output_path, as_attachment=True)
        except Exception as e:
            print(f"Error: {e}")
            return f"Błąd konwersji: {e}", 500
    return "Nieprawidłowy plik", 400

# 5. ОБРАБОТЧИКИ БОТА (из bot.py)
@dp.message()
async def handle_message(message: types.Message):
    # Здесь твой код из bot.py
    if message.text == '/start':
        await message.answer("Cześć! Wyślij mi plik .docx, a ja go skonwertuję na PDF!")
    elif message.document:
        # Обработка файла
        await message.answer("Konwertuję...")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
