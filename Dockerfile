# Dockerfile
FROM python:3.11-slim

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Установка pip-зависимостей
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Указываем переменные среды
ENV PYTHONUNBUFFERED=1

# Запускаем бота
CMD ["python", "main.py"]
