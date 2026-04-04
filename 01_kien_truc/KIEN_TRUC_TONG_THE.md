# Kiến trúc tổng thể

## Các lớp của hệ thống

### 1. Ingestion Layer
Chứa các collector, crawler, RSS fetcher, API fetcher.
Mục tiêu:
- lấy dữ liệu theo lịch
- tách biệt logic theo nguồn
- ghi log job

### 2. Raw Storage Layer
Lưu dữ liệu nguyên bản:
- HTML
- XML RSS
- JSON API
- metadata fetch

### 3. Processing Layer
Bao gồm:
- parser
- cleaner
- normalizer
- dedup
- classifier
- enricher

### 4. Structured Storage Layer
Lưu dữ liệu sạch trong PostgreSQL.

### 5. Retrieval Layer
Lưu embedding và xây cơ chế semantic search.

### 6. Service Layer
Cung cấp API cho:
- tin nóng
- giá cả
- thời tiết
- chính sách
- giao thông
- truy vấn tổng hợp

### 7. AI Agent Layer
Nhận câu hỏi, xác định intent, gọi tool, tổng hợp câu trả lời.

## Quy tắc thiết kế
- pipeline độc lập
- parser tách khỏi fetcher
- raw và clean phải tách riêng
- service không truy cập web trực tiếp
- AI Agent không crawl trực tiếp
