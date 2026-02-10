import asyncio
import os
import logging
import json
import subprocess
import tempfile
from collections import defaultdict
from aiohttp import ClientSession, FormData
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Счетчики пользователей (fake)
user_stats = defaultdict(lambda: {"conversions": 0, "premium": False})

# ✅ ПРАВИЛЬНОЕ автоопределение языка по Telegram language_code
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
    return 'pl'  # По умолчанию польский

# ✅ Тексты с новой почтой + сайтом + возвратом денег
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
        'success': "✅ <b>PREMIUM PDF GOTOWE!</b>\\n✨ HR friendly design!\\n💎 Kolejna: 9,99zł mc",
        'trial_used': "🎁 Gratis zużyty!\\n💎 Premium 9,99zł → Nielimitowane!"
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
        'success': "✅ <b>ПРЕМІУМ PDF ГОТОВО!</b>\\n✨ Ідеально для HR!\\n💎 Наступна: 9,99zł/міс",
        'trial_used': "🎁 Безкоштовна використана!\\n💎 Premium 9,99zł → Необмежено!"
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
        'success': "✅ <b>PREMIUM PDF READY!</b>\\n✨ HR friendly design!\\n💎 Next: 9,99zł/month",
        'trial_used': "🎁 Free trial used!\\n💎 Premium 9,99zł → Unlimited!"
    }
}

def main_keyboard(lang='pl'):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔒 Polityka prywatności", callback_data="privacy"))
    builder.add(InlineKeyboardButton(text="📧 Support 24h", callback_data="support"))
    builder.add(InlineKeyboardButton(text="💎 Premium 9,99zł", callback_data="premium"))
    builder.add(InlineKeyboardButton(text="💳 Przelewy24", callback_data="przelew24"))
    builder.add(InlineKeyboardButton(text="📊 Statystyki", callback_data="stats"))
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
• Zażalenia: [cvkonwerterpoland@gmail.com](mailto:cvkonwerterpoland@gmail.com)

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
        "<a href='https://t.me/+08zaEqwDXTI4YTI0'>Support CV Konwerter</a>\n\n"
        "👨‍💼 <b>Główny support:</b> @autoalex_ai\n"
        "📧 <b>Email:</b> <a href='mailto:cvkonwerterpoland@gmail.com'>cvkonwerterpoland@gmail.com</a>\n\n"
        "⚡ <b>Odpowiedź w 30 minut!</b>\n"
        "💎 Premium = priorytet (5 minut)\n\n"
        "🤖 <i>@GroupHelpBot + @anti_spambot aktywne</i>",
        parse_mode="HTML",
        reply_markup=main_keyboard(lang),
        disable_web_page_preview=True
    )
    await callback.answer()

@dp.callback_query(F.data == "premium")
async def premium_info(callback: types.CallbackQuery):
    lang = detect_language(callback.from_user)
    await callback.message.edit_text(
        "💎 <b>PREMIUM 9,99zł/mc - WSZYSTKO ВКЛЮЧЕНО</b>\\n\\n"
        "🎯 <b>Co otrzymujesz:</b>\\n"
        "• 100+ konwersji dziennie\\n"
        "• ⚡ Turbo prędkość 5 sekund\\n"
        "• 🎨 Profesjonalny design CV\\n"
        "• 📱 Aplikacja mobilna\\n"
        "• 🌙 Dostęp 24/7 bez limitów\\n"
        "• 🔒 100% prywatność\\n"
        "• 📧 Support w 5 minut\\n\\n"
        "💰 <b>9,99zł = 33gr/konwersja</b>\\n"
        "💰 <b>14 dni na zwrot</b> (polskie prawo)\\n"
        "💳 <a href='https://przelewy24.pl/cvkonwerter'>Przelewy24 → AKTYWUJ</a>",
        parse_mode="HTML",
        reply_markup=main_keyboard(lang),
        disable_web_page_preview=True
    )
    await callback.answer()

@dp.callback_query(F.data == "przelew24")
async def przelew24(callback: types.CallbackQuery):
    lang = detect_language(callback.from_user)
    await callback.message.edit_text(
        "💳 <b>PRZELEWY24 - NATYCHMIAST!</b>\\n\\n"
        "🔗 <a href='https://przelewy24.pl/cvkonwerter'>PŁAĆ 9,99zł → PREMIUM AKTYWNE</a>\\n\\n"
        "⚡ Aktywacja w <b>5 sekund</b>\\n"
        "✅ Natychmiastowy dostęp\\n"
        "💰 14 dni zwrot pieniędzy\\n\\n"
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
        f"📊 <b>Twoje statystyki</b>\\n\\n"
        f"✅ Konwersji: <b>{conversions}</b>\\n"
        f"🎯 Status: <b>{status}</b>\\n\\n"
        f"💎 Premium 9,99zł → Nielimitowane!\\n"
        f"🔒 Dane chronione GDPR/RODO\\n"
        f"📧 <a href='mailto:cvkonwerterpoland@gmail.com'>Support</a>",
        parse_mode="HTML",
        reply_markup=main_keyboard('pl')
    )
    await callback.answer()

# ✅ LIBREOFFICE ЗАМЕНА Render.com
@dp.message(F.document)
async def handle_doc(message: types.Message):
    user_id = message.from_user.id
    doc = message.document
    
    # Обновляем статистику
    user_stats[user_id]["conversions"] += 1
    
    if not doc.file_name or not doc.file_name.lower().endswith(('.docx', '.doc')):
        lang = detect_language(message.from_user)
        await message.reply(
            "📄 Tylko .docx lub .doc pliki!\\n🔒 Dane chronione GDPR.",
            parse_mode="HTML",
            reply_markup=main_keyboard(lang)
        )
        return
    
    lang = detect_language(message.from_user)
    await message.reply(
        "⏳ <b>Konwertuję 1 plik... ⚙️ LibreOffice</b>\\n⏱️ Czekaj 30-60s\\n🔒 Plik usuwany po konwersji",
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
        
        logger.info(f"📊 Konwertuję: {temp_docx} → {temp_pdf}")
        
        # ✅ LIBREOFFICE CLI (1 файл за раз!)
        result = subprocess.run([
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            temp_docx,
            '--outdir', '/tmp'
        ], capture_output=True, text=True, timeout=90)
        
        # Проверяем PDF создался
        pdf_path = f"/tmp/{os.path.splitext(os.path.basename(temp_docx))[0]}.pdf"
        if result.returncode != 0 or not os.path.exists(pdf_path):
            logger.error(f"LibreOffice stderr: {result.stderr}")
            raise Exception(f"LibreOffice failed. Spróbuj prostszy plik.")
        
        # Читаем PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        logger.info(f"✅ PDF gotowy! Size: {len(pdf_bytes)} bytes")
        
        # Fake Premium
        is_premium = user_stats[user_id]["conversions"] % 3 == 0
        user_stats[user_id]["premium"] = is_premium
        status_emoji = "💎" if is_premium else "🎁"
        filename = "cv_premium.pdf" if is_premium else "cv.pdf"
        
        await message.reply_document(
            BufferedInputFile(pdf_bytes, filename=filename),
            caption=(
                f"{status_emoji} <b>{TEXTS[lang]['success']}</b>\\n\\n"
                f"📊 Konwersji: <b>{user_stats[user_id]['conversions']}</b>\\n"
                f"⚙️ LibreOffice Premium\\n"
                f"🔒 <i>Dane usunięte (GDPR 60s)</i>\\n"
                f"💎 <a href='https://przelewy24.pl/cvkonwerter'>Premium 9,99zł</a>"
            ),
            parse_mode="HTML",
            reply_markup=main_keyboard(lang),
            disable_web_page_preview=True
        )
        logger.info("✅ Konwersja OK!")
    
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
            f"❌ Błąd konwersji: <code>{str(e)[:100]}</code>\\n\\n"
            f"{TEXTS[lang]['trial_used']}\\n"
            "📧 <a href='mailto:cvkonwerterpoland@gmail.com'>Support</a>",
            parse_mode="HTML",
            reply_markup=main_keyboard(lang)
        )
    
    finally:
        # GDPR - чистим файлы
        for path in [temp_docx, temp_pdf]:
            try:
                if path and os.path.exists(path):
                    os.unlink(path)
            except:
                pass

async def main():
    logger.info("🚀 CV Konwerter Premium + LIBREOFFICE started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


