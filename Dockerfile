FROM python:3.9

# Устанавливаем библиотеки
RUN pip install --no-cache-dir flask requests

# Копируем все файлы в папку /app
WORKDIR /app
COPY . .

# Запускаем наш сервер
CMD ["python", "app.py"]
