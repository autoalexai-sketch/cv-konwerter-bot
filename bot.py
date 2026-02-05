import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
APP_URL = "https://cv-konwerter-bot.fly.dev"
# ОБЯЗАТЕЛЬНО: Вставь свою ссылку Przelewy24 ниже
P24_LINK = "https://secure.przelewy24.pl/your_actual_link" 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ЛОГИКА БОТА (ПРЕЖНИЙ ВИД) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Возвращаем полноценное приветствие на 3-х языках
    text = (
        "👋 **Witaj в CV Konwerter!**\n\n"
        "🇵🇱 Wyślij mi swoje CV w formacie PDF lub DOCX, а ja pomogę Ci je przetłumaczyć.\n"
        "🇬🇧 Send me your CV in PDF or DOCX format, and I will help you translate it.\n"
        "🇺🇦 Надішліть мені своє CV у форматі PDF або DOCX, і я допоможу вам його перекласти.\n\n"
        "💳 /pay — Płatność / Payment / Оплата"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("pay"))
async def cmd_pay(message: types.Message):
    # Профессиональный вид сообщения об оплате
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Opłać przez Przelewy24 🇵🇱", url=P24_LINK))
    
    await message.answer(
        "Aby rozpocząć tłumaczenie, prosimy o dokonanie płatności:\n"
        "To start the translation, please make a payment:",
        reply_markup=builder.as_markup()
    )

@dp.message(F.document)
async def handle_docs(message: types.Message):
    # Возвращаем выбор языка вместо простой надписи
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Na Polski 🇵🇱", callback_data="to_pl"),
        types.InlineKeyboardButton(text="To English 🇬🇧", callback_data="to_en")
    )
    
    await message.answer(
        "📄 **Dokument otrzymany!** Wybierz język tłumaczenia:\n"
        "📄 **Document received!** Choose translation language:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("to_"))
async def process_translation(callback: types.CallbackQuery):
    target = "Polski" if callback.data == "to_pl" else "English"
    await callback.message.edit_text(f"⏳ Tłumaczenie na język {target} rozpoczęte...\nProszę czekać.")
    # Здесь вызывается логика конвертации

# --- ВЕБ-СТРАНИЦА (ПРЕЖНИЙ ВИД) ---

async def handle_index(request):
    # Возвращаем строгий вид страницы
    html = """
    <html>
        <head><meta charset="utf-8"><title>CV Konwerter Service</title></head>
        <body style="display:flex; justify-content:center; align-items:center; height:100vh; margin:0; font-family:sans-serif; background:#f0f2f5;">
            <div style="text-align:center; padding:50px; background:white; border-radius:15px; box-shadow:0 10px 25px rgba(0,0,0,0.1);">
                <h1 style="color:#1a73e8;">🤖 CV Konwerter Bot</h1>
                <p style="font-size:1.2em; color:#5f6368;">Service is Online</p>
                <hr style="border:0; border-top:1px solid #eee; margin:20px 0;">
                <p>European Market Support: 🇵🇱 🇬🇧 🇺🇦</p>
            </div>
        </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

# --- СИСТЕМНАЯ ЧАСТЬ ---

async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    await bot.set_webhook(url=f"{APP_URL}/webhook", drop_pending_updates=True)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
