Bạn hãy hoàn thiện lớp lưu trữ dữ liệu.

Mục tiêu:
- PostgreSQL là database chính
- raw storage lưu bản gốc
- thiết kế model rõ ràng, migration rõ ràng
- chuẩn bị lớp retrieval/vector cho AI về sau

Yêu cầu:
1. Đối chiếu với file schema đã có trong repo, cập nhật nếu cần.
2. Tạo ORM model hoặc migration tương ứng.
3. Thiết kế các bảng chính:
   - sources
   - crawl_jobs
   - raw_documents
   - articles
   - article_clusters
   - price_snapshots
   - weather_snapshots
   - policy_documents
   - traffic_events
   - document_embeddings (nếu dùng)
4. Tạo repository/service layer cho CRUD và query chính.
5. Tạo cơ chế lưu raw file theo cấu trúc thư mục dễ truy vết.
6. Tạo script seed dữ liệu demo.
7. Tạo test database cơ bản.

Đầu ra:
- database schema chạy được
- có migration hoặc script tạo bảng
- có seed data để demo end-to-end
