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
        await message.answer("Cześć! Wyślij mi файл .docx!")
    else:
        await message.answer("Otrzymałem wiadomość!")

# Эта функция скажет Телеграму, куда слать данные
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    # Принудительно устанавливаем вебхук перед запуском сервера
    asyncio.run(on_startup())
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
