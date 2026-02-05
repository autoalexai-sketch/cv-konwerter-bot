import asyncio
import os
import subprocess
import time
from pathlib import Path
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- КРИТИЧЕСКИ ВАЖНО: УБРАТЬ ПРОБЕЛЫ В URL ---
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"  # ← УБРАЛ ПРОБЕЛЫ В КОНЦЕ!
P24_LINK = "https://przelewy24.pl/payment/YOUR_LINK_HERE"  # ← УБРАЛ ПРОБЕЛЫ В КОНЦЕ!

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

temp_dir = Path("/tmp/cv_bot")
temp_dir.mkdir(parents=True, exist_ok=True)
os.chmod(temp_dir, 0o777)

libreoffice_profile = Path("/tmp/.libreoffice")
libreoffice_profile.mkdir(parents=True, exist_ok=True)
os.chmod(libreoffice_profile, 0o777)
os.environ["HOME"] = "/tmp"
os.environ["TMPDIR"] = "/tmp"

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
            "🇺🇦 Привіт! 👋 Конвертую твоє CV з Word → ідеальний PDF\n\n"
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

@dp.message(F.document)
async def handle_docs(message: types.Message):
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
        file = await bot.get_file(doc.file_id)
        # 🔑 КРИТИЧЕСКИ ВАЖНО: УБРАТЬ ПРОБЕЛЫ ПОСЛЕ "bot"!
        file_path = f"https://api.telegram.org/file/bot{API_TOKEN}/{file.file_path}"
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(file_path, timeout=30) as resp:
                content = await resp.read()
                input_path = temp_dir / f"{message.from_user.id}_{int(time.time())}_{doc.file_name}"
                input_path.write_bytes(content)
                os.chmod(input_path, 0o666)
        
        output_path = temp_dir / f"{input_path.stem}.pdf"
        
        # Конвертация через LibreOffice
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
            timeout=60,
            cwd="/tmp"
        )
        
        if not output_path.exists():
            raise Exception("PDF nie został utworzony")
        
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
        
    except subprocess.TimeoutExpired:
        await processing_msg.edit_text("😅 Konwersja trwa zbyt długo. Spróbuj ponownie za chwilę.")
    except Exception as e:
        await processing_msg.edit_text(f"😅 Nie udało się przekonwertować pliku.")
        print(f"❌ Ошибка: {type(e).__name__}: {e}")
    finally:
        if input_path and input_path.exists():
            input_path.unlink(missing_ok=True)
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)

async def handle_health(request):
    return web.Response(text="OK", status=200, content_type='text/plain')

async def handle_index(request):
    return web.Response(text="CV Konwerter Bot is running!\n", status=200, content_type='text/plain')

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
    # 🔑 КРИТИЧЕСКИ ВАЖНО: ЯВНО УКАЗАТЬ ПОРТ 8080 ДЛЯ FLY.IO
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    
    print("✅ Bot запущен и готов к работе!")
    print(f"✅ Webhook: {APP_URL}/webhook")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
