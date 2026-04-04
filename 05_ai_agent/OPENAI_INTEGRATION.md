# Tích hợp OpenAI API

## Vai trò
OpenAI API dùng để:
- hiểu câu hỏi tiếng Việt
- phân loại intent
- chọn tool
- viết lại kết quả thành câu trả lời tự nhiên

## Không nên dùng để
- thay thế crawler
- thay thế scheduler
- thay thế database

## Luồng
1. User hỏi
2. Model đọc system prompt
3. Model chọn tool
4. Backend gọi service
5. Tool trả JSON
6. Model tạo câu trả lời cuối
