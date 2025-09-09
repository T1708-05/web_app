# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn
COPY . /app

# Chuẩn bị thư mục dữ liệu (app cũng tự tạo, nhưng thêm cho chắc)
RUN mkdir -p /app/data/uploads /app/data/hidden_images

# Render sẽ đặt PORT động; fallback 8080 nếu chạy local
ENV PORT=8080

# Chạy bằng gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 app:app
