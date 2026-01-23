# Используем официальный Python 3.14 
FROM python:3.12-bullseye

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем LibreOffice (для конвертации)
RUN apt-get update && apt-get install -y \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Force rebuild on code change (dummy line)
RUN echo "Rebuild trigger: 2026-01-23"

# Запускаем бота
CMD ["python", "bot.py"]
