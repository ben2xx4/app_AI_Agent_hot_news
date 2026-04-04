# AI Agent là gì trong hệ thống này

AI Agent không phải crawler.
AI Agent là lớp điều phối thông minh đứng trên dữ liệu đã thu thập.

## Agent làm gì
1. Nhận câu hỏi người dùng
2. Xác định intent
3. Gọi đúng tool nội bộ
4. Tổng hợp kết quả
5. Trả lời bằng tiếng Việt
6. Nêu thời điểm cập nhật và nguồn khi cần

## Agent không nên làm gì
- không tự crawl web chính
- không tự kết luận từ nguồn chưa được hệ thống thu thập
- không truy cập DB bằng chuỗi SQL do model tự bịa
