# Hướng dẫn chạy nhanh

File này dành cho trường hợp bạn muốn clone repo và chạy demo local nhanh nhất có thể.

## Cách 1: Chạy chuẩn với PostgreSQL
### 1. Clone repo và vào thư mục dự án
```bash
git clone https://github.com/ben2xx4/app_AI_Agent_hot_news.git
cd app_AI_Agent_hot_news
```

### 2. Tạo môi trường Python và cài dependency
```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cp .env.example .env
```

### 3. Bật PostgreSQL local bằng Docker
```bash
docker compose up -d postgres
```

### 4. Chạy migration
```bash
.venv/bin/alembic upgrade head
```

### 5. Nạp dữ liệu demo
```bash
.venv/bin/python scripts/seed_demo_data.py --demo-only
```

### 6. Chạy API
```bash
.venv/bin/uvicorn app.main:app --reload
```

### 7. Chạy UI ở terminal khác
```bash
.venv/bin/streamlit run app/ui/streamlit_app.py
```

### 8. Mở địa chỉ để kiểm tra
- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`
- UI: `http://127.0.0.1:8501`

Sau khi UI chạy, nên đọc thêm:
- `docs/huong-dan-nguoi-dung.md`

### 9. Xác nhận app đang dùng PostgreSQL
```bash
curl http://127.0.0.1:8000/health
```

Kết quả mong muốn:
```json
{"status":"ok","database_driver":"postgresql+psycopg", ...}
```

## Cách 1B: Chạy full stack Docker nhanh nhất
Nếu muốn bật luôn `postgres + api + ui + scheduler` bằng Docker:

### 1. Tạo `.env`
```bash
cp .env.production.example .env
```

### 2. Bật stack
```bash
docker compose up -d postgres api ui scheduler
```

### 3. Nạp demo data
```bash
docker compose --profile demo run --rm seed_demo
docker compose --profile ops run --rm refresh_live_data
```

### 4. Kiểm tra
```bash
docker compose ps
curl http://127.0.0.1:8000/health
```

Mở:
- API docs: `http://127.0.0.1:8000/docs`
- UI: `http://127.0.0.1:8501`

Để biết cách bấm và demo giao diện:
- `docs/huong-dan-nguoi-dung.md`

Nếu dữ liệu không tự tăng dù `scheduler` đang `Up`:
```bash
rm data/processed/scheduler_status.json
docker compose restart scheduler
docker compose logs -f scheduler
```

## Cách 2: Chạy cực nhanh bằng SQLite fallback
Nếu không muốn bật Docker/PostgreSQL, bạn vẫn có thể chạy local bằng SQLite.

### 1. Tạo môi trường và cài dependency
```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cp .env.example .env
```

### 2. Để `DATABASE_URL` rỗng trong `.env`
```bash
DATABASE_URL=
```

### 3. Chạy migration, seed và API
```bash
.venv/bin/alembic upgrade head
.venv/bin/python scripts/seed_demo_data.py --demo-only
.venv/bin/uvicorn app.main:app --reload
```

### 4. Chạy UI
```bash
.venv/bin/streamlit run app/ui/streamlit_app.py
```

Kết quả mong muốn:
```bash
curl http://127.0.0.1:8000/health
```

Trả về `database_driver=sqlite`.

## Lệnh hay dùng
### Chạy test
```bash
.venv/bin/pytest -q
```

### Chạy toàn bộ pipeline demo
```bash
.venv/bin/python scripts/run_pipeline.py --pipeline all --demo-only
```

### Chạy toàn bộ pipeline live
```bash
.venv/bin/python scripts/run_pipeline.py --pipeline all
```

### Nếu vừa seed demo và muốn cập nhật lại giá live
```bash
.venv/bin/python scripts/refresh_live_prices.py
```

### Nếu vừa seed demo và muốn nạp lại toàn bộ dữ liệu live
```bash
.venv/bin/python scripts/refresh_live_data.py
```

### Chạy scheduler local một vòng
```bash
.venv/bin/python scripts/run_scheduler.py --demo-only --run-once
```

### Xem trạng thái scheduler
```bash
.venv/bin/python scripts/run_scheduler.py --show-status
```

### Xem trạng thái scheduler trong Docker
```bash
docker compose exec scheduler python scripts/run_scheduler.py --show-status
```

### Làm mới giá live trong Docker
```bash
docker compose --profile ops run --rm refresh_live_prices
```

### Làm mới toàn bộ dữ liệu live trong Docker
```bash
docker compose --profile ops run --rm refresh_live_data
```

## Hỏi đáp AI
- Chat API: `POST /chat/query`
- UI có avatar chat tròn ở góc phải
- Nếu OpenAI không sẵn sàng hoặc hết quota, hệ thống tự fallback về agent nội bộ

Ví dụ gọi nhanh:
```bash
curl -X POST http://127.0.0.1:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Tin hot hôm nay là gì?"}'
```

## Nếu gặp lỗi
### `Address already in use`
Có process cũ đang chiếm cổng `8000` hoặc `8501`.

Kiểm tra:
```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:8501 -sTCP:LISTEN
```

### PostgreSQL không kết nối được
Kiểm tra:
```bash
docker compose ps
curl http://127.0.0.1:8000/health
```

### Chat không dùng được OpenAI
Không sao. Hệ thống vẫn trả lời bằng agent nội bộ.

## Tài liệu đầy đủ hơn
- [README.md](/Users/lamhung/Downloads/codex_news_ai_guide-2/README.md)
- [docs/run-local.md](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/run-local.md)
- [docs/testing.md](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/testing.md)
- [06_deployment/RUNBOOK.md](/Users/lamhung/Downloads/codex_news_ai_guide-2/06_deployment/RUNBOOK.md)
