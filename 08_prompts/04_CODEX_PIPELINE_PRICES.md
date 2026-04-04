Bạn hãy triển khai pipeline 2: Structured Price Ingestion.

Phạm vi:
- giá xăng
- giá vàng
- tỷ giá

Yêu cầu:
1. Tạo pipeline riêng cho dữ liệu giá cả.
2. Thiết kế mô hình snapshot để lưu giá theo thời điểm.
3. Hỗ trợ parser tách riêng theo từng loại nguồn:
   - parser giá xăng
   - parser giá vàng
   - parser tỷ giá
4. Chuẩn hóa dữ liệu về một cấu trúc chung:
   - item_type
   - item_name
   - region nếu có
   - buy_price
   - sell_price
   - unit
   - effective_at
   - source_name
5. Lưu raw HTML/JSON gốc.
6. Viết logic so sánh với snapshot gần nhất để biết tăng/giảm.
7. Tạo service truy vấn giá mới nhất và service so sánh với hôm trước/lần trước.
8. Có test và seed data.

Đầu ra:
- pipeline chạy được độc lập
- bảng snapshot giá hoạt động
- service trả dữ liệu đủ cho chatbot/API
