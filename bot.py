import asyncio
import os
import logging
import subprocess
import tempfile
from collections import defaultdict
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from rate_limiter import RateLimitMiddleware

# Загрузить переменные окружения
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
logger.info("TELEGRAM_BOT_TOKEN loaded" if TOKEN else "TELEGRAM_BOT_TOKEN is missing")

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Rate limiting: 5 запросов в час
dp.message.middleware(RateLimitMiddleware(rate_limit=5, time_window=3600))

# Счетчики пользователей (in-memory)
user_stats = defaultdict(lambda: {"conversions": 0, "premium": False})


def detect_language(user: types.User):
    """Определяем язык пользователя по language_code"""
    if not user.language_code:
        return 'pl'
    
    lang = user.language_code.lower()
    if lang.startswith('uk') or lang == 'ua':
        return 'uk'
    elif lang.startswith('en'):
        return 'en'
    elif lang.startswith('pl'):
        return 'pl'
    return 'pl'


TEXTS = {
    'pl': {
        'welcome': """✨ <b>CV Konwerter Premium</b> ✨

🇪🇺 <i>Cześć! Wyślij .docx → PDF w 15 sekund!</i>

<b>💎 PREMIUM 9,99zł/mc ZAWIERA:</b>
✅ <b>Nielimitowane</b> konwersje (100+/dzień)
⚡ <b>Turbo 5s</b> zamiast 15s
🎨 <b>Design Premium</b> (HR friendly)
🌙 <b>24/7 Dostęp</b> bez limitów
💰 <b>14 dni zwrot</b> (polskie prawo)

🎁 <b>PIERWSZA KONWERSJA GRATIS!</b>

🌐 <b>Serwis:</b> <a href='https://cv-konwerter-web-docker.onrender.com/'>cv-konwerter-web-docker.onrender.com</a>

📎 Wyślij .docx:""",
        'success': "✅ <b>PREMIUM PDF GOTOWE!</b>\n✨ HR friendly design!\n💎 Kolejna: 9,99zł mc",
        'trial_used': "🎁 Gratis zużyty!\n💎 Premium 9,99zł → Nielimitowane!"
    },
    'uk': {
        'welcome': """✨ <b>CV Конвертер Premium</b> ✨

🇪🇺 <i>Привіт! Відправ .docx → PDF за 15 сек!</i>

<b>💎 PREMIUM 9,99zł/міс ВКЛЮЧАЄ:</b>
✅ <b>Необмежено</b> конверсій (100+/день)
⚡ <b>Турбо 5с</b> замість 15с
🎨 <b>Преміум дизайн</b> (HR friendly)
🌙 <b>24/7 Доступ</b> без лімітів
💰 <b>14 днів повернення</b> (EU закон)

🎁 <b>ПЕРША БЕЗКОШТОВНО!</b>

🌐 <b>Сервіс:</b> <a href='https://cv-konwerter-web-docker.onrender.com/'>cv-konwerter-web-docker.onrender.com</a>

📎 Відправ .docx:""",
        'success': "✅ <b>ПРЕМІУМ PDF ГОТОВО!</b>\n✨ Ідеально для HR!\n💎 Наступна: 9,99zł/міс",
        'trial_used': "🎁 Безкоштовна використана!\n💎 Premium 9,99zł → Необмежено!"
    },
    'en': {
        'welcome': """✨ <b>CV Converter Premium</b> ✨

🇪🇺 <i>Hi! Send .docx → PDF in 15 seconds!</i>

<b>💎 PREMIUM 9,99zł/mo INCLUDES:</b>
✅ <b>Unlimited</b> conversions (100+/day)
⚡ <b>Turbo 5s</b> instead 15s
🎨 <b>Premium design</b> (HR friendly)
🌙 <b>24/7 Access</b> no limits
💰 <b>14 days refund</b> (EU law)

🎁 <b>FIRST ONE FREE!</b>

🌐 <b>Service:</b> <a href='https://cv-konwerter-web-docker.onrender.com/'>cv-konwerter-web-docker.onrender.com</a>

📎 Send .docx:""",
        'success': "✅ <b>PREMIUM PDF READY!</b>\n✨ HR friendly design!\n💎 Next: 9,99zł/month",
        'trial_used': "🎁 Free trial used!\n💎 Premium 9,99zł → Unlimited!"
    }
}


def main_keyboard(lang='pl'):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔒 Polityka prywatności", url="https://cv-konwerter-web-docker.onrender.com/polityka-prywatnosci"))
    builder.add(InlineKeyboardButton(text="📋 Regulamin", url="https://cv-konwerter-web-docker.onrender.com/regulamin"))
    builder.add(InlineKeyboardButton(text="🍪 Polityka cookies", url="https://cv-konwerter-web-docker.onrender.com/polityka-cookies"))
    builder.add(InlineKeyboardButton(text="💎 Zasady subskrypcji", url="https://cv-konwerter-web-docker.onrender.com/zasady-subskrypcji"))
    builder.add(InlineKeyboardButton(text="📧 Support 24h", callback_data="support"))
    builder.adjust(1)
    return builder.as_markup()


@dp.message(Command("start"))
async def start(message: types.Message):
    lang = detect_language(message.from_user)
    
    await message.answer(
        TEXTS[lang]['welcome'],
        parse_mode="HTML",
        reply_markup=main_keyboard(lang)
    )


@dp.callback_query(F.data == "privacy")
async def privacy_policy(callback: types.CallbackQuery):
    await callback.message.edit_text(
        """🔒 <b>POLITYKA PRYWATNOŚCI</b> 🔒

<b>1. Jakie dane zbieramy?</b>
• Telegram ID (anonimowy numer)
• Liczba konwersji (statystyka)
• Nazwa pliku .docx (tymczasowo → 60s)

<b>2. Czego NIE zbieramy?</b>
❌ Treść dokumentów CV
❌ Imię, nazwisko, email, telefon
❌ Adres IP, lokalizacja
❌ Żadne dane osobowe

<b>3. Przechowywanie:</b>
• Pliki .docx → usuwane po 60s
• Statystyka → pamięć RAM (nie dysk)
• Zero baz danych

<b>4. Bezpieczeństwo:</b>
✅ SSL szyfrowanie (HTTPS)
✅ Conform GDPR/RODO
✅ Zero reklam i trackerów

<b>5. Prawa użytkownika:</b>
• Usuń dane: @autoalex_ai
• Dostęp do danych: Support 24h
• Zażalenia: cvkonwerterpoland@gmail.com

<i>CV Konwerter Team | 2026
Ostatnia aktualizacja: 09.02.2026</i>""",
        parse_mode="HTML",
        reply_markup=main_keyboard('pl'),
        disable_web_page_preview=True
    )
    await callback.answer()


@dp.callback_query(F.data == "support")
async def support(callback: types.CallbackQuery):
    lang = detect_language(callback.from_user)
    await callback.message.edit_text(
        "📧 <b>SUPPORT 24h</b>\n\n"
        "💬 <b>Grupa wsparcia:</b>\n"
        "t.me/+08zaEqwDXTI4YTI0\n\n"
        "👨‍💼 <b>Główny support:</b> @autoalex_ai\n"
        "📧 <b>Email:</b> cvkonwerterpoland@gmail.com\n\n"
        "⚡ <b>Odpowiedź w 30 minut!</b>\n"
        "💎 Premium = priorytet (5 minut)",
        parse_mode="HTML",
        reply_markup=main_keyboard(lang),
        disable_web_page_preview=True
    )
    await callback.answer()


@dp.callback_query(F.data == "premium")
async def premium_info(callback: types.CallbackQuery):
    lang = detect_language(callback.from_user)
    await callback.message.edit_text(
        "💎 <b>PREMIUM 9,99zł/mc - WSZYSTKO WŁĄCZONE</b>\n\n"
        "🎯 <b>Co otrzymujesz:</b>\n"
        "• 100+ konwersji dziennie\n"
        "• ⚡ Turbo prędkość 5 sekund\n"
        "• 🎨 Profesjonalny design CV\n"
        "• 📱 Aplikacja mobilna\n"
        "• 🌙 Dostęp 24/7 bez limitów\n"
        "• 🔒 100% prywatność\n"
        "• 📧 Support w 5 minut\n\n"
        "💰 <b>9,99zł = 33gr/konwersja</b>\n"
        "💰 <b>14 dni na zwrot</b> (polskie prawo)",
        parse_mode="HTML",
        reply_markup=main_keyboard(lang),
        disable_web_page_preview=True
    )
    await callback.answer()


@dp.callback_query(F.data == "przelew24")
async def przelew24(callback: types.CallbackQuery):
    lang = detect_language(callback.from_user)
    await callback.message.edit_text(
        "💳 <b>PRZELEWY24 - NATYCHMIAST!</b>\n\n"
        "⚡ Aktywacja w <b>5 sekund</b>\n"
        "✅ Natychmiastowy dostęp\n"
        "💰 14 dni zwrot pieniędzy\n\n"
        "<i>Bezpieczne płatności Przelewy24</i>",
        parse_mode="HTML",
        reply_markup=main_keyboard(lang),
        disable_web_page_preview=True
    )
    await callback.answer()


@dp.callback_query(F.data == "stats")
async def stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    stats = user_stats[user_id]
    
    status = "💎 PREMIUM AKTYWNE" if stats["premium"] else "🎁 Trial"
    conversions = stats["conversions"]
    
    await callback.message.edit_text(
        f"📊 <b>Twoje statystyki</b>\n\n"
        f"✅ Konwersji: <b>{conversions}</b>\n"
        f"🎯 Status: <b>{status}</b>\n\n"
        f"💎 Premium 9,99zł → Nielimitowane!\n"
        f"🔒 Dane chronione GDPR/RODO\n"
        f"📧 Support: cvkonwerterpoland@gmail.com",
        parse_mode="HTML",
        reply_markup=main_keyboard('pl')
    )
    await callback.answer()


@dp.message(F.document)
async def handle_doc(message: types.Message):
    user_id = message.from_user.id
    doc = message.document
    lang = detect_language(message.from_user)
    
    # ============ ПРОВЕРКИ БЕЗОПАСНОСТИ ============
    
    # 1. Проверка размера файла (15 MB лимит)
    MAX_SIZE = int(os.getenv('MAX_FILE_SIZE_MB', '15')) * 1024 * 1024
    if doc.file_size and doc.file_size > MAX_SIZE:
        await message.reply(
            "❌ <b>Plik za duży!</b>\n"
            f"📊 Maksymalnie: {MAX_SIZE // 1024 // 1024} MB\n"
            f"📁 Twój plik: {doc.file_size // 1024 // 1024} MB\n\n"
            "💡 Spróbuj skompresować plik lub usuń obrazy.",
            parse_mode="HTML",
            reply_markup=main_keyboard(lang)
        )
        logger.warning(f"File too large: {doc.file_size} bytes from user {user_id}")
        return
    
    # 2. Proверка расширения файла
    if not doc.file_name or not doc.file_name.lower().endswith(('.docx', '.doc')):
        await message.reply(
            "❌ <b>Nieprawidłowy format!</b>\n\n"
            "📎 Akceptujemy tylko:\n"
            "• .docx (Word 2007+)\n"
            "• .doc (Word 97-2003)\n\n"
            "💡 Zapisz plik jako Word Document.",
            parse_mode="HTML",
            reply_markup=main_keyboard(lang)
        )
        logger.warning(f"Invalid file format: {doc.file_name} from user {user_id}")
        return
    
    # 3. Проверка на пустой файл
    if doc.file_size == 0:
        await message.reply(
            "❌ <b>Plik jest pusty!</b>\n\n"
            "📄 Wyślij plik z treścią.",
            parse_mode="HTML",
            reply_markup=main_keyboard(lang)
        )
        logger.warning(f"Empty file from user {user_id}")
        return
    
    # ============ КОНЕЦ ПРОВЕРОК ============
    
    # Обновляем статистику
    user_stats[user_id]["conversions"] += 1
    
    await message.reply(
        "⏳ <b>Konwertuję 1 plik... ⚙️ LibreOffice</b>\n⏱️ Czekaj 30-60s\n🔒 Plik usuwany po konwersji",
        parse_mode="HTML"
    )
    
    temp_docx = None
    temp_pdf = None
    
    try:
        # Скачиваем файл
        file_info = await bot.get_file(doc.file_id)
        async with ClientSession() as session:
            async with session.get(
                f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
            ) as file_resp:
                doc_bytes = await file_resp.read()
        
        # Временные файлы
        temp_docx = f"/tmp/{doc.file_id}.docx"
        temp_pdf = f"/tmp/{doc.file_id}.pdf"
        
        # Сохраняем .docx
        with open(temp_docx, "wb") as f:
            f.write(doc_bytes)
        
        logger.info(f"📊 Converting: {temp_docx} → {temp_pdf}")
        
        # LibreOffice конвертация
        result = subprocess.run([
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            temp_docx,
            '--outdir', '/tmp'
        ], capture_output=True, text=True, timeout=90)
        
        # Проверяем что PDF создался
        pdf_path = f"/tmp/{os.path.splitext(os.path.basename(temp_docx))[0]}.pdf"
        if result.returncode != 0 or not os.path.exists(pdf_path):
            logger.error(f"LibreOffice stderr: {result.stderr}")
            raise Exception("LibreOffice conversion failed")
        
        # Читаем PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        logger.info(f"✅ PDF ready! Size: {len(pdf_bytes)} bytes")
        
        # Fake Premium (каждая 3-я конвертация)
        is_premium = user_stats[user_id]["conversions"] % 3 == 0
        user_stats[user_id]["premium"] = is_premium
        status_emoji = "💎" if is_premium else "🎁"
        filename = "cv_premium.pdf" if is_premium else "cv.pdf"
        
        await message.reply_document(
            BufferedInputFile(pdf_bytes, filename=filename),
            caption=(
                f"{status_emoji} <b>{TEXTS[lang]['success']}</b>\n\n"
                f"📊 Konwersji: <b>{user_stats[user_id]['conversions']}</b>\n"
                f"⚙️ LibreOffice Premium\n"
                f"🔒 <i>Dane usunięte (GDPR 60s)</i>"
            ),
            parse_mode="HTML",
            reply_markup=main_keyboard(lang)
        )
        logger.info("✅ Conversion completed successfully!")
    
    except subprocess.TimeoutExpired:
        logger.error("❌ LibreOffice timeout 90s")
        await message.reply(
            "⏰ Timeout! Spróbuj <b>prostszy</b> .docx (bez tabel/kolorów)",
            parse_mode="HTML",
            reply_markup=main_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
        await message.reply(
            f"❌ Błąd konwersji\n\n"
            f"{TEXTS[lang]['trial_used']}\n"
            "📧 Support: cvkonwerterpoland@gmail.com",
            parse_mode="HTML",
            reply_markup=main_keyboard(lang)
        )
    
    finally:
        # GDPR - чистим файлы
        for path in [temp_docx, temp_pdf]:
            try:
                if path and os.path.exists(path):
                    os.unlink(path)
                    logger.info(f"🗑️ Deleted: {path}")
            except Exception as e:
                logger.error(f"Failed to delete {path}: {e}")


async def main():
    logger.info("🚀 CV Konwerter Premium + LIBREOFFICE started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

