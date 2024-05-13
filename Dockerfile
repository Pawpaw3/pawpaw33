# Используем базовый образ Python
FROM python:3.9-slim

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6

# Устанавливаем рабочий каталог
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем остальные файлы приложения
COPY . .

# Запуск бота
CMD ["python", Tebot.py"]
