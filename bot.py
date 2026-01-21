# bot.py
import asyncio
import aiohttp
import subprocess
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ── Настройки ───────────────────────────────────────────────
API_TOKEN = '8579290334:AAEkgqc24lCNWYPXfx6x-UxIoHcZOGrdLTo'
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 МБ

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

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
            async with session.get(file_path) as resp:
                if resp.status != 200:
                    raise Exception("Download failed")
                input_path.write_bytes(await resp.read())

        # Конвертация через LibreOffice
      result = subprocess.run(
    ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(temp_dir), str(input_path)],
    capture_output=True,
    text=True,
    check=True
)

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

    except Exception as e:
        print(f"Ошибка: {type(e).__name__} → {e}")
        if lang == 'pl':
            err_msg = "😅 Coś poszło nie tak... Spróbuj później."
        elif lang == 'uk':
            err_msg = "😅 Щось пішло не так... Спробуй пізніше."
        else:
            err_msg = "😅 Something went wrong... Try again later."
        await message.reply(err_msg)

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
    print("Бот запущен (LibreOffice)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
