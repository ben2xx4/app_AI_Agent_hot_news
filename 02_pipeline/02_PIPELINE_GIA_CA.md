# Pipeline 2 - Giá cả

## Phạm vi
- giá xăng
- giá vàng
- tỷ giá
- giá hàng hóa có cấu trúc trong tương lai

## Các bước
1. Fetch HTML hoặc API
2. Parse bảng dữ liệu
3. Chuẩn hóa: item_type, item_name, buy_price, sell_price, unit, region, effective_at, source_name
4. Lưu raw
5. Lưu snapshot
6. So sánh với snapshot gần nhất nếu cần

## Bảng liên quan
- price_snapshots
- raw_documents
- sources

## Tần suất chạy
- 5 đến 30 phút
