import asyncio
import os
import time
import re
import logging
from pathlib import Path
from aiohttp import web, ClientSession, FormData, ClientTimeout
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import BufferedInputFile

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ из переменных окружения ---
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не задан! Установи переменную окружения.")
    exit(1)

APP_URL = os.getenv("APP_URL", "https://cv-konwerter-bot.fly.dev")
P24_LINK = os.getenv("P24_LINK", "https://przelewy24.pl/payment/YOUR_LINK_HERE")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://cv-konwerter-web-docker.onrender.com")
FILE_SIZE_LIMIT = int(os.getenv("FILE_SIZE_LIMIT", "15")) * 1024 * 1024  # 15MB
RATE_LIMIT_COUNT = int(os.getenv("RATE_LIMIT_COUNT", "5"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Защита от спама
user_limits = {}

# Безопасная временная папка
temp_dir = Path("/tmp/cv_bot")
temp_dir.mkdir(parents=True, exist_ok=True)
temp_dir.chmod(0o755)  # Более безопасные права

# --- МУЛЬТИЯЗЫЧНЫЕ ТЕКСТЫ ---
MESSAGES = {
    'pl': {
        'start': "🇪🇺 Cześć! 👋 Konwertuję CV z Word → idealny PDF (zgodny z RODO/GDPR)\n\n"
                "📄 Wyślij plik .doc lub .docx → PDF gotowy w kilka sekund\n\n"
                "💎 Premium: piękny szablon CV + list motywacyjny + AI asystent\n"
                "   tylko 9.99 zł/ 2.50 € ✨\n\n"
                "ℹ️ /premium - szczegóły Premium\nℹ️ /help - pomoc",
        'premium_btn': "Kup Premium (9.99 zł/ 2.50 €) 💎",
        'processing': "⏳ Konwertuję do PDF...",
        'success': "✅ Gotowe! Twój PDF (zgodny z RODO/GDPR) 📄",
        'rate_limit': "⚠️ Zbyt wiele plików. Spróbuj ponownie za minutę.",
        'wrong_format': "📄 Tylko pliki .doc lub .docx, proszę.",
        'file_too_big': "📄 Plik zbyt duży (maks. {limit} MB).",
        'timeout': "😅 Konwersja trwa zbyt długo. Spróbuj ponownie za chwilę.",
        'error': "😅 Nie udało się przekonwertować pliku. Spróbuj ponownie za chwilę.",
        'premium_info': "💎 **Premium (9.99 zł jednorazowo):**\n\n"
                       "• Profesjonalne szablony CV\n"
                       "• List motywacyjny w pakiecie\n"
                       "• Asystent AI ocenia Twoje CV\n"
                       "• Wybór układu pod branżę\n\n"
                       "[Kup teraz]({p24})",
        'help': "ℹ️ **Pomoc:**\n\n"
               "1️⃣ Wyślij plik .doc lub .docx\n"
               "2️⃣ Otrzymasz PDF zgodny z RODO\n"
               "3️⃣ Pliki usuwane automatycznie po 24h\n\n"
               "💎 Premium: /premium\n"
               "🔒 Polityka prywatności: {privacy}"
    },
    'uk': {
        'start': "🇺🇦 Привіт! 👋 Конвертую твоє CV з Word → ідеальний PDF (GDPR)\n\n"
                "📄 Надішли .doc або .docx → PDF готовий за секунди\n\n"
                "💎 Преміум: шаблон CV + супровідний лист + AI помічник\n"
                "   лише 9.99 зл/ 2.50 € ✨\n\n"
                "ℹ️ /premium - деталі Преміум\nℹ️ /help - допомога",
        'premium_btn': "Купити Преміум (9.99 зл/ 2.50 €) 💎",
        'processing': "⏳ Перетворюю в PDF...",
        'success': "✅ Готово! Твій PDF (GDPR-сумісний) 📄",
        'rate_limit': "⚠️ Занадто багато файлів. Спробуйте через хвилину.",
        'wrong_format': "📄 Тільки файли .doc або .docx, будь ласка.",
        'file_too_big': "📄 Файл занадто великий (макс. {limit} МБ).",
        'timeout': "😅 Перетворення триває надто довго. Спробуйте ще раз.",
        'error': "😅 Не вдалося перетворити файл. Спробуйте ще раз.",
        'premium_info': "💎 **Преміум (9.99 зл одноразово):**\n\n"
                       "• Професійні шаблони CV\n"
                       "• Супровідний лист у комплекті\n"
                       "• AI асистент оцінює CV\n"
                       "• Вибір макету під спеціальність\n\n"
                       "[Купити]({p24})",
        'help': "ℹ️ **Допомога:**\n\n"
               "1️⃣ Надішліть .doc або .docx\n"
               "2️⃣ Отримайте PDF сумісний з GDPR\n"
               "3️⃣ Файли видаляються автоматично через 24 год\n\n"
               "💎 Преміум: /premium"
    },
    'en': {
        'start': "🇪🇺 Hi! 👋 Converting CV from Word → GDPR-compliant PDF\n\n"
                "📄 Send .doc or .docx → PDF ready in seconds\n\n"
                "💎 Premium: CV templates + cover letter + AI assistant\n"
                "   only 9.99 zł/ 2.50 € ✨\n\n"
                "ℹ️ /premium - Premium details\nℹ️ /help - help",
        'premium_btn': "Buy Premium (9.99 zł/ 2.50 €) 💎",
        'processing': "⏳ Converting to PDF...",
        'success': "✅ Done! Your GDPR-safe PDF 📄",
        'rate_limit': "⚠️ Too many files. Try again in a minute.",
        'wrong_format': "📄 Only .doc or .docx files, please.",
        'file_too_big': "📄 File too big (max {limit} MB).",
        'timeout': "😅 Conversion taking too long. Try again.",
        'error': "😅 Failed to convert file. Try again.",
        'premium_info': "💎 **Premium (9.99 zł one-time):**\n\n"
                       "• Professional CV templates\n"
                       "• Cover letter included\n"
                       "• AI assistant reviews CV\n"
                       "• Industry-specific layouts\n\n"
                       "[Buy now]({p24})",
        'help': "ℹ️ **Help:**\n\n"
               "1️⃣ Send .doc or .docx file\n"
               "2️⃣ Get GDPR-compliant PDF\n"
               "3️⃣ Files auto-deleted after 24h\n\n"
               "💎 Premium: /premium"
    }
}

def get_message(key: str, lang: str = 'en', **kwargs) -> str:
    """Получить локализованное сообщение"""
    lang = lang[:2]  # pl/uk/en
    msg = MESSAGES.get(lang, MESSAGES['en']).get(key, key)
    return msg.format(**kwargs)

# --- ЗАЩИТА: Валидация имён файлов ---
def sanitize_filename(filename: str) -> str:
    safe_name = re.sub(r'[^a-zA-Z0-9._\\-]', '_', filename)
    safe_name = safe_name.lstrip('.')
    return safe_name[:100] or "file"

# --- ЗАЩИТА: Проверка лимита файлов ---
def check_user_limit(user_id: int) -> bool:
    now = time.time()
    if user_id not in user_limits:
        user_limits[user_id] = (now, 1)
        return True
    
    last_time, count = user_limits[user_id]
    if now - last_time > RATE_LIMIT_WINDOW:
        user_limits[user_id] = (now, 1)
        return True
    
    if count >= RATE_LIMIT_COUNT:
        return False
    
    user_limits[user_id] = (last_time, count + 1)
    return True

# --- КОМАНДЫ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = message.from_user.language_code or 'en'
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text=get_message('premium_btn', lang), 
        url=P24_LINK
    ))
    await message.answer(get_message('start', lang), 
                        reply_markup=builder.as_markup(), 
                        parse_mode='Markdown')

@dp.message(Command("premium"))
async def cmd_premium(message: types.Message):
    lang = message.from_user.language_code or 'en'
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text=get_message('premium_btn', lang), 
        url=P24_LINK
    ))
    await message.answer(get_message('premium_info', lang, p24=P24_LINK), 
                        reply_markup=builder.as_markup(), 
                        parse_mode='Markdown')

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    lang = message.from_user.language_code or 'en'
    privacy_url = "https://cv-konwerter-bot.fly.dev/polityka-prywatnosci.html"
    await message.answer(get_message('help', lang, privacy=privacy_url), 
                        parse_mode='Markdown')

# --- ОБРАБОТКА ФАЙЛОВ ---
@dp.message(F.document)
async def handle_docs(message: types.Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code or 'en'
    
    # Проверка лимита
    if not check_user_limit(user_id):
        await message.reply(get_message('rate_limit', lang))
        return
    
    doc = message.document
    
    # Валидация формата
    if not doc.file_name or not doc.file_name.lower().endswith(('.doc', '.docx')):
        await message.reply(get_message('wrong_format', lang))
        return
    
    # Валидация размера
    if doc.file_size and doc.file_size > FILE_SIZE_LIMIT:
        mb_limit = FILE_SIZE_LIMIT / (1024 * 1024)
        await message.reply(get_message('file_too_big', lang, limit=mb_limit))
        return
    
    # Сообщение о обработке
    processing_msg = await message.reply(get_message('processing', lang))
    input_path = None
    
    try:
        # Скачиваем файл
        file = await bot.get_file(doc.file_id)
        file_path = file.file_path  # Безопасно, токен уже в Bot
        
        async with ClientSession(timeout=ClientTimeout(total=30)) as session:
            async with session.get(file_path) as resp:
                if resp.status != 200:
                    raise Exception(f"Telegram API error: {resp.status}")
                content = await resp.read()
                
                safe_filename = sanitize_filename(doc.file_name)
                input_path = temp_dir / f"{user_id}_{int(time.time())}_{safe_filename}"
                input_path.write_bytes(content)
                input_path.chmod(0o644)  # Более безопасные права
        
        # Отправляем на конвертер
        async with ClientSession(timeout=ClientTimeout(total=60)) as session:
            data = FormData()
            data.add_field('file', open(input_path, 'rb'), filename=safe_filename)
            
            async with session.post(
                f"{WEB_APP_URL}/convert", 
                data=data, 
                headers={'User-Agent': 'CVKonwerterBot/1.0'},
                timeout=ClientTimeout(total=60)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Converter error {resp.status}: {text[:200]}")
                    raise Exception(f"Conversion failed: HTTP {resp.status}")
                
                pdf_content = await resp.read()
        
        # Успех
        await processing_msg.delete()
        await message.answer_document(
            BufferedInputFile(pdf_content, filename=f"cv_{int(time.time())}.pdf"),
            caption=get_message('success', lang),
            parse_mode='Markdown'
        )
        
    except asyncio.TimeoutError:
        await processing_msg.edit_text(get_message('timeout', lang))
    except Exception as e:
        logger.error(f"Conversion error for user {user_id}: {e}", exc_info=True)
        await processing_msg.edit_text(get_message('error', lang))
    finally:
        # Очистка
        if input_path and input_path.exists():
            try:
                input_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file {input_path}: {e}")

# --- HEALTH CHECK ---
async def handle_health(request):
    return web.Response(text="OK", status=200, content_type='text/plain')

async def handle_index(request):
    return web.Response(text="CV Konwerter Bot v2.0 - RODO compliant\n", status=200)

# --- ГРАЦИОЗНАЯ ОСТАНОВКА ---
shutdown_event = asyncio.Event()

async def on_startup(app):
    logger.info("🚀 Bot starting up...")
    await bot.set_webhook(url=f"{APP_URL}/webhook", drop_pending_updates=True)
    logger.info(f"✅ Webhook set: {APP_URL}/webhook")

async def on_shutdown(app):
    logger.info("🛑 Shutting down...")
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()
    shutdown_event.set()

# --- ЗАПУСК ---
async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/health', handle_health)
    
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    # Graceful shutdown
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    
    logger.info("✅ Bot gotowy do pracy!")
    logger.info(f"✅ Webhook: {APP_URL}/webhook")
    logger.info(f"✅ Converter: {WEB_APP_URL}")
    logger.info(f"✅ Rate limit: {RATE_LIMIT_COUNT}/min, max {FILE_SIZE_LIMIT/(1024*1024)}MB")
    
    await shutdown_event.wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt - shutting down gracefully")

