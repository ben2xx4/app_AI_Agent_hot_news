# Đề tài

**Xây dựng nền tảng dữ liệu tự động thu thập và tích hợp thông tin trực tuyến tại Việt Nam, hỗ trợ AI Agent hỏi đáp thông tin trong ngày**

## Bài toán
Hệ thống cần thu thập dữ liệu từ nhiều nguồn khác nhau trên Internet như:
- tin nóng
- giá cả
- thời tiết
- giao thông
- chính sách
- tài chính
- giải trí
- sức khỏe
- xã hội
- giáo dục

Sau khi thu thập, hệ thống phải:
1. lưu trữ dữ liệu thô
2. làm sạch và chuẩn hóa
3. loại trùng lặp
4. tổ chức dữ liệu để truy vấn nhanh
5. hỗ trợ AI Agent trả lời câu hỏi bằng tiếng Việt

## Phạm vi MVP
Bản MVP bắt buộc có:
- 5 pipeline độc lập
- PostgreSQL
- raw storage
- dedup cơ bản
- REST API
- OpenAI API để hỏi đáp bằng tool calling
- ít nhất 8 nguồn dữ liệu
- chạy scheduler tự động

## Ngoài phạm vi MVP
- realtime giao thông cấp bản đồ
- fake news detection hoàn chỉnh
- ranking phức tạp dùng mô hình học sâu riêng
- mobile app native
- hệ thống phân quyền nhiều tenant

## Tiêu chí thành công
- Hệ thống có thể trả lời đúng các câu hỏi phổ biến:
  - Tin hot hôm nay là gì?
  - Giá xăng hôm nay bao nhiêu?
  - Giá vàng hôm nay tăng hay giảm?
  - Hà Nội hôm nay có mưa không?
  - Có chính sách mới nào về giáo dục không?
- Dữ liệu có timestamp cập nhật
- Câu trả lời có nguồn
- Có log và khả năng debug dữ liệu đầu vào
