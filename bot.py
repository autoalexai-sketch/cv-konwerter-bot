# bot.py
import asyncio
import aiohttp
import subprocess
import shutil
import os
import signal

from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Правильный импорт для webhook в aiogram 3.x — ТОЛЬКО ОДНА строка!
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ── Настройки ───────────────────────────────────────────────
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 МБ
SOFFICE_PATH = "soffice"  # для Linux (Fly.io)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
WEBHOOK_PATH = '/webhook'
WEBAPP_HOST = '0.0.0.0'  # для Fly.io
WEBAPP_PORT = int(os.environ.get("PORT", 8080))  # Fly.io использует переменную PORT

# Поддерживаемые языки (Telegram language_code → наш код)
LANG_MAP = {
    'pl': 'pl',   # польский
    'uk': 'uk',   # украинский
    'en': 'en',   # английский (fallback)
}

DEFAULT_LANG = 'en'

def get_user_language(message: Message) -> str:
    user = message.from_user
    if not user or not user.language_code:
        return DEFAULT_LANG
    tg_lang = user.language_code.lower()[:2]
    return LANG_MAP.get(tg_lang, DEFAULT_LANG)

# ── Динамическая клавиатура Premium ──────────────────────────────────────
def get_premium_kb(lang: str) -> InlineKeyboardMarkup:
    if lang == 'pl':
        btn_text = "Kup Premium (39 zł / 8,5 €) 💎"
    elif lang == 'uk':
        btn_text = "Купити Преміум (39 zł / 8,5 €) 💎"
    else:
        btn_text = "Buy Premium (39 zł / 8,5 €) 💎"
    
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=btn_text, callback_data="buy_premium")
    ]])

# ── /start ──────────────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: Message):
    lang = get_user_language(message)
    
    if lang == 'pl':
        text = (
            "🇪🇺 Cześć! 👋 Konwertuję CV z Word → idealny PDF (zgodny z RODO/GDPR)\n\n"
            "📄 Wyślij plik .doc lub .docx → PDF gotowy w kilka sekund\n\n"
            "💎 Premium: piękny szablon CV + list motywacyjny\n"
            "   tylko 39 zł / 8,5 € ✨"
        )
    elif lang == 'uk':
        text = (
            "🇺🇦 Привіт! 👋 Конвертую твоє CV з Word → ідеальний PDF (відповідно до GDPR)\n\n"
            "📄 Надішли .doc або .docx → PDF готовий за лічені секунди\n\n"
            "💎 Преміум: красивий шаблон CV + супровідний лист\n"
            "   лише 39 zł / 8,5 € ✨"
        )
    else:  # en
        text = (
            "🇪🇺 Hi! 👋 Converting your CV from Word → perfect PDF (GDPR-compliant)\n\n"
            "📄 Send .doc or .docx file → PDF ready in seconds\n\n"
            "💎 Premium: beautiful template + cover letter\n"
            "   only 39 zł / 8,5 € ✨"
        )
    
    await message.answer(text, reply_markup=get_premium_kb(lang))

# ── Обработка файлов ────────────────────────────────────────
@dp.message()
async def handle_document(message: Message):
    if not message.document:
        return

    lang = get_user_language(message)
    doc = message.document
    filename = doc.file_name or "cv.docx"

    # Проверка расширения
    if not filename.lower().endswith(('.doc', '.docx')):
        if lang == 'pl':
            msg = "📄 Tylko plik .doc lub .docx, proszę."
        elif lang == 'uk':
            msg = "📄 Тільки .doc або .docx файл, будь ласка."
        else:
            msg = "📄 Only .doc or .docx file, please."
        await message.reply(msg)
        return

    # Проверка размера
    if doc.file_size and doc.file_size > MAX_FILE_SIZE:
        if lang == 'pl':
            msg = "📄 Plik zbyt duży (maks. 15 MB)."
        elif lang == 'uk':
            msg = "📄 Файл занадто великий (макс. 15 МБ)."
        else:
            msg = "📄 File too big (max 15 MB)."
        await message.reply(msg)
        return

    # Сообщение о начале конвертации
    if lang == 'pl':
        wait_msg = "⏳ Konwertuję do PDF..."
    elif lang == 'uk':
        wait_msg = "⏳ Перетворюю в PDF..."
    else:
        wait_msg = "⏳ Converting to PDF..."
    await message.reply(wait_msg)

    try:
        # Скачиваем файл
        file = await bot.get_file(doc.file_id)
        file_path = f"https://api.telegram.org/file/bot{API_TOKEN}/{file.file_path}"
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        input_path = temp_dir / f"{file.file_id}.docx"
        output_path = temp_dir / f"{file.file_id}.pdf"

        async with aiohttp.ClientSession() as session:
            async with session.get(file_path, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    raise Exception(f"Download failed with status {resp.status}")
                input_path.write_bytes(await resp.read())

        # Конвертация через LibreOffice с таймаутом
        result = subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(temp_dir), str(input_path)],
            capture_output=True,
            text=True,
            timeout=30,  # 30 секунд таймаут
            check=True
        )
        print(f"LibreOffice output: {result.stdout}")

        # Отправляем PDF
        if lang == 'pl':
            caption = "✅ Gotowe! Twój PDF (zgodny z RODO/GDPR) 📄"
        elif lang == 'uk':
            caption = "✅ Готово! Твій PDF (відповідно до GDPR) 📄"
        else:
            caption = "✅ Done! Your PDF (GDPR-safe) 📄"

        await message.answer_document(
            BufferedInputFile(
                file=output_path.read_bytes(),
                filename=filename.rsplit(".", 1)[0] + ".pdf"
            ),
            caption=caption
        )

        # Удаляем временные файлы
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)

    except subprocess.TimeoutExpired:
        print(f"Таймаут конвертации для файла {filename}")
        if lang == 'pl':
            err_msg = "😅 Konwersja trwa zbyt długo. Spróbuj mniejszego pliku."
        elif lang == 'uk':
            err_msg = "😅 Конвертація триває занадто довго. Спробуй менший файл."
        else:
            err_msg = "😅 Conversion timeout. Try a smaller file."
        await message.reply(err_msg)
        # Очистка
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
    except Exception as e:
        print(f"Ошибка конвертации: {type(e).__name__} → {e}")
        import traceback
        traceback.print_exc()
        if lang == 'pl':
            err_msg = "😅 Coś poszło nie tak... Spróbuj później."
        elif lang == 'uk':
            err_msg = "😅 Щось пішло не так... Спробуй пізніше."
        else:
            err_msg = "😅 Something went wrong... Try again later."
        await message.reply(err_msg)
        # Очистка
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        
# ── Premium ────────────────────────────────────────────────
@dp.callback_query(lambda c: c.data == "buy_premium")
async def process_premium(callback):
    await callback.answer()
    lang = get_user_language(callback.message)
    
    if lang == 'pl':
        text = "💳 Kup Premium (39 zł / 8,5 €):\n👉 https://przelewy24.pl/payment/YOUR_LINK_HERE\n\nPo opłacie napisz do mnie – wyślę szablon + instrukcję"
    elif lang == 'uk':
        text = "💳 Купити Преміум (39 zł / 8,5 €):\n👉 https://przelewy24.pl/payment/YOUR_LINK_HERE\n\nПісля оплати напиши мені – надішлю шаблон + інструкцію"
    else:
        text = "💳 Buy Premium (39 zł / 8,5 €):\n👉 https://przelewy24.pl/payment/YOUR_LINK_HERE\n\nAfter payment write to me – I'll send template + instructions"
    
    await callback.message.answer(text)

# ── Запуск ────────────────────────────────────────────────
async def main():
    # Очистка временной папки при старте
    temp_dir = Path("temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("Временная папка очищена")
    temp_dir.mkdir(exist_ok=True)

    print("Бот запущен (LibreOffice)...")

    app = web.Application()
    
    # Middleware для логирования всех запросов
    @web.middleware
    async def logging_middleware(request, handler):
        print(f"📥 Входящий запрос: {request.method} {request.path} от {request.remote}")
        try:
            response = await handler(request)
            print(f"📤 Ответ: {response.status}")
            return response
        except Exception as e:
            print(f"❌ Ошибка обработки запроса: {e}")
            raise
    
    app.middlewares.append(logging_middleware)
    
    # Добавляем health check endpoint для Fly.io
    async def health_check(request):
        print(f"Health check запрос от {request.remote}")
        return web.Response(text="OK", status=200)
    
    # Root endpoint для проверки
    async def root_handler(request):
        print(f"Root запрос от {request.remote}")
        return web.Response(text="CV Konwerter Bot is running!", status=200)
    
    app.router.add_get('/health', health_check)
    app.router.add_get('/', root_handler)

    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_handler.register(app, path=WEBHOOK_PATH)
    
    print(f"Webhook handler зарегистрирован на {WEBHOOK_PATH}")

    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()

    print(f"Сервер запущен на {WEBAPP_HOST}:{WEBAPP_PORT}")
    print("Ожидание входящих запросов...")

    # Получаем URL приложения из переменной окружения или используем дефолтный
    app_url = os.environ.get("FLY_APP_NAME")
    if app_url:
        webhook_url = f"https://{app_url}.fly.dev{WEBHOOK_PATH}"
    else:
        webhook_url = f"https://cv-poland-project.fly.dev{WEBHOOK_PATH}"
    
    try:
        # Удаляем старый webhook
        await bot.delete_webhook(drop_pending_updates=True)
        print("Старый webhook удален")
        
        # Устанавливаем новый webhook
        await bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        print(f"Webhook успешно установлен: {webhook_url}")
        
        # Проверяем webhook
        webhook_info = await bot.get_webhook_info()
        print(f"Webhook info: {webhook_info}")
    except Exception as e:
        print(f"Ошибка установки webhook: {type(e).__name__} → {e}")
        raise

    # Держим процесс живым + graceful shutdown для Fly.io
    print("Бот полностью запущен и ожидает запросов...")
    
    # Создаем событие для graceful shutdown
    shutdown_event = asyncio.Event()
    
    def handle_shutdown(signum, frame):
        print(f"Получен сигнал остановки: {signum}")
        shutdown_event.set()
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    try:
        # Ждем сигнала остановки
        await shutdown_event.wait()
    except asyncio.CancelledError:
        print("asyncio отменён — нормальный shutdown")
    finally:
        print("Начинаем graceful shutdown...")
        await bot.delete_webhook()
        await runner.cleanup()
        await bot.session.close()
        print("Ресурсы очищены")


if __name__ == "__main__":
    asyncio.run(main())
