import asyncio
import os
import subprocess
import shutil
import time
import re
from pathlib import Path
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"
P24_LINK = "https://przelewy24.pl/payment/YOUR_LINK_HERE"  # ← ЗАМЕНИ НА СВОЮ ССЫЛКУ!

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Защита от спама: максимум 5 файлов/минуту на пользователя
user_limits = {}

# Временная папка для файлов
temp_dir = Path("/tmp/cv_converter")
temp_dir.mkdir(parents=True, exist_ok=True)

# LibreOffice profile directory (КРИТИЧЕСКИ ВАЖНО для Fly.io!)
libreoffice_profile = Path("/tmp/.libreoffice")
libreoffice_profile.mkdir(parents=True, exist_ok=True)
os.environ["HOME"] = "/tmp"

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

# --- ЗАЩИТА: Фоновая очистка старых файлов ---
async def cleanup_old_files():
    while True:
        try:
            now = time.time()
            deleted = 0
            for file in temp_dir.glob("*.*"):
                if file.stat().st_mtime < now - 24 * 3600:
                    file.unlink(missing_ok=True)
                    deleted += 1
            if deleted > 0:
                print(f"🧹 Очищено {deleted} старых файлов (>24ч)")
        except Exception as e:
            print(f"⚠️ Ошибка очистки: {e}")
        await asyncio.sleep(3600)

# --- ПРИВЕТСТВИЕ С КОНВЕРТАЦИЕЙ CV ---
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

# --- КОНВЕРТАЦИЯ ФАЙЛОВ (ИСПРАВЛЕНА) ---
@dp.message(F.document)
async def handle_docs(message: types.Message):
    user_id = message.from_user.id
    
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
    
    if not doc.file_name or not doc.file_name.lower().endswith(('.doc', '.docx')):
        lang = message.from_user.language_code or 'en'
        if lang.startswith('pl'):
            await message.reply("📄 Tylko pliki .doc lub .docx, proszę.")
        elif lang.startswith('uk'):
            await message.reply("📄 Тільки файли .doc або .docx, будь ласка.")
        else:
            await message.reply("📄 Only .doc or .docx files, please.")
        return
    
    if doc.file_size and doc.file_size > 15 * 1024 * 1024:
        lang = message.from_user.language_code or 'en'
        if lang.startswith('pl'):
            await message.reply("📄 Plik zbyt duży (maks. 15 MB).")
        elif lang.startswith('uk'):
            await message.reply("📄 Файл занадто великий (макс. 15 МБ).")
        else:
            await message.reply("📄 File too big (max 15 MB).")
        return
    
    safe_filename = sanitize_filename(doc.file_name)
    
    lang = message.from_user.language_code or 'en'
    if lang.startswith('pl'):
        wait_msg = "⏳ Konwertuję do PDF..."
    elif lang.startswith('uk'):
        wait_msg = "⏳ Перетворюю в PDF..."
    else:
        wait_msg = "⏳ Converting to PDF..."
    processing_msg = await message.reply(wait_msg)
    
    input_path = None
    output_path = None
    
    try:
        # Скачиваем файл
        file = await bot.get_file(doc.file_id)
        file_path = f"https://api.telegram.org/file/bot{API_TOKEN}/{file.file_path}"
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(file_path, timeout=30) as resp:
                if resp.status != 200:
                    raise Exception("Download failed")
                content = await resp.read()
                input_path = temp_dir / f"{user_id}_{int(time.time())}_{safe_filename}"
                input_path.write_bytes(content)
        
        # 🔑 КРИТИЧЕСКИ ВАЖНО: правильные параметры LibreOffice для Fly.io
        output_path = temp_dir / f"{input_path.stem}.pdf"
        result = subprocess.run(
            [
                "soffice",
                "--headless",
                "--nologo",
                "--nofirststartwizard",
                "--norestore",
                f"-env:UserInstallation=file://{libreoffice_profile}",
                "--convert-to", "pdf",
                "--outdir", str(temp_dir),
                str(input_path)
            ],
            capture_output=True,
            text=True,
            timeout=60,  # Увеличен до 60 секунд
            check=True
        )
        
        # Отправляем PDF
        lang = message.from_user.language_code or 'en'
        if lang.startswith('pl'):
            caption = "✅ Gotowe! Twój PDF (zgodny z RODO/GDPR) 📄"
        elif lang.startswith('uk'):
            caption = "✅ Готово! Твій PDF (відповідно до GDPR) 📄"
        else:
            caption = "✅ Done! Your PDF (GDPR-safe) 📄"
        
        await message.answer_document(
            types.FSInputFile(output_path),
            caption=caption
        )
        
        # Удаляем файлы
        if input_path and input_path.exists():
            input_path.unlink(missing_ok=True)
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)
        
    except subprocess.TimeoutExpired:
        await processing_msg.edit_text("😅 Konwersja trwa zbyt długo. Spróbuj ponownie za chwilę.")
    except subprocess.CalledProcessError as e:
        await processing_msg.edit_text("😅 Nie udało się przekonwertować pliku. Sprawdź format.")
    except Exception as e:
        await processing_msg.edit_text("😅 Coś poszło nie tak... Spróbuj później.")
        print(f"⚠️ Внутренняя ошибка: {type(e).__name__}: {e}")
    finally:
        if input_path and input_path.exists():
            input_path.unlink(missing_ok=True)
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)

# --- HEALTH CHECK ДЛЯ FLY.IO ---
async def handle_health(request):
    if not temp_dir.exists():
        return web.Response(text="ERROR: temp dir missing", status=500)
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
    
    asyncio.create_task(cleanup_old_files())
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    print(f"✅ Bot running on port {port}")
    print(f"✅ LibreOffice profile: {libreoffice_profile}")
    print(f"✅ Temp dir: {temp_dir}")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
