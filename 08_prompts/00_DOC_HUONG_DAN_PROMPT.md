# Hướng dẫn dùng bộ prompt cho Codex

Bộ file này dùng để giao việc cho Codex theo từng giai đoạn, tránh đưa một prompt quá dài ngay từ đầu.

## Cách dùng khuyến nghị

1. Bắt đầu bằng `01_CODEX_KICKOFF_MASTER_PROMPT.md` để Codex đọc repo, hiểu mục tiêu và lập kế hoạch tổng thể.
2. Sau khi Codex tạo xong khung dự án, dùng `02_CODEX_PLAN_AND_REPO_SETUP.md` để chốt kiến trúc thư mục, công nghệ và môi trường.
3. Triển khai từng pipeline bằng các file:
   - `03_CODEX_PIPELINE_NEWS.md`
   - `04_CODEX_PIPELINE_PRICES.md`
   - `05_CODEX_PIPELINE_WEATHER.md`
   - `06_CODEX_PIPELINE_POLICY.md`
   - `07_CODEX_PIPELINE_TRAFFIC.md`
4. Sau đó dùng:
   - `08_CODEX_DATABASE_AND_STORAGE.md`
   - `09_CODEX_BACKEND_API.md`
   - `10_CODEX_AI_AGENT_AND_RAG.md`
5. Cuối cùng chạy:
   - `11_CODEX_TESTING_AND_E2E.md`
   - `12_CODEX_DEPLOYMENT_AND_HANDOFF.md`

## Nguyên tắc khi làm việc với Codex

- Yêu cầu Codex đọc kỹ README, START_HERE.txt, schema SQL và toàn bộ thư mục hướng dẫn trước khi code.
- Yêu cầu Codex ghi rõ kế hoạch trước khi sửa code lớn.
- Yêu cầu Codex commit theo từng phần nhỏ hoặc ít nhất ghi changelog nội bộ sau mỗi nhóm việc.
- Yêu cầu Codex luôn tạo test, seed data và script chạy demo.
- Yêu cầu Codex không bỏ qua xử lý lỗi, logging, timeout, retry, rate limit.

## Cách giao việc an toàn

- Giao theo từng pha.
- Sau mỗi prompt, yêu cầu Codex báo:
  - đã làm gì
  - file nào đã tạo/sửa
  - cách chạy kiểm thử
  - phần nào còn dang dở

## Câu nhắc thêm khi dùng Codex

Bạn có thể thêm vào cuối bất kỳ prompt nào đoạn sau:

"Trước khi code, hãy đọc toàn bộ file hướng dẫn trong repo này. Nếu có điểm mơ hồ, hãy tự đưa ra giả định hợp lý, ghi rõ giả định đó trong README hoặc changelog, sau đó tiếp tục triển khai thay vì dừng lại."
