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