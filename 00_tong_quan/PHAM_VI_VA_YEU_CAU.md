# Phạm vi và yêu cầu

## Yêu cầu chức năng
1. Tự động thu thập dữ liệu theo lịch
2. Lưu dữ liệu thô và dữ liệu chuẩn hóa
3. Phân loại dữ liệu theo 5 pipeline
4. Loại trùng exact duplicate và near duplicate cơ bản
5. Hỗ trợ tìm kiếm theo từ khóa và ngữ nghĩa
6. Cung cấp API để frontend hoặc chatbot gọi
7. Hỗ trợ AI Agent hỏi đáp bằng tiếng Việt
8. Lưu lịch sử job và lỗi

## Yêu cầu phi chức năng
- Dễ mở rộng thêm nguồn mới
- Dễ thay parser khi nguồn thay đổi
- Có khả năng chạy lại job
- Tách biệt giữa ingestion, storage, service, agent
- Có kiểm thử cơ bản
- Có logging rõ ràng

## Tại sao phải chia 5 pipeline
Vì các nhóm dữ liệu khác nhau về:
- cấu trúc nội dung
- tốc độ cập nhật
- cách parse
- cách dedup
- cách truy vấn
- cách AI Agent sử dụng

Nếu dồn vào 1 pipeline, hệ thống khó bảo trì, dễ hỏng dây chuyền, khó đặt lịch và khó tối ưu riêng.
