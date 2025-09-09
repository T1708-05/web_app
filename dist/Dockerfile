# Sử dụng nginx image
FROM nginx:alpine

# Xóa file mặc định của nginx
RUN rm -rf /usr/share/nginx/html/*

# Copy toàn bộ code web vào thư mục nginx
COPY . /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Khởi động nginx
CMD ["nginx", "-g", "daemon off;"]
