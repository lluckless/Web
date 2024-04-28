# Використання офіційного образу Python
FROM python:3.12

# Встановлення залежностей
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

# Копіювання додатку до контейнера
COPY . /app

# Встановлення змінних середовища
ENV HTTP_PORT=3003
ENV UDP_PORT=5005

# Директорія для зберігання даних поза контейнером
VOLUME /app/storage

# Виконання HTTP та UDP серверів у потоках
CMD ["python", "main.py"]
