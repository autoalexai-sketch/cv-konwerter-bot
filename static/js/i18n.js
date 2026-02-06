// Internationalization (i18n) for CV Konwerter
const translations = {
    pl: {
        'meta.title': 'CV Konwerter - Darmowa konwersja DOCX → PDF',
        'meta.description': 'Konwertuj CV do PDF w 2 sekundy! Bezpłatnie, szybko, bez rejestracji.',
        'nav.convert': 'Konwersja',
        'nav.premium': 'Premium',
        'nav.telegram': 'Telegram Bot',
        'hero.title': 'Konwertuj CV do PDF w 2 sekundy!',
        'hero.subtitle': 'Bezpłatnie, szybko i bez rejestracji',
        'hero.features.fast': 'Szybko',
        'hero.features.free': 'Darmowo',
        'hero.features.secure': 'Bezpiecznie',
        'convert.title': 'Konwertuj swoje CV',
        'convert.subtitle': 'Przeciągnij plik DOCX lub kliknij, aby wybrać',
        'convert.upload.drag': 'Przeciągnij plik tutaj',
        'convert.upload.or': 'lub',
        'convert.upload.button': 'Wybierz plik DOCX',
        'convert.upload.maxSize': 'Maksymalny rozmiar: 15 MB',
        'convert.button': 'Konwertuj do PDF',
        'convert.converting': 'Konwersja...',
        'convert.success.title': 'Gotowe! 🎉',
        'convert.success.download': 'Pobierz PDF',
        'convert.error.title': 'Wystąpił błąd',
        'premium.title': '💎 Pakiet Premium',
        'premium.subtitle': 'Profesjonalne CV + List motywacyjny za 9,99 zł',
        'premium.free.title': '🆓 Wersja darmowa',
        'premium.free.button': 'Używasz teraz',
        'premium.paid.title': '💎 Premium',
        'premium.paid.badge': 'Popularne',
        'premium.paid.price': '9.99 zł',
        'premium.paid.priceNote': 'jednorazowo',
        'premium.paid.button': 'Kup Premium (9,99 zł)',
        'premium.paid.payment': '💳 Płatność przez Przelewy24',
        'telegram.title': '📱 Używasz Telegram?',
        'telegram.subtitle': 'Wyślij CV bezpośrednio do naszego bota!',
        'telegram.button': 'Otwórz Telegram Bot',
        'footer.copyright': '&copy; 2026 CV Konwerter. Wszystkie prawa zastrzeżone.',
        'footer.privacy': 'Twoje pliki są automatycznie usuwane po <strong>24 godzinach</strong> zgodnie z RODO.',
        'rodo.consent': 'Potwierdzam, że mam prawo do udostępnienia tego dokumentu i akceptuję <a href="/polityka-prywatnosci" target="_blank" style="color: #4a6cf7;">politykę prywatności</a> zgodnie z RODO.',
        'form.step1.title': ' Dane osobowe',
        'form.step1.name': 'Imię',
        'form.step1.surname': 'Nazwisko',
        'form.step1.email': 'Email',
        'form.step1.phone': 'Telefon',
        'form.step1.address': 'Adres',
        'form.step1.postcode': 'Kod pocztowy',
        'form.step1.city': 'Miasto',
        'form.required': 'Pole wymagane',
        'form.invalid_email': 'Nieprawidłowy adres email',
        'form.invalid_phone': 'Nieprawidłowy numer telefonu (min. 9 cyfr)'
    },
    en: {
        'meta.title': 'CV Converter - Free DOCX → PDF conversion',
        'meta.description': 'Convert CV to PDF in 2 seconds! Free, fast, no registration.',
        'nav.convert': 'Conversion',
        'nav.premium': 'Premium',
        'nav.telegram': 'Telegram Bot',
        'hero.title': 'Convert your CV to PDF in 2 seconds!',
        'hero.subtitle': 'Free, fast and no registration',
        'hero.features.fast': 'Fast',
        'hero.features.free': 'Free',
        'hero.features.secure': 'Secure',
        'convert.title': 'Convert your CV',
        'convert.subtitle': 'Drag DOCX file or click to select',
        'convert.upload.drag': 'Drag file here',
        'convert.upload.or': 'or',
        'convert.upload.button': 'Select DOCX file',
        'convert.upload.maxSize': 'Max size: 15 MB',
        'convert.button': 'Convert to PDF',
        'convert.converting': 'Converting...',
        'convert.success.title': 'Done! 🎉',
        'convert.success.download': 'Download PDF',
        'convert.error.title': 'An error occurred',
        'premium.title': '💎 Premium Package',
        'premium.subtitle': 'Professional CV + Cover letter for 9.99 zł',
        'premium.free.title': '🆓 Free version',
        'premium.free.button': 'You are using now',
        'premium.paid.title': '💎 Premium',
        'premium.paid.badge': 'Popular',
        'premium.paid.price': '9.99 zł',
        'premium.paid.priceNote': 'one-time',
        'premium.paid.button': 'Buy Premium (9.99 zł)',
        'premium.paid.payment': '💳 Payment via Przelewy24',
        'telegram.title': '📱 Using Telegram?',
        'telegram.subtitle': 'Send CV directly to our bot!',
        'telegram.button': 'Open Telegram Bot',
        'footer.copyright': '&copy; 2026 CV Konwerter. All rights reserved.',
        'footer.privacy': 'Your files are automatically deleted after <strong>24 hours</strong> in accordance with GDPR.',
        'rodo.consent': 'I confirm that I have the right to share this document and accept the <a href="/privacy-policy" target="_blank" style="color: #4a6cf7;">privacy policy</a> in accordance with GDPR.',
        'form.step1.title': ' Personal data',
        'form.step1.name': 'First name',
        'form.step1.surname': 'Last name',
        'form.step1.email': 'Email',
        'form.step1.phone': 'Phone',
        'form.step1.address': 'Address',
        'form.step1.postcode': 'Postcode',
        'form.step1.city': 'City',
        'form.required': 'Required field',
        'form.invalid_email': 'Invalid email address',
        'form.invalid_phone': 'Invalid phone number (min. 9 digits)'
    },
    uk: {
        'meta.title': 'CV Конвертер - Безкоштовна конвертація DOCX → PDF',
        'meta.description': 'Конвертуйте CV в PDF за 2 секунди! Безкоштовно, швидко, без реєстрації.',
        'nav.convert': 'Конвертація',
        'nav.premium': 'Преміум',
        'nav.telegram': 'Telegram Бот',
        'hero.title': 'Конвертуйте своє CV в PDF за 2 секунди!',
        'hero.subtitle': 'Безкоштовно, швидко і без реєстрації',
        'hero.features.fast': 'Швидко',
        'hero.features.free': 'Безкоштовно',
        'hero.features.secure': 'Безпечно',
        'convert.title': 'Конвертуйте своє CV',
        'convert.subtitle': 'Перетягніть файл DOCX або натисніть, щоб вибрати',
        'convert.upload.drag': 'Перетягніть файл сюди',
        'convert.upload.or': 'або',
        'convert.upload.button': 'Вибрати файл DOCX',
        'convert.upload.maxSize': 'Максимальний розмір: 15 МБ',
        'convert.button': 'Конвертувати в PDF',
        'convert.converting': 'Конвертація...',
        'convert.success.title': 'Готово! 🎉',
        'convert.success.download': 'Завантажити PDF',
        'convert.error.title': 'Сталася помилка',
        'premium.title': '💎 Пакет Преміум',
        'premium.subtitle': 'Професійне CV + Супровідний лист за 9,99 зл',
        'premium.free.title': '🆓 Безкоштовна версія',
        'premium.free.button': 'Ви використовуєте зараз',
        'premium.paid.title': '💎 Преміум',
        'premium.paid.badge': 'Популярне',
        'premium.paid.price': '9.99 зл',
        'premium.paid.priceNote': 'одноразово',
        'premium.paid.button': 'Купити Преміум (9,99 зл)',
        'premium.paid.payment': '💳 Оплата через Przelewy24',
        'telegram.title': '📱 Користуєтесь Telegram?',
        'telegram.subtitle': 'Надішліть CV безпосередньо до нашого бота!',
        'telegram.button': 'Відкрити Telegram Бот',
        'footer.copyright': '&copy; 2026 CV Konwerter. Всі права захищені.',
        'footer.privacy': 'Ваші файли автоматично видаляються через <strong>24 години</strong> відповідно до GDPR.',
        'rodo.consent': 'Підтверджую, що маю право надати цей документ і приймаю <a href="/polityka-prywatnosci" target="_blank" style="color: #4a6cf7;">політику конфіденційності</a> відповідно до GDPR.',
        'form.step1.title': ' Особисті дані',
        'form.step1.name': "Ім'я",
        'form.step1.surname': 'Прізвище',
        'form.step1.email': 'Email',
        'form.step1.phone': 'Телефон',
        'form.step1.address': 'Адреса',
        'form.step1.postcode': 'Поштовий індекс',
        'form.step1.city': 'Місто',
        'form.required': 'Обов\'язкове поле',
        'form.invalid_email': 'Неправильна адреса email',
        'form.invalid_phone': 'Неправильний номер телефону (мін. 9 цифр)'
    }
};

// Функция получения перевода
function getTranslation(key, lang = 'pl') {
    return translations[lang]?.[key] || translations['pl'][key] || key;
}

// Установка языка
function setLanguage(lang) {
    // Сохраняем язык в localStorage
    localStorage.setItem('language', lang);
    
    // Обновляем все элементы с атрибутом data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const translation = getTranslation(key, lang);
        
        // Если есть вложенные ссылки (<a>), сохраняем их
        if (translation.includes('<a ')) {
            el.innerHTML = translation;
        } else {
            el.textContent = translation;
        }
    });
    
    // Обновляем флаги активного языка
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.lang-btn[data-lang="${lang}"]`).classList.add('active');
    
    // Обновляем фичи премиум-пакета
    updatePremiumFeatures(lang);
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    const savedLang = localStorage.getItem('language') || 'pl';
    setLanguage(savedLang);
});

// Функция обновления фич премиум-пакета
function updatePremiumFeatures(lang) {
    const premiumFeatures = {
        pl: [
            '✅ Profesjonalne szablony CV',
            '✅ List motywacyjny w pakiecie',
            '✅ Format DOCX + PDF',
            '✅ Bezpłatna aktualizacja',
            '✅ Priorytetowa obsługa'
        ],
        en: [
            '✅ Professional CV templates',
            '✅ Cover letter included',
            '✅ DOCX + PDF format',
            '✅ Free updates',
            '✅ Priority support'
        ],
        uk: [
            '✅ Професійні шаблони резюме',
            '✅ Супровідний лист у комплекті',
            '✅ Формат DOCX + PDF',
            '✅ Безкоштовне оновлення',
            '✅ Пріоритетна підтримка'
        ]
    };
    
    const freeFeatures = {
        pl: [
            '✅ Konwersja DOCX → PDF',
            '✅ Szybka konwersja (2 sekundy)',
            '✅ Bezpłatnie',
            '⚠️ Brak szablonów premium'
        ],
        en: [
            '✅ DOCX → PDF conversion',
            '✅ Fast conversion (2 seconds)',
            '✅ Free',
            '⚠️ No premium templates'
        ],
        uk: [
            '✅ Конвертація DOCX → PDF',
            '✅ Швидка конвертація (2 секунди)',
            '✅ Безкоштовно',
            '⚠️ Немає преміум шаблонів'
        ]
    };
    
    const premiumList = document.getElementById('premiumFeatures');
    const freeList = document.getElementById('freeFeatures');
    
    if (premiumList && premiumFeatures[lang]) {
        premiumList.innerHTML = premiumFeatures[lang].map(item => `<li>${item}</li>`).join('');
    }
    
    if (freeList && freeFeatures[lang]) {
        freeList.innerHTML = freeFeatures[lang].map(item => `<li>${item}</li>`).join('');
    }
}
