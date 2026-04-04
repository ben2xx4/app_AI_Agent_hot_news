Bạn hãy triển khai lớp AI hỏi đáp cho hệ thống.

Mục tiêu:
- dùng OpenAI API làm lớp hỏi đáp thông minh
- AI hiểu câu hỏi tiếng Việt
- AI gọi đúng tool nội bộ
- có thể dùng RAG cho câu hỏi tổng hợp hoặc document dài

Yêu cầu:
1. Thiết kế agent theo mô hình tool-calling.
2. Các tool tối thiểu:
   - get_hot_news
   - search_news
   - get_latest_price
   - compare_price
   - get_weather
   - search_policy
   - get_traffic_updates
3. Tạo lớp nhận diện intent.
4. Với câu factual ngắn, ưu tiên query DB/API trực tiếp.
5. Với câu tổng hợp dài, dùng retrieval/RAG nếu cần.
6. Trả lời bằng tiếng Việt.
7. Câu trả lời nên có:
   - nội dung chính
   - thời điểm cập nhật
   - nguồn dữ liệu
8. Tạo prompt hệ thống cho agent trong code hoặc file cấu hình.
9. Viết test/demo conversation tối thiểu 10 câu.

Lưu ý:
- không để model tự crawl web trực tiếp làm nguồn chính
- dữ liệu chính phải đến từ các pipeline của hệ thống
