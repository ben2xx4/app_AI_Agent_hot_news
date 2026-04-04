# Kế hoạch kiểm thử end-to-end

## Mục tiêu
Xác nhận toàn bộ hệ thống hoạt động từ crawl đến AI.

## Kịch bản 1 - Tin tức
1. Chạy pipeline tin tức
2. Kiểm tra bài viết vào DB
3. Gọi API `/api/news/hot`
4. Hỏi AI: "Tin hot hôm nay là gì?"
5. Kiểm tra câu trả lời có nguồn và thời điểm

## Kịch bản 2 - Giá vàng
1. Chạy pipeline giá cả
2. Kiểm tra `price_snapshots`
3. Gọi API `/api/prices/latest?item=vang`
4. Hỏi AI: "Giá vàng hôm nay thế nào?"
5. Kiểm tra câu trả lời khớp dữ liệu DB

## Kịch bản 3 - Thời tiết
1. Chạy pipeline thời tiết
2. Kiểm tra `weather_snapshots`
3. Hỏi AI: "Hà Nội hôm nay có mưa không?"

## Kịch bản 4 - Chính sách
1. Chạy pipeline chính sách
2. Kiểm tra `policy_documents`
3. Hỏi AI: "Có chính sách mới nào về giáo dục không?"

## Kịch bản 5 - Giao thông
1. Chạy pipeline giao thông
2. Kiểm tra `traffic_events`
3. Hỏi AI: "Có thông báo giao thông nào đáng chú ý không?"
