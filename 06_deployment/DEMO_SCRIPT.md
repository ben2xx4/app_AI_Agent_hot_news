# Demo script

## Mục tiêu
File này dùng khi cần demo nhanh hệ thống cho giảng viên, khách xem demo hoặc bàn giao kỹ thuật.

## Chuẩn bị trước demo
### 1. Tạo `.env`
```bash
cp .env.production.example .env
```

### 2. Bật full stack Docker
```bash
docker compose up -d postgres api ui scheduler
docker compose --profile demo run --rm seed_demo
docker compose --profile ops run --rm refresh_live_prices
```

### 3. Kiểm tra nhanh
```bash
curl http://127.0.0.1:8000/health
```

Kỳ vọng:
- `status = ok`
- `database_driver = postgresql+psycopg`

## Trình tự demo khuyến nghị
### Bước 1. Mở dashboard
- `http://127.0.0.1:8501`

Giới thiệu nhanh:
- dashboard Streamlit
- tình trạng hệ thống
- sức khỏe nguồn dữ liệu
- data browser
- chat AI

### Bước 2. Xem tin, giá, thời tiết
Nói ngắn:
- hệ thống đang có 5 pipeline ingestion
- dữ liệu được đẩy vào PostgreSQL
- UI đang đọc từ API và một phần dữ liệu trực tiếp cho data browser

### Bước 3. Mở Data Browser
Cho xem:
- `articles`
- `price_snapshots`
- `weather_snapshots`
- `policy_documents`
- `traffic_events`

Điểm nhấn:
- không cần SQL vẫn xem được dữ liệu
- dữ liệu có tiếng Việt có dấu

### Bước 4. Demo chat
Ví dụ câu hỏi:
- `Tin hot hôm nay là gì?`
- `Giá vàng SJC hôm nay bao nhiêu?`
- `Thời tiết Hải Phòng hôm nay thế nào?`
- `Có văn bản nào về học đường không?`
- `Có tuyến đường nào đang bị cấm không?`

Điểm nhấn:
- hỏi đáp bằng tiếng Việt
- có fallback nội bộ khi OpenAI không sẵn sàng
- câu trả lời xuống dòng dễ đọc

### Bước 5. Demo scheduler
```bash
docker compose exec scheduler python scripts/run_scheduler.py --show-status
```

Điểm nhấn:
- mỗi source có lịch chạy riêng
- có `health_state`
- có `failure_streak`
- có `attention_sources`

### Bước 6. Demo pipeline chạy tay
```bash
docker compose exec api python scripts/run_pipeline.py --pipeline news
docker compose exec api python scripts/run_pipeline.py --pipeline traffic
```

Điểm nhấn:
- có thể ingest theo từng pipeline hoặc từng source
- không cần chạy toàn bộ stack lại từ đầu

## Các thông điệp nên nhấn mạnh khi demo
- hệ thống có 5 pipeline ingestion thật
- có PostgreSQL và raw storage
- có API backend
- có AI chat tiếng Việt
- có scheduler local
- có retention + cleanup
- có retrieval experimental cho `news` và `policy`

## Nếu OpenAI lỗi trong lúc demo
Nói rõ:
- hệ thống vẫn chạy
- chat sẽ fallback về agent nội bộ
- đây là hành vi chủ động, không phải crash

## Nếu cần reset demo
```bash
docker compose --profile demo run --rm seed_demo
```

Nếu vừa reseed và muốn khôi phục giá live mới nhất:
```bash
docker compose --profile ops run --rm refresh_live_prices
```

Nếu vừa reseed và muốn nạp lại toàn bộ dữ liệu live:
```bash
docker compose --profile ops run --rm refresh_live_data
```

## Kết thúc demo
Nếu cần giữ dữ liệu:
```bash
docker compose down
```

Nếu cần xóa sạch:
```bash
docker compose down -v
```
