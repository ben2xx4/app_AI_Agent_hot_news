Bạn hãy triển khai pipeline 4: Policy/Document Ingestion.

Mục tiêu:
- thu thập chính sách, văn bản, thông báo từ nguồn chính thức
- trích metadata quan trọng
- lưu document đã làm sạch

Yêu cầu:
1. Tạo module pipeline văn bản/chính sách riêng.
2. Chuẩn hóa các trường:
   - issuing_agency
   - doc_number
   - title
   - summary
   - issued_at
   - effective_at
   - field
   - url
   - content_clean
3. Có raw storage cho HTML/PDF metadata hoặc nội dung text gốc nếu có thể.
4. Tạo service tìm kiếm chính sách theo từ khóa/lĩnh vực/thời gian.
5. Viết logic chia document thành các đoạn để chuẩn bị RAG.
6. Có test và dữ liệu demo.

Lưu ý:
- không cần giải quyết hoàn hảo mọi site ngay từ đầu
- ưu tiên thiết kế module sạch, dễ mở rộng nguồn mới
