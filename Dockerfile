# Sử dụng image Python chính thức
FROM python:3.11-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt vào thư mục làm việc
COPY requirements.txt .

# Cài đặt các dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào thư mục làm việc
COPY . .

# Mở cổng 8501 để Streamlit có thể truy cập
EXPOSE 8501

# Chạy ứng dụng Streamlit
CMD ["streamlit", "run", "Home.py"]