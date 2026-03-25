FROM python:3.10-slim

# Устанавливаем системные зависимости для psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# Открываем порты: 8501 для Streamlit, 8000 для FastAPI
EXPOSE 8501
EXPOSE 8000

# Создаем скрипт для запуска обоих сервисов
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]