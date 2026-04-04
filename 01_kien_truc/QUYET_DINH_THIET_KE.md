# Các quyết định thiết kế chính

## 1. Dùng 5 pipeline thay vì 1 pipeline
Lý do:
- khác cấu trúc dữ liệu
- khác lịch cập nhật
- khác cách parse
- khác cách dedup
- khác cách truy vấn

## 2. Dùng PostgreSQL
Lý do:
- phù hợp dữ liệu có cấu trúc
- hỗ trợ JSONB
- dễ mở rộng với pgvector
- đủ tốt cho MVP

## 3. Dùng raw storage riêng
Lý do:
- parser có thể lỗi khi nguồn đổi HTML
- cần lưu bằng chứng dữ liệu gốc
- có thể reprocess mà không phải crawl lại

## 4. Dùng AI Agent theo tool calling
Lý do:
- kiểm soát câu trả lời
- tránh hallucination
- dễ tách logic nghiệp vụ

## 5. Không để AI Agent crawl trực tiếp
Lý do:
- khó kiểm soát nguồn
- chậm
- khó debug
- không đúng trọng tâm data platform
