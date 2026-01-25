# Используем официальный Python 3.12 
FROM python:3.12-bullseye

# Force rebuild - CRITICAL FIX - no asyncio.signal anymore!
RUN echo "Build timestamp: 2026-01-25-00:58:00-UTC - FIXED asyncio.signal bug"

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем LibreOffice (для конвертации) + необходимые шрифты
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    libreoffice-core \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Создаем директорию для кеша LibreOffice
RUN mkdir -p /tmp/.libreoffice && chmod 777 /tmp/.libreoffice
ENV HOME=/tmp

# Копируем requirements.txt первым (для кэширования)
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы проекта (это будет последним, чтобы изменения кода сбрасывали кэш)
COPY . .

# Проверяем что код правильный - не должно быть asyncio.signal
RUN grep -q "import signal" bot.py && echo "✓ Correct: using signal module" || exit 1
RUN ! grep -q "asyncio.signal" bot.py && echo "✓ Correct: no asyncio.signal" || (echo "ERROR: asyncio.signal found!" && exit 1)

# Запускаем бота
CMD ["python", "bot.py"]
