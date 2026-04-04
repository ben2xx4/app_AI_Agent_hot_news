# Pipeline 5 - Giao thông / di chuyển

## Phạm vi
- cấm đường
- điều chỉnh luồng tuyến
- sự cố giao thông
- tin nổi bật liên quan di chuyển

## Các bước
1. Fetch tin giao thông
2. Parse: title, event_type, location, start_time, end_time, description, source_name
3. Chuẩn hóa địa điểm
4. Lưu raw
5. Lưu traffic_events

## Bảng liên quan
- traffic_events
- raw_documents
- sources

## Tần suất chạy
- 10 đến 30 phút
