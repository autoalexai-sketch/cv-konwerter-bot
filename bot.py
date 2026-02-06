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

API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"
P24_LINK = "https://przelewy24.pl/payment/YOUR_LINK_HERE"  # ← ЗАМЕНИ НА СВОЮ ССЫЛКУ!

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

temp_dir = Path("/tmp/cv_bot")
temp_dir.mkdir(parents=True, exist_ok=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "🇪🇺 Cześć! 👋 Konwertuję CV z Word → idealny PDF (zgodny z RODO/GDPR)\n\n"
        "📄 Wyślij plik .doc lub .docx → PDF gotowy w kilka sekund\n\n"
        "💎 Premium: piękny szablon CV + list motywacyjny\n"
        "   tylko 9.99 zł/ 2.50 € ✨"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Kup Premium (9.99 zł/ 2.50 €) 💎", url=P24_LINK))
    await message.answer(text, reply_markup=builder.as_markup())

@dp.message(F.document)
async def handle_docs(message: types.Message):
    doc = message.document
    if not doc.file_name or not doc.file_name.lower().endswith(('.doc', '.docx')):
        await message.reply("📄 Tylko pliki .doc lub .docx, proszę.")
        return
    
    if doc.file_size and doc.file_size > 15 * 1024 * 1024:
        await message.reply("📄 Plik zbyt duży (maks. 15 MB).")
        return
    
    processing_msg = await message.reply("⏳ Konwertuję do PDF...")
    
    input_path = None
    output_path = None
    
    try:
        file = await bot.get_file(doc.file_id)
        file_path = f"https://api.telegram.org/file/bot{API_TOKEN}/{file.file_path}"
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(file_path) as resp:
                content = await resp.read()
                input_path = temp_dir / f"{message.from_user.id}_{int(time.time())}_{doc.file_name}"
                input_path.write_bytes(content)
        
        output_path = temp_dir / f"{input_path.stem}.pdf"
        
        # Прямая конвертация через LibreOffice
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(temp_dir), str(input_path)],
            timeout=30,
            check=True
        )
        
        if not output_path.exists():
            raise Exception("PDF nie został utworzony")
        
        await message.answer_document(
            types.FSInputFile(output_path),
            caption="✅ Gotowe! Twój PDF (zgodny z RODO/GDPR) 📄"
        )
        
    except Exception as e:
        await processing_msg.edit_text("😅 Nie udało się przekonwertować pliku. Spróbuj ponownie za chwilę.")
    finally:
        if input_path and input_path.exists():
            input_path.unlink(missing_ok=True)
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)

async def handle_health(request):
    return web.Response(text="OK", status=200, content_type='text/plain')

async def handle_index(request):
    return web.Response(text="Bot is running", status=200, content_type='text/plain')

async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)  # ← КРИТИЧЕСКИ ВАЖНО: добавь эту строку!
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
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
