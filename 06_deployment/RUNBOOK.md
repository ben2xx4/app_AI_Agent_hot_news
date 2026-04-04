# Runbook

## Khởi động cục bộ
1. Cấu hình `.env`
2. Chạy `docker compose up -d`
3. Tạo database schema
4. Chạy các pipeline theo lệnh CLI hoặc scheduler
5. Khởi động API
6. Test endpoint `/health`
7. Test endpoint `/api/chat/query`

## Kiểm tra nhanh
- PostgreSQL kết nối được
- raw storage ghi được file
- crawler lấy được ít nhất 1 nguồn
- API query được
- AI Agent gọi được tool
