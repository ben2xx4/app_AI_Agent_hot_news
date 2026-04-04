Bạn hãy triển khai pipeline 5: Traffic/Event Ingestion.

Mục tiêu:
- thu thập thông tin giao thông đi lại, cấm đường, sự cố, điều chỉnh luồng tuyến
- lưu theo dạng sự kiện có thời gian và địa điểm

Yêu cầu:
1. Tạo module pipeline giao thông riêng.
2. Chuẩn hóa cấu trúc dữ liệu:
   - title
   - event_type
   - city_or_region
   - start_time
   - end_time
   - description
   - source_name
   - url
3. Lưu raw data vào raw storage.
4. Tạo service lấy danh sách sự kiện giao thông mới nhất theo khu vực.
5. Có khả năng lọc theo thành phố/tỉnh nếu dữ liệu cho phép.
6. Có test và seed data.

Mục tiêu cuối:
- người dùng có thể hỏi kiểu “Hôm nay có thông tin giao thông gì đáng chú ý ở TP.HCM?”
