Bạn hãy thực hiện pha khởi tạo dự án.

Mục tiêu:
- tạo cấu trúc thư mục chuẩn cho hệ thống data platform + AI Agent
- cấu hình môi trường local/dev
- tạo requirements hoặc pyproject
- tạo file `.env.example`
- tạo file cấu hình logging
- tạo file cấu hình nguồn dữ liệu mẫu
- tạo thư mục raw storage, processed storage, logs, scripts, tests

Yêu cầu:
1. Tạo cây thư mục source code rõ ràng, ví dụ:
   - app/
   - app/pipelines/
   - app/services/
   - app/db/
   - app/api/
   - app/agent/
   - app/models/
   - app/utils/
   - config/
   - storage/raw/
   - storage/processed/
   - logs/
   - scripts/
   - tests/
2. Chọn một framework backend phù hợp, ưu tiên FastAPI.
3. Tạo cấu hình PostgreSQL connection.
4. Tạo base settings theo môi trường dev/test/prod nếu hợp lý.
5. Tạo script khởi tạo database.
6. Tạo README chạy local.
7. Tạo Makefile hoặc script shell tiện dụng nếu phù hợp.

Sau khi xong:
- liệt kê toàn bộ file đã tạo
- giải thích ngắn gọn vai trò từng thư mục
- nêu lệnh chạy local đầu tiên
