import asyncio
import os
import time
import re
from pathlib import Path
from aiohttp import web, ClientSession, FormData
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- КОНФИГУРАЦИЯ (БЕЗ ПРОБЕЛОВ!) ---
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"  # ← НЕТ ПРОБЕЛОВ!
P24_LINK = "https://przelewy24.pl/payment/YOUR_LINK_HERE"  # ← НЕТ ПРОБЕЛОВ!
WEB_APP_URL = "https://cv-konwerter-web-docker.onrender.com"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Защита от спама: максимум 5 файлов/минуту на пользователя
user_limits = {}

temp_dir = Path("/tmp/cv_bot")
temp_dir.mkdir(parents=True, exist_ok=True)
os.chmod(temp_dir, 0o777)

# --- ЗАЩИТА: Валидация имён файлов ---
def sanitize_filename(filename: str) -> str:
    safe_name = re.sub(r'[^a-zA-Z0-9._\-]', '_', filename)
    safe_name = safe_name.lstrip('.')
    return safe_name[:100] or "file"

# --- ЗАЩИТА: Проверка лимита файлов ---
def check_user_limit(user_id: int) -> bool:
    now = time.time()
    if user_id not in user_limits:
        user_limits[user_id] = (now, 1)
        return True
    
    last_time, count = user_limits[user_id]
    if now - last_time > 60:
        user_limits[user_id] = (now, 1)
        return True
    
    if count >= 5:
        return False
    
    user_limits[user_id] = (last_time, count + 1)
    return True

# --- КОМАНДА /start (МУЛЬТИЯЗЫЧНАЯ) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = message.from_user.language_code or 'en'
    
    if lang.startswith('pl'):
        text = (
            "🇪🇺 Cześć! 👋 Konwertuję CV z Word → idealny PDF (zgodny z RODO/GDPR)\n\n"
            "📄 Wyślij plik .doc lub .docx → PDF gotowy w kilka sekund\n\n"
            "💎 Premium: piękny szablon CV + list motywacyjny\n"
            "   tylko 9.99 zł/ 2.50 € ✨"
        )
        btn_text = "Kup Premium (9.99 zł/ 2.50 €) 💎"
    elif lang.startswith('uk'):
        text = (
            "🇺🇦 Привіт! 👋 Конвертую твоє CV з Word → ідеальний PDF (відповідно до GDPR)\n\n"
            "📄 Надішли .doc або .docx → PDF готовий за лічені секунди\n\n"
            "💎 Преміум: красивий шаблон CV + супровідний лист\n"
            "   лише 9.99 зл/ 2.50 € ✨"
        )
        btn_text = "Купити Преміум (9.99 зл/ 2.50 €) 💎"
    else:
        text = (
            "🇪🇺 Hi! 👋 Converting your CV from Word → perfect PDF (GDPR-compliant)\n\n"
            "📄 Send .doc or .docx file → PDF ready in seconds\n\n"
            "💎 Premium: beautiful template + cover letter\n"
            "   only 9.99 zł/ 2.50 € ✨"
        )
        btn_text = "Buy Premium (9.99 zł/ 2.50 €) 💎"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=btn_text, url=P24_LINK))
    await message.answer(text, reply_markup=builder.as_markup())

# --- ОБРАБОТКА ФАЙЛОВ (МУЛЬТИЯЗЫЧНАЯ + ЗАЩИТА) ---
@dp.message(F.document)
async def handle_docs(message: types.Message):
    user_id = message.from_user.id
    
    # 🔒 ЗАЩИТА: Проверка лимита файлов
    if not check_user_limit(user_id):
        lang = message.from_user.language_code or 'en'
        if lang.startswith('pl'):
            await message.reply("⚠️ Zbyt wiele plików. Spróbuj ponownie za minutę.")
        elif lang.startswith('uk'):
            await message.reply("⚠️ Занадто багато файлів. Спробуйте через хвилину.")
        else:
            await message.reply("⚠️ Too many files. Try again in a minute.")
        return
    
    doc = message.document
    
    # 🔒 ЗАЩИТА: Валидация расширения
    if not doc.file_name or not doc.file_name.lower().endswith(('.doc', '.docx')):
        lang = message.from_user.language_code or 'en'
        if lang.startswith('pl'):
            await message.reply("📄 Tylko pliki .doc lub .docx, proszę.")
        elif lang.startswith('uk'):
            await message.reply("📄 Тільки файли .doc або .docx, будь ласка.")
        else:
            await message.reply("📄 Only .doc or .docx files, please.")
        return
    
    # 🔒 ЗАЩИТА: Ограничение размера
    if doc.file_size and doc.file_size > 15 * 1024 * 1024:
        lang = message.from_user.language_code or 'en'
        if lang.startswith('pl'):
            await message.reply("📄 Plik zbyt duży (maks. 15 MB).")
        elif lang.startswith('uk'):
            await message.reply("📄 Файл занадто великий (макс. 15 МБ).")
        else:
            await message.reply("📄 File too big (max 15 MB).")
        return
    
    # Мультиязычное сообщение о конвертации
    lang = message.from_user.language_code or 'en'
    if lang.startswith('pl'):
        wait_msg = "⏳ Konwertuję do PDF..."
    elif lang.startswith('uk'):
        wait_msg = "⏳ Перетворюю в PDF..."
    else:
        wait_msg = "⏳ Converting to PDF..."
    processing_msg = await message.reply(wait_msg)
    
    input_path = None
    
    try:
        # Скачиваем файл от пользователя
        file = await bot.get_file(doc.file_id)
        # 🔑 КРИТИЧЕСКИ ВАЖНО: НЕТ ПРОБЕЛОВ ПОСЛЕ "bot"!
        file_path = f"https://api.telegram.org/file/bot{API_TOKEN}/{file.file_path}"
        async with ClientSession() as session:
            async with session.get(file_path) as resp:
                content = await resp.read()
                safe_filename = sanitize_filename(doc.file_name)
                input_path = temp_dir / f"{user_id}_{int(time.time())}_{safe_filename}"
                input_path.write_bytes(content)
                os.chmod(input_path, 0o666)
        
        # 🔑 ОТПРАВЛЯЕМ ФАЙЛ НА ТВОЙ РАБОЧИЙ САЙТ
        async with ClientSession() as session:
            data = FormData()
            data.add_field('file', open(input_path, 'rb'), filename=safe_filename)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            async with session.post(f"{WEB_APP_URL}/convert", data=data, headers=headers, timeout=60) as resp:
                if resp.status != 200:
                    raise Exception(f"Conversion failed: HTTP {resp.status}")
                pdf_content = await resp.read()
        
        # Мультиязычное сообщение об успехе
        lang = message.from_user.language_code or 'en'
        if lang.startswith('pl'):
            caption = "✅ Gotowe! Twój PDF (zgodny z RODO/GDPR) 📄"
        elif lang.startswith('uk'):
            caption = "✅ Готово! Твій PDF (відповідно до GDPR) 📄"
        else:
            caption = "✅ Done! Your PDF (GDPR-safe) 📄"
        
        await message.answer_document(
            types.BufferedInputFile(pdf_content, filename=f"cv_{int(time.time())}.pdf"),
            caption=caption
        )
        
    except asyncio.TimeoutError:
        lang = message.from_user.language_code or 'en'
        if lang.startswith('pl'):
            error_msg = "😅 Konwersja trwa zbyt długo. Spróbuj ponownie za chwilę."
        elif lang.startswith('uk'):
            error_msg = "😅 Перетворення триває надто довго. Спробуйте ще раз за хвилину."
        else:
            error_msg = "😅 Conversion taking too long. Try again in a moment."
        await processing_msg.edit_text(error_msg)
    except Exception as e:
        lang = message.from_user.language_code or 'en'
        if lang.startswith('pl'):
            error_msg = "😅 Nie udało się przekonwertować pliku. Spróbuj ponownie za chwilę."
        elif lang.startswith('uk'):
            error_msg = "😅 Не вдалося перетворити файл. Спробуйте ще раз за хвилину."
        else:
            error_msg = "😅 Failed to convert file. Try again in a moment."
        await processing_msg.edit_text(error_msg)
        print(f"❌ Ошибка конвертации: {type(e).__name__}: {e}")
    finally:
        if input_path and input_path.exists():
            input_path.unlink(missing_ok=True)

# --- HEALTH CHECK ---
async def handle_health(request):
    return web.Response(text="OK", status=200, content_type='text/plain')

async def handle_index(request):
    return web.Response(text="CV Konwerter Bot is running!\n", status=200, content_type='text/plain')

# --- ЗАПУСК БОТА ---
async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/health', handle_health)
    
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    await bot.set_webhook(url=f"{APP_URL}/webhook", drop_pending_updates=True)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    
    print("✅ Bot gotowy do pracy!")
    print(f"✅ Webhook: {APP_URL}/webhook")
    print(f"✅ Konwersja przez: {WEB_APP_URL}")
    print(f"✅ RODO: pliki usuwane po konwersji")
    print(f"✅ Bezpieczeństwo: limit 5 plików/min, max 15 MB")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())