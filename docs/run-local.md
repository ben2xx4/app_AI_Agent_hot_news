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

### Cách 3: Chạy full stack bằng Docker Compose
Nếu muốn dựng nhanh cả `postgres + api + ui + scheduler` bằng container:

```bash
cp .env.production.example .env
docker compose up -d postgres api ui scheduler
docker compose --profile demo run --rm seed_demo
```

Lưu ý:
- stack Docker hiện mặc định dùng PostgreSQL nội bộ, không dùng SQLite fallback trong container
- `seed_demo` là service chạy một lần để reset và nạp lại demo data
- `api` và `scheduler` tự chạy migration khi khởi động
- `api`, `scheduler`, `ui` trong Docker đã được cố định `TIMEZONE/TZ=Asia/Ho_Chi_Minh`

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

## Hành vi retention theo source
- `news`: toàn bộ source live hiện tại giữ cửa sổ ingest `30 ngày`.
- `traffic`: source live giữ cửa sổ `14 ngày`, áp cả khi ingest và khi đọc dữ liệu từ API/service.
- `policy`: không cắt ingest theo ngày; search chỉ ưu tiên văn bản recent.
- `policy`: nếu cùng query có cả source live và demo, runtime sẽ ưu tiên source live.
- `price` và `weather`: chưa áp `max_age_days` ở pha hiện tại.

Retention cleanup theo bảng được đọc từ:
```text
config/retention.yml
```

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

## Làm mới riêng giá live sau khi seed demo
Nếu vừa chạy `seed_demo_data.py --demo-only` và muốn UI/API quay lại giá live mới nhất:

```bash
.venv/bin/python scripts/refresh_live_prices.py
```

Lệnh này chỉ làm mới `price` live:
- `sjc_gold_prices_live`
- `petrolimex_fuel_prices_live`
- `sbv_fx_rates_live`
- `vietcombank_fx_rates_live`

Không reset lại các pipeline khác.

## Làm mới toàn bộ dữ liệu live sau khi seed demo
Nếu vừa chạy `seed_demo_data.py --demo-only` và muốn nạp lại đủ dữ liệu live cho `news`, `price`, `weather`, `policy`, `traffic`:

```bash
.venv/bin/python scripts/refresh_live_data.py
```

Lệnh này phù hợp khi dashboard đang hiện quá ít dữ liệu vì DB vừa bị reset về bộ demo nhỏ.

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

Tài liệu nên đọc thêm cho người dùng cuối:
- [Hướng dẫn người dùng](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/huong-dan-nguoi-dung.md)

## Cách dùng UI mới
Giao diện hiện tại được tách thành 4 workspace ở sidebar:

- `Tổng quan`
  - xem KPI nhanh của 5 pipeline
  - xem preview `Tin tức`, `Giá`, `Thời tiết`, `Chính sách`, `Giao thông`
  - dùng khối `Bắt đầu nhanh` để chuyển tiếp sang AI hoặc Explorer
- `Trợ lý AI`
  - hội thoại đầy đủ bằng tiếng Việt
  - xem lịch sử chat, câu hỏi gần đây và follow-up suggestion
  - có badge runtime cho `Chat`, `Retrieval`, `Database`
  - item chat trả về có `Thao tác ▼` để mở chi tiết nội bộ, AI hoặc link nguồn
- `Explorer`
  - tra cứu dữ liệu sâu hơn mà không cần SQL
  - tách `Dữ liệu nghiệp vụ` và `Bảng kỹ thuật`
  - hỗ trợ filter theo `pipeline`, `source`, `location`, `item_name`
  - có thể chọn một bản ghi trong preview để xem kỹ hơn và gửi sang AI
- `Hệ thống`
  - xem `runtime status`
  - xem `source health`
  - xem runbook lệnh local thường dùng

Avatar chat nổi ở góc phải vẫn được giữ cho thao tác nhanh.
Nếu muốn hội thoại rõ ràng hơn, nên dùng workspace `Trợ lý AI`.
Nếu muốn demo đủ luồng, đi theo thứ tự:
`Tổng quan` -> `Thao tác ▼` -> `Xem chi tiết` -> `Tóm tắt bằng AI` -> `Mở Explorer` -> `Mở nguồn`.

## Chạy full stack Docker
### Khởi động service dài hạn
```bash
docker compose up -d postgres api ui scheduler
```

### Nạp dữ liệu demo cho full stack
```bash
docker compose --profile demo run --rm seed_demo
```

### Làm mới lại giá live trong Docker
```bash
docker compose --profile ops run --rm refresh_live_prices
```

### Kiểm tra nhanh
```bash
docker compose ps
curl http://127.0.0.1:8000/health
```

### Xem log
```bash
docker compose logs -f api
docker compose logs -f scheduler
docker compose logs -f ui
```

### Nếu scheduler Docker không tự tăng dữ liệu
Trường hợp thường gặp là file status cũ được ghi từ runtime trước đó, làm scheduler hiểu sai `next_run_at`.

Xử lý:
```bash
rm data/processed/scheduler_status.json
docker compose restart scheduler
docker compose logs -f scheduler
```

Nếu muốn nạp dữ liệu ngay sau khi restart:
```bash
docker compose --profile ops run --rm refresh_live_data
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
.venv/bin/python scripts/run_pipeline.py --pipeline news
.venv/bin/python scripts/run_pipeline.py --pipeline price --source vietcombank_fx_rates_live
.venv/bin/python scripts/run_pipeline.py --pipeline weather --source open_meteo_weather_hanoi_live
.venv/bin/python scripts/run_pipeline.py --pipeline policy --source congbao_policy_updates_live
.venv/bin/python scripts/run_pipeline.py --pipeline traffic
.venv/bin/python scripts/run_pipeline.py --pipeline traffic --source vov_giaothong_traffic_live
```

## Chạy cleanup dữ liệu cũ
### Dry-run
```bash
.venv/bin/python scripts/run_cleanup.py
```

### Xóa thật
```bash
.venv/bin/python scripts/run_cleanup.py --apply
```

Mặc định cleanup local:
- `articles`: `30 ngày`
- `traffic_events`: `14 ngày`
- `raw_documents`: `14 ngày`
- `crawl_jobs`: `14 ngày`

Muốn đổi retention cleanup, sửa:
```text
config/retention.yml
```

Cleanup sẽ:
- dọn `document_embeddings` của `article` bị xóa
- dọn `article_clusters` mồ côi
- chỉ xóa file raw nằm trong `RAW_STORAGE_PATH`

## Chạy scheduler local
### Chạy một vòng
```bash
.venv/bin/python scripts/run_scheduler.py --demo-only --run-once
```

### Xem trạng thái scheduler
```bash
.venv/bin/python scripts/run_scheduler.py --show-status
```

Output hiện bao gồm:
- `summary`: tổng quan số job `healthy`, `due`, `pending`, `failing`
- `attention_sources`: danh sách source cần chú ý
- `health_state`, `failure_streak`, `last_duration_seconds` cho từng job

### Chạy riêng một pipeline/source
```bash
.venv/bin/python scripts/run_scheduler.py --pipeline news --source vnexpress_rss_tin_moi --run-once
```

### Gắn cleanup sau mỗi vòng
```bash
.venv/bin/python scripts/run_scheduler.py --run-once --cleanup-after-run
.venv/bin/python scripts/run_scheduler.py --run-once --cleanup-after-run --cleanup-apply
```

Lưu ý:
- `--cleanup-after-run` mặc định chỉ dry-run
- thêm `--cleanup-apply` mới xóa thật

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
- `traffic_lookup` hiện hiểu rõ hơn các nhóm câu hỏi `cấm đường`, `ùn tắc`, `tai nạn`.
- `policy_lookup` hiện ưu tiên source live hơn demo khi cùng có kết quả phù hợp.

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

### 6. API vẫn trả kết quả cũ sau khi sửa code
- Nếu vừa thay parser/service/repository mà endpoint chưa đổi kết quả, restart lại `uvicorn`.
- Ở vòng verify retention gần nhất, cần restart server để endpoint `traffic` nhận read-path mới.

### 7. Cleanup không xóa gì
- Nếu output `matched_rows = 0` thì không phải lỗi; chỉ là hiện chưa có bản ghi nào vượt retention.
- Với PostgreSQL local hiện tại, dry-run cleanup gần nhất đang trả `0` cho cả `news`, `traffic`, `raw_documents`, `crawl_jobs`.
- Nếu cần đổi số ngày cleanup, sửa `config/retention.yml` rồi chạy lại script hoặc scheduler.

## Trạng thái hiện tại
### Đã hoàn thành
- PostgreSQL hoặc SQLite fallback
- Migration local
- Seed/demo data
- API
- UI
- Ingest tay
- Scheduler local
- Retention theo source cho `news` và `traffic`
- Ranking `policy` ưu tiên recent mà không cắt văn bản cũ
- Cleanup retention theo bảng qua `config/retention.yml`

### Experimental
- Retrieval local-first cho `news` và `policy`
- Bật/tắt bằng feature flag
- Fallback sạch về flow cũ khi retrieval tắt hoặc lỗi

### TODO
- Embedding/RAG thật hoặc `pgvector`
- Đọc toàn văn PDF/OCR cho `policy`
- Scheduler production-grade
