# Acceptance criteria

## Hệ thống đạt nếu:
- 5 pipeline chạy độc lập
- có raw storage
- có PostgreSQL schema
- có ít nhất 1 nguồn đang chạy cho mỗi pipeline
- API phản hồi đúng format
- AI Agent trả lời được các câu hỏi mẫu
- log được job và lỗi
- có tài liệu triển khai

## Hệ thống chưa đạt nếu:
- AI Agent trả lời nhưng DB trống
- không có raw data
- không có timestamp dữ liệu
- pipeline này lỗi làm pipeline khác dừng
- không tách được logic tool/service/crawl
