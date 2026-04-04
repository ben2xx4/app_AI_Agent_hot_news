Bạn hãy triển khai pipeline 3: Weather Ingestion.

Mục tiêu:
- lấy dữ liệu thời tiết theo địa phương
- hỗ trợ forecast và cảnh báo nếu nguồn có
- lưu snapshot theo thời điểm

Yêu cầu:
1. Tạo module pipeline thời tiết riêng.
2. Chuẩn hóa cấu trúc dữ liệu:
   - location
   - forecast_time
   - min_temp
   - max_temp
   - humidity
   - wind
   - warning_text
   - source_name
3. Tạo raw storage cho dữ liệu thô.
4. Tạo service lấy thời tiết mới nhất theo địa phương.
5. Tạo service lấy cảnh báo thời tiết mới nhất.
6. Có test và có dữ liệu mẫu fallback nếu nguồn thật thay đổi format.

Lưu ý:
- viết code sao cho về sau dễ thêm nhiều nguồn thời tiết khác nhau.
