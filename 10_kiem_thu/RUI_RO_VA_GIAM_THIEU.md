# Rủi ro và cách giảm thiểu

## 1. Nguồn đổi giao diện
Giải pháp:
- tách parser riêng
- lưu raw để debug
- có test parser

## 2. Dữ liệu trùng quá nhiều
Giải pháp:
- hash chuẩn hóa
- thêm rule near duplicate
- cluster thay vì xóa ngay

## 3. AI Agent trả lời sai
Giải pháp:
- dùng tool calling
- không cho truy cập web trực tiếp
- buộc trả lời từ dữ liệu nội bộ

## 4. Scheduler chạy lỗi âm thầm
Giải pháp:
- log crawl_jobs
- alert khi job fail nhiều lần

## 5. Data cũ nhưng user hỏi hôm nay
Giải pháp:
- luôn kèm updated_at
- cảnh báo khi dữ liệu cũ hơn ngưỡng
