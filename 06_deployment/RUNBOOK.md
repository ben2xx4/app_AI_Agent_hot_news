# Runbook triển khai và vận hành local/full-stack

## Mục tiêu
File này dành cho trường hợp cần dựng toàn bộ stack bằng Docker để:
- demo nhanh
- bàn giao cho người khác
- kiểm tra luồng vận hành gần giống production hơn local chạy tay

Compose chuẩn của repo hiện tại:
- root: `docker-compose.yml`
- biến thể triển khai: `06_deployment/docker-compose.yml`

## Thành phần trong stack Docker
- `postgres`: PostgreSQL chính
- `api`: FastAPI backend
- `ui`: Streamlit dashboard + chat
- `scheduler`: scheduler local chạy vòng lặp
- `seed_demo`: service chạy một lần để nạp demo data

## Chuẩn bị
### 1. Tạo file môi trường
```bash
cp .env.production.example .env
```

Nếu chỉ cần demo nội bộ, có thể để trống:
- `OPENAI_API_KEY`

Nếu muốn dùng OpenAI thật:
- điền `OPENAI_API_KEY`

### 2. Kiểm tra port
Các port mặc định:
- `5432`: PostgreSQL
- `8000`: API
- `8501`: UI

Nếu cổng đang bị chiếm, dừng process cũ trước khi `docker compose up`.

## Khởi động full stack
### 1. Bật PostgreSQL, API, UI, scheduler
```bash
docker compose up -d postgres api ui scheduler
```

### 2. Nạp dữ liệu demo một lần
```bash
docker compose --profile demo run --rm seed_demo
```

Lưu ý:
- `seed_demo` sẽ reset dữ liệu nghiệp vụ rồi nạp lại 5 pipeline ở chế độ `--demo-only`
- không cần chạy lặp lại sau mỗi lần restart container
- nếu muốn kéo lại riêng dữ liệu giá live sau khi seed demo, dùng:
```bash
docker compose --profile ops run --rm refresh_live_prices
```
- nếu muốn kéo lại toàn bộ dữ liệu live sau khi seed demo, dùng:
```bash
docker compose --profile ops run --rm refresh_live_data
```

## Kiểm tra nhanh sau khi lên stack
### 1. Kiểm tra container
```bash
docker compose ps
```

### 2. Kiểm tra API health
```bash
curl http://127.0.0.1:8000/health
```

Kỳ vọng:
- `status = ok`
- `database_driver = postgresql+psycopg`

### 3. Kiểm tra UI
Mở:
- `http://127.0.0.1:8501`

### 4. Kiểm tra endpoint dữ liệu
```bash
curl "http://127.0.0.1:8000/news/hot?limit=3"
curl "http://127.0.0.1:8000/prices/latest?item_name=gia-vang-sjc"
curl "http://127.0.0.1:8000/weather/latest?location=Hai%20Phong"
curl "http://127.0.0.1:8000/policies/search?query=hoc%20duong"
curl "http://127.0.0.1:8000/traffic/latest?limit=3"
```

### 5. Kiểm tra chat
```bash
curl -X POST http://127.0.0.1:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Tin hot hôm nay là gì?"}'
```

## Chạy lệnh vận hành thường dùng
### Xem log API
```bash
docker compose logs -f api
```

### Xem log scheduler
```bash
docker compose logs -f scheduler
```

### Nếu scheduler đứng ở `runs: []` dù container vẫn Up
Đây thường là dấu hiệu file `scheduler_status.json` cũ đang làm lệch lịch chạy.

Xử lý:
```bash
rm data/processed/scheduler_status.json
docker compose restart scheduler
docker compose logs -f scheduler
```

Nếu muốn nạp lại dữ liệu ngay:
```bash
docker compose --profile ops run --rm refresh_live_data
```

### Chạy ingest tay trong container API
```bash
docker compose exec api python scripts/run_pipeline.py --pipeline news
docker compose exec api python scripts/run_pipeline.py --pipeline price
docker compose exec api python scripts/run_pipeline.py --pipeline traffic
```

### Làm mới riêng giá live
```bash
docker compose --profile ops run --rm refresh_live_prices
```

### Chạy cleanup dry-run
```bash
docker compose exec api python scripts/run_cleanup.py
```

### Chạy cleanup thật
```bash
docker compose exec api python scripts/run_cleanup.py --apply
```

### Xem scheduler status
```bash
docker compose exec scheduler python scripts/run_scheduler.py --show-status
```

## Chu kỳ khởi động khuyến nghị
### Demo chuẩn
1. `cp .env.production.example .env`
2. `docker compose up -d postgres api ui scheduler`
3. `docker compose --profile demo run --rm seed_demo`
4. `curl http://127.0.0.1:8000/health`
5. mở `http://127.0.0.1:8501`

### Khi cần reseed
```bash
docker compose --profile demo run --rm seed_demo
```

### Khi chỉ cần cập nhật lại giá live sau reseed
```bash
docker compose --profile ops run --rm refresh_live_prices
```

## Xử lý sự cố nhanh
### 1. `/health` trả `sqlite`
Nguyên nhân:
- app ngoài Docker đang chạy ở `8000`
- hoặc API container không dùng đúng `.env`

Cách kiểm tra:
```bash
docker compose ps
docker compose logs api
curl http://127.0.0.1:8000/health
```

Trong stack Docker chuẩn, API phải trả:
- `postgresql+psycopg`

### 2. UI lên nhưng Data Browser lỗi
Nguyên nhân thường gặp:
- `ui` chưa đọc được PostgreSQL
- `api` hoặc `postgres` chưa sẵn sàng

Cách xử lý:
```bash
docker compose logs ui
docker compose logs postgres
```

### 3. Scheduler không chạy source mới
Kiểm tra:
```bash
docker compose exec scheduler python scripts/run_scheduler.py --show-status
```

Nhìn các trường:
- `health_state`
- `failure_streak`
- `attention_sources`

### 4. Chat không dùng được OpenAI
Hành vi hiện tại:
- không crash
- fallback sang agent nội bộ

Kiểm tra:
- `CHAT_USE_OPENAI=true`
- `OPENAI_API_KEY` hợp lệ
- log của `api`

### 5. Reseed làm mất dữ liệu live cũ
Đây là hành vi hiện tại của:
```bash
docker compose --profile demo run --rm seed_demo
```

Vì `seed_demo_data.py` reset dữ liệu nghiệp vụ trước khi nạp demo lại.

## Khi cần dừng stack
### Dừng nhưng giữ volume PostgreSQL
```bash
docker compose down
```

### Dừng và xóa luôn volume PostgreSQL
```bash
docker compose down -v
```

Chỉ dùng `-v` khi chấp nhận mất toàn bộ dữ liệu DB của stack Docker này.
