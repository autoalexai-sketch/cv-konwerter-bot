FROM python:3.12-slim

WORKDIR /app

# Установка LibreOffice и зависимостей
RUN apt-get update && \
    apt-get install -y \
    libreoffice-writer \
    libreoffice-core \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всех файлов проекта
COPY . .

# Переменные окружения будут переданы через Fly.io secrets
# НЕ копируем .env файл - используем secrets от Fly.io

# Запуск бота
CMD ["python", "bot.py"]