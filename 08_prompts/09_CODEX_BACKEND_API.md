Bạn hãy triển khai backend API cho hệ thống.

Mục tiêu:
- cung cấp API cho frontend hoặc AI Agent gọi
- tách bạch controller/router và service

Yêu cầu:
1. Dùng FastAPI.
2. Tạo các endpoint tối thiểu:
   - GET /health
   - GET /news/hot
   - GET /news/search
   - GET /prices/latest
   - GET /prices/compare
   - GET /weather/latest
   - GET /policy/search
   - GET /traffic/latest
   - POST /chat/query
3. Chuẩn hóa response JSON.
4. Có validation input.
5. Có error handling chuẩn.
6. Có docs OpenAPI chạy được.
7. Viết test cho các endpoint chính.

Yêu cầu thêm:
- response cần có trường source, updated_at nếu phù hợp
- API phải đủ để AI Agent có thể dùng như một tool layer
