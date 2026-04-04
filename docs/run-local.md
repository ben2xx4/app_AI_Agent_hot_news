# Hướng dẫn chạy local

## Điều kiện cần
- Python 3.12
- `venv`
- Docker Desktop nếu muốn chạy PostgreSQL bằng `docker compose`
- Kết nối mạng nếu muốn thử live source hoặc OpenAI thật

## Cài dependency và tạo `.env`
```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cp .env.example .env
```

Mặc định `.env.example` đã an toàn cho local/demo:
- Không hardcode OpenAI key mẫu
- Có thể chạy ngay với SQLite fallback
- Retrieval experimental mặc định tắt

## Cấu hình `.env`
Các biến thường dùng:
```bash
DATABASE_URL=
SQLITE_FALLBACK_URL=sqlite:///./data/app.db
CHAT_USE_OPENAI=true
EXPERIMENTAL_RETRIEVAL_ENABLED=false
```

Biến retrieval experimental:
```bash
EXPERIMENTAL_RETRIEVAL_ENABLED=false
EXPERIMENTAL_RETRIEVAL_MODEL=experimental-local-sparse-v1
EXPERIMENTAL_RETRIEVAL_MIN_SCORE=0.025
EXPERIMENTAL_RETRIEVAL_LIMIT=6
```

## Chọn database runtime
### Cách 1: Chạy nhanh bằng SQLite fallback
Không cần bật PostgreSQL. Giữ `.env` mặc định là đủ.

### Cách 2: Dùng PostgreSQL thật
Khởi động PostgreSQL:
```bash
docker compose up -d postgres
```

Cập nhật `.env`:
```bash
DATABASE_URL=postgresql+psycopg://app_user:app_password@localhost:5432/news_ai_db
```

## Hành vi SQLite/PostgreSQL
- PostgreSQL là database chính nếu `DATABASE_URL` trỏ đúng và server đang chạy.
- Nếu PostgreSQL chưa sẵn sàng, app sẽ fallback sang SQLite local.
- `alembic upgrade head` đủ ổn định cho local SQLite.
- `scripts/seed_demo_data.py` và `scripts/build_retrieval_index.py` cũng đi theo cùng runtime này.
- Có thể kiểm tra runtime thực tế bằng:
```bash
curl http://localhost:8000/health
```

`/health` sẽ cho biết đang dùng `sqlite` hay `postgresql`.

## Chạy migration
```bash
.venv/bin/alembic upgrade head
```

## Seed dữ liệu demo
Nạp dữ liệu demo cho cả 5 pipeline:
```bash
.venv/bin/python scripts/seed_demo_data.py --demo-only
```

Lưu ý:
- Dữ liệu demo hiện dùng tiếng Việt có dấu.
- Query không dấu vẫn tương thích cho nhiều case tìm kiếm.
- Ở chế độ `demo_only`, source live không có fixture sẽ được bỏ qua.
- Với code hiện tại, `news` và `policy` ingest sẽ tự ghi experimental retrieval index cho chunk mới.

## Bật Phase D experimental
Nếu muốn demo retrieval cho `topic_summary` và semantic `policy_lookup`, thêm vào `.env`:
```bash
EXPERIMENTAL_RETRIEVAL_ENABLED=true
```

Nếu database đã có dữ liệu từ trước khi pull code Phase D, build lại index:
```bash
.venv/bin/python scripts/build_retrieval_index.py --doc-type all
```

Có thể build riêng:
```bash
.venv/bin/python scripts/build_retrieval_index.py --doc-type news
.venv/bin/python scripts/build_retrieval_index.py --doc-type policy
```

## Chạy API
```bash
.venv/bin/uvicorn app.main:app --reload
```

API mặc định chạy ở:
```text
http://localhost:8000
```

## Chạy UI
Mở terminal khác và chạy:
```bash
.venv/bin/streamlit run app/ui/streamlit_app.py
```

UI mặc định chạy ở:
```text
http://localhost:8501
```

## Chạy ingest tay
### Chạy demo cho toàn bộ pipeline
```bash
.venv/bin/python scripts/run_pipeline.py --pipeline all --demo-only
```

### Chạy demo theo từng pipeline
```bash
.venv/bin/python scripts/run_pipeline.py --pipeline news --demo-only
.venv/bin/python scripts/run_pipeline.py --pipeline price --demo-only
.venv/bin/python scripts/run_pipeline.py --pipeline weather --demo-only
.venv/bin/python scripts/run_pipeline.py --pipeline policy --demo-only
.venv/bin/python scripts/run_pipeline.py --pipeline traffic --demo-only
```

### Chạy live theo từng source
```bash
.venv/bin/python scripts/run_pipeline.py --pipeline news --source tuoitre_rss_thoi_su
.venv/bin/python scripts/run_pipeline.py --pipeline price --source vietcombank_fx_rates_live
.venv/bin/python scripts/run_pipeline.py --pipeline weather --source open_meteo_weather_hanoi_live
.venv/bin/python scripts/run_pipeline.py --pipeline policy --source congbao_policy_updates_live
.venv/bin/python scripts/run_pipeline.py --pipeline traffic --source vov_giaothong_traffic_live
```

## Chạy scheduler local
### Chạy một vòng
```bash
.venv/bin/python scripts/run_scheduler.py --demo-only --run-once
```

### Xem trạng thái scheduler
```bash
.venv/bin/python scripts/run_scheduler.py --show-status
```

### Chạy riêng một pipeline/source
```bash
.venv/bin/python scripts/run_scheduler.py --pipeline news --source vnexpress_rss_tin_moi --run-once
```

Trạng thái scheduler mặc định được lưu tại:
```text
data/processed/scheduler_status.json
```

## Hành vi chat/OpenAI
- `POST /chat/query` sẽ dùng OpenAI nếu có `OPENAI_API_KEY` hợp lệ và `CHAT_USE_OPENAI=true`.
- Nếu OpenAI lỗi, bị quota limit hoặc không kết nối được, hệ thống fallback sang agent nội bộ.
- Khi `EXPERIMENTAL_RETRIEVAL_ENABLED=true`, fallback nội bộ có thể dùng retrieval cho:
  - `topic_summary`
  - `policy_lookup` ngữ nghĩa

Ví dụ kiểm tra nhanh:
```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Có những chủ đề nào về xe công cộng điện đang được nhiều báo nói tới?"}'
```

## Kiểm tra nhanh sau khi chạy
```bash
curl http://localhost:8000/health
curl "http://localhost:8000/news/hot?limit=3"
curl "http://localhost:8000/prices/latest"
curl "http://localhost:8000/weather/latest?location=Ha%20Noi"
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Tin hot hôm nay là gì?"}'
```

## Troubleshooting ngắn gọn
### 1. `connection refused` hoặc `Operation not permitted` với PostgreSQL
Nguyên nhân:
- PostgreSQL chưa chạy
- `.env` đang trỏ vào PostgreSQL nhưng local chưa bật DB

Cách xử lý:
- Bật PostgreSQL bằng `docker compose up -d postgres`
- Hoặc quay về SQLite bằng cách để `DATABASE_URL=` trong `.env`

### 2. `alembic upgrade head` vẫn chạy nhưng log báo fallback
Đây là hành vi chấp nhận được khi local đang dùng SQLite fallback.

### 3. Chat báo OpenAI `429`, `Connection error` hoặc quota
Backend sẽ fallback sang agent nội bộ. Nếu muốn dùng OpenAI thật, cần:
- Key hợp lệ
- Có quota
- `CHAT_USE_OPENAI=true`

### 4. Retrieval experimental không chạy
Kiểm tra:
- `.env` có `EXPERIMENTAL_RETRIEVAL_ENABLED=true`
- Đã reseed demo hoặc đã chạy:
```bash
.venv/bin/python scripts/build_retrieval_index.py --doc-type all
```

### 5. Live source lỗi
- Một số source live phụ thuộc website bên ngoài.
- Khi cần demo ổn định, dùng:
```bash
.venv/bin/python scripts/seed_demo_data.py --demo-only
```

## Trạng thái hiện tại
### Đã hoàn thành
- PostgreSQL hoặc SQLite fallback
- Migration local
- Seed/demo data
- API
- UI
- Ingest tay
- Scheduler local

### Experimental
- Retrieval local-first cho `news` và `policy`
- Bật/tắt bằng feature flag
- Fallback sạch về flow cũ khi retrieval tắt hoặc lỗi

### TODO
- Embedding/RAG thật hoặc `pgvector`
- Đọc toàn văn PDF/OCR cho `policy`
- Scheduler production-grade
