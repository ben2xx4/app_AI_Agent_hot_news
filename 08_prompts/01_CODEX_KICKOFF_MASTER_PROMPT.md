Bạn là Codex, coding agent chính cho dự án này. Hãy triển khai toàn bộ hệ thống end-to-end dựa trên các tài liệu hướng dẫn sẵn có trong repo.

Nhiệm vụ của bạn:
1. Đọc toàn bộ các file hướng dẫn trong repo, đặc biệt là:
   - START_HERE.txt
   - README.md
   - 00_tong_quan/*
   - 01_kien_truc/*
   - 02_pipeline/*
   - 03_du_lieu_va_db/*
   - 04_backend_api/*
   - 05_ai_agent/*
   - 10_kiem_thu/*
2. Tóm tắt lại mục tiêu hệ thống bằng tiếng Việt trong tối đa 20 dòng.
3. Lập kế hoạch triển khai theo các pha rõ ràng:
   - khởi tạo repo và môi trường
   - tạo schema database
   - xây 5 pipeline ingestion
   - service layer và API
   - AI Agent + RAG
   - test và demo end-to-end
   - docker hóa và bàn giao
4. Tạo hoặc cập nhật file `AGENTS.md` ở thư mục gốc của dự án để chuẩn hóa cách Codex làm việc trong repo này.
5. Chỉ ra những file/directory còn thiếu cần tạo thêm để có thể code end-to-end.
6. Sau khi lập kế hoạch, mới bắt đầu code.

Ràng buộc:
- Dùng Python cho backend, crawler và pipeline.
- Dùng PostgreSQL làm database chính.
- Có raw storage riêng cho dữ liệu gốc.
- Có logging, retry, timeout, rate limiting ở các pipeline.
- Có seed/demo data nếu một số nguồn thật khó truy cập trong lúc phát triển.
- Tất cả comment và tài liệu nội bộ viết bằng tiếng Việt.

Đầu ra mong muốn của bước này:
- kế hoạch triển khai rõ ràng
- cây thư mục dự kiến
- danh sách package cần dùng
- danh sách môi trường cần cấu hình
- file AGENTS.md ban đầu

Chưa cần code toàn bộ ngay. Hãy ưu tiên đọc hiểu repo, đề xuất kế hoạch, rồi mới triển khai theo từng pha.
