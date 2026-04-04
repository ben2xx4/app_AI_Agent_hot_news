# Pipeline 3 - Thời tiết

## Phạm vi
- dự báo hôm nay
- dự báo nhiều ngày
- cảnh báo thời tiết
- theo địa phương

## Các bước
1. Fetch nguồn thời tiết
2. Parse dữ liệu theo địa phương
3. Chuẩn hóa: location, forecast_time, min_temp, max_temp, humidity, wind, weather_text, warning_text
4. Lưu raw
5. Lưu weather_snapshots

## Bảng liên quan
- weather_snapshots
- raw_documents
- sources

## Tần suất chạy
- 30 đến 60 phút
