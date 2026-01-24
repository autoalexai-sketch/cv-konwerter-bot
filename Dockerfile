# Используем официальный Python 3.12 
FROM python:3.12-bullseye

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

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

# Force rebuild on code change (dummy line)
RUN echo "Rebuild trigger: 2026-01-24-fix-v2-signal-fixed"

# Запускаем бота
CMD ["python", "bot.py"]
