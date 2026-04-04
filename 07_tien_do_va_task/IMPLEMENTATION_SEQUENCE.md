# Trình tự triển khai end-to-end

## Giai đoạn 1 - Nền móng
1. Tạo repo
2. Tạo cấu trúc code
3. Cấu hình PostgreSQL
4. Tạo schema SQL
5. Tạo logging và config

## Giai đoạn 2 - Storage
1. Tạo raw storage abstraction
2. Tạo repository layer
3. Tạo job logging

## Giai đoạn 3 - Pipeline Tin tức
1. Fetch RSS
2. Parse RSS
3. Crawl content chi tiết
4. Lưu articles
5. Dedup cơ bản

## Giai đoạn 4 - Pipeline Giá cả
1. Parse giá vàng
2. Parse giá xăng
3. Parse tỷ giá
4. Lưu snapshots

## Giai đoạn 5 - Pipeline Thời tiết
1. Parse dữ liệu theo địa phương
2. Lưu weather snapshots

## Giai đoạn 6 - Pipeline Chính sách
1. Parse danh sách văn bản
2. Parse nội dung
3. Lưu policy documents

## Giai đoạn 7 - Pipeline Giao thông
1. Parse tin sự kiện giao thông
2. Lưu traffic events

## Giai đoạn 8 - API
1. Tạo endpoints theo nhóm
2. Thêm validation
3. Thêm test API

## Giai đoạn 9 - AI Agent
1. Thiết kế system prompt
2. Khai báo tools
3. Tạo chat endpoint
4. Test câu hỏi thật

## Giai đoạn 10 - Nghiệm thu
1. Chạy pipeline
2. Dữ liệu vào DB
3. API phản hồi
4. AI trả lời được các câu hỏi mẫu
