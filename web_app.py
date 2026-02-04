
import os
import asyncio
import subprocess
import unicodedata
import re
import requests
from datetime import datetime
from flask import Flask, request
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

app = Flask(__name__)

# --- НАСТРОЙКИ ---
API_TOKEN = os.getenv("BOT_TOKEN")
# ВСТАВЬТЕ СЮДА ССЫЛКУ ИЗ GOOGLE APPS SCRIPT
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbwzJ0NbWy07Sgc9BpzxtbW0uWL4fnHG34Wk0PimHlX6jwTV1lBzhRf1avmFwGZ5bxfy/exec"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

BASE_TMP = "/tmp/cv_bot"
os.makedirs(os.path.join(BASE_TMP, 'uploads'), exist_ok=True)
os.makedirs(os.path.join(BASE_TMP, 'outputs'), exist_ok=True)

def smart_name(filename):
    name, ext = os.path.splitext(filename)
    name = unicodedata.normalize('NFC', name)
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return f"{name.strip() or 'cv'}{ext}"

# Клавиатура с оценками
def get_rating_keyboard(filename):
    buttons = [
        [InlineKeyboardButton(text="⭐️ 5", callback_data=f"rate_5_{filename}"),
         InlineKeyboardButton(text="⭐️ 4", callback_data=f"rate_4_{filename}")],
        [InlineKeyboardButton(text="👎 1-3", callback_data=f"rate_3_{filename}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(F.text == '/start')
async def cmd_start(message: types.Message):
    await message.answer("🇵🇱 Cześć! Wyślij mi .docx\n🇺🇦 Привіт! Надішліть .docx\n🇬🇧 Hi! Send .docx")

@dp.message(F.document)
async def handle_docs(message: types.Message):
    if not message.document.file_name.lower().endswith(('.docx', '.doc')):
        await message.answer("❌ Error: .docx please")
        return

    status = await message.answer("⏳ Processing...")
    safe_name = smart_name(message.document.file_name)
    input_path = f"/tmp/cv_bot/uploads/{datetime.now().strftime('%H%M%S')}_{safe_name}"
    
    try:
        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, input_path)
        
        subprocess.run(['soffice', '--headless', '-env:UserInstallation=file:///tmp/.libreoffice',
                        '--convert-to', 'pdf', '--outdir', '/tmp/cv_bot/outputs', input_path], check=True, timeout=40)

        out_path = f"/tmp/cv_bot/outputs/{os.path.splitext(os.path.basename(input_path))[0]}.pdf"

        if os.path.exists(out_path):
            await message.answer_document(FSInputFile(out_path), caption="✅ Done!")
            # Спрашиваем оценку
            await message.answer("🇵🇱 Jak oceniasz jakość?\n🇺🇦 Як оцінюєте якість?\n🇬🇧 Rate the quality:", 
                               reply_markup=get_rating_keyboard(safe_name))
            
            await status.delete()
            os.remove(input_path)
            os.remove(out_path)
    except Exception as e:
        await message.answer(f"❌ Error: {e}")

# Обработка нажатия на кнопки
@dp.callback_query(F.data.startswith('rate_'))
async def process_rating(callback: types.CallbackQuery):
    _, rating, filename = callback.data.split('_', 2)
    
    # Отправка в Google Таблицу
    payload = {
        "user_id": callback.from_user.id,
        "username": callback.from_user.username or "N/A",
        "rating": rating,
        "filename": filename
    }
    try:
        requests.post(GOOGLE_SHEET_URL, json=payload, timeout=5)
        await callback.answer("Dziękuję! / Дякую! / Thank you!")
        await callback.message.edit_text(f"⭐ Twoja ocena: {rating}. Спасибо!")
    except:
        await callback.answer("Saved (Offline)")

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    update = types.Update.model_validate(request.json, context={"bot": bot})
    asyncio.run(dp.feed_update(bot, update))
    return "OK", 200

@app.route('/health')
def health(): return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
