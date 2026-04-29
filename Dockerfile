FROM python:3.9
# Устанавливаем рабочую директорию
WORKDIR /app
# Копируем все файлы
COPY . .
# Устанавливаем библиотеки (на всякий случай)
RUN pip install --no-cache-dir flask flask-cors requests
# Запускаем ваш основной файл
CMD ["python", "app.py"]
