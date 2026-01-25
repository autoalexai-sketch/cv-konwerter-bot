# 🚀 CV Konwerter - Веб-приложение + Telegram бот

## 📋 Что это?

Полноценная платформа для конвертации резюме DOCX → PDF с монетизацией.

### Два канала доступа:
1. **Веб-сайт** - https://your-site.onrender.com
2. **Telegram бот** - @cv_konwerter_bot (работает на Fly.io)

---

## 🎯 Функции

### Бесплатно:
- ✅ Конвертация DOCX → PDF
- ✅ Без лимитов
- ✅ Без регистрации

### Premium (39 zł):
- 💎 5 профессиональных шаблонов CV
- 💎 Шаблон сопроводительного письма
- 💎 Соответствие GDPR
- 💎 Мгновенная отправка на email

---

## 🛠️ Локальный запуск

### Установка зависимостей:
```bash
pip install -r requirements.txt
```

### Запуск веб-приложения:
```bash
python web_app.py
```

Откройте: http://localhost:5000

### Запуск Telegram бота:
```bash
python bot.py
```

---

## 🚀 Деплой

### Веб-приложение на Render.com:
1. Создайте аккаунт на render.com
2. New → Web Service
3. Connect GitHub репозиторий
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python web_app.py`
6. Environment Variables:
   - `PYTHON_VERSION`: `3.12`
7. Deploy!

### Telegram бот на Fly.io:
Уже работает! ✅
- URL: https://cv-konwerter-bot.fly.dev/
- Деплой: `flyctl deploy -a cv-konwerter-bot`

---

## 📂 Структура проекта

```
webapp/
├── bot.py                  # Telegram бот
├── web_app.py             # Flask веб-приложение
├── web/
│   ├── templates/
│   │   └── index.html     # Главная страница
│   └── static/
│       ├── js/
│       │   └── main.js    # JavaScript
│       └── uploads/       # Временные файлы
├── requirements.txt       # Зависимости
├── Dockerfile            # Docker для Telegram бота
└── fly.toml              # Конфигурация Fly.io
```

---

## 🔧 Технологии

- **Backend**: Flask (Python 3.12)
- **Telegram**: aiogram 3.x
- **Конвертация**: LibreOffice
- **Frontend**: HTML + TailwindCSS + JavaScript
- **Хостинг**: Render.com (веб) + Fly.io (бот)

---

## 📝 TODO

- [ ] Интеграция Przelewy24
- [ ] Создание шаблонов CV
- [ ] LinkedIn автопостинг
- [ ] Email-уведомления

---

## 📞 Контакты

При возникновении вопросов обращайтесь к разработчику.
