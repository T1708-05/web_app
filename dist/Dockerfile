# Sử dụng nginx image để chạy web tĩnh
FROM nginx:alpine

# Copy file web vào thư mục mặc định của nginx
COPY . /usr/share/nginx/html

# Mở cổng 80
EXPOSE 80

# Lệnh khởi động
CMD ["nginx", "-g", "daemon off;"]
