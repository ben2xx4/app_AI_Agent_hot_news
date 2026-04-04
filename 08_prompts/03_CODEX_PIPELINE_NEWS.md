Bạn hãy triển khai pipeline 1: News Ingestion.

Mục tiêu:
- đọc RSS từ các nguồn báo điện tử Việt Nam
- lấy metadata bài viết
- crawl nội dung chi tiết nếu cần
- chuẩn hóa bài viết
- loại trùng exact duplicate
- chuẩn bị dữ liệu cho near-duplicate clustering về sau

Yêu cầu chi tiết:
1. Tạo module pipeline tin tức riêng.
2. Hỗ trợ cấu hình nhiều nguồn RSS trong file YAML/JSON.
3. Với mỗi bài viết, lưu được:
   - source_name
   - category
   - title
   - summary/description
   - published_at
   - url
   - author nếu có
   - content_raw/content_clean nếu crawl được
4. Lưu raw RSS/XML hoặc raw HTML vào raw storage.
5. Tạo hash để loại trùng exact duplicate.
6. Viết parser tách riêng cho:
   - fetch RSS
   - parse RSS item
   - fetch article detail
   - normalize article
   - save to db
7. Viết test cho ít nhất một nguồn RSS mẫu.
8. Tạo script chạy pipeline thủ công và có logging.

Kết quả mong muốn:
- có thể chạy lệnh để nạp tin mới vào database
- có bảng hoặc model article hoạt động
- có dữ liệu demo để API tin nóng dùng được
