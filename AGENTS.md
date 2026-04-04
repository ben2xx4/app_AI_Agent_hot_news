# AGENTS.md

## Mục tiêu repo
Repo này xây dựng hệ thống nền tảng dữ liệu cho tin tức và thông tin hằng ngày tại Việt Nam, gồm 5 pipeline ingestion và một lớp AI hỏi đáp.

## Cách Codex nên làm việc trong repo này
1. Đọc `START_HERE.txt` và `README.md` trước khi sửa code.
2. Với tác vụ lớn, lập kế hoạch trước rồi mới triển khai.
3. Triển khai theo thứ tự:
   - database và storage
   - 5 pipeline
   - service layer và API
   - AI Agent + RAG
   - test, demo, deployment
4. Mọi comment, README nội bộ và tài liệu kỹ thuật viết bằng tiếng Việt.
5. Ưu tiên code dễ đọc, module nhỏ, test được.
6. Không sửa bừa toàn repo trong một lần nếu có thể tách theo từng pha.
7. Luôn thêm logging, timeout, retry, error handling ở các pipeline.
8. Khi thiếu nguồn thật hoặc trang thay đổi format, thêm dữ liệu seed/demo để bảo toàn luồng end-to-end.
9. Sau mỗi nhóm việc, cập nhật README hoặc changelog ngắn.

## Định nghĩa hoàn thành
Một tác vụ chỉ được xem là hoàn thành khi:
- code chạy được
- có test cơ bản
- có hướng dẫn chạy
- có ghi rõ file đã tạo hoặc sửa
