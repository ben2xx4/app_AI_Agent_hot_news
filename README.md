# Nền tảng dữ liệu tin tức và thông tin hằng ngày cho Việt Nam

## Tổng quan hệ thống
Đây là hệ thống end-to-end để thu thập, chuẩn hóa, lưu trữ và phục vụ dữ liệu cho 5 nhóm thông tin hằng ngày:
- Tin tức
- Giá cả có cấu trúc
- Thời tiết
- Chính sách, văn bản
- Giao thông, sự kiện

Trên lớp dữ liệu này, repo hiện có:
- Backend FastAPI
- AI chat tiếng Việt qua `POST /chat/query`
- UI demo bằng Streamlit
- Seed/demo data để chạy local end-to-end
- Scheduler local để chạy pipeline theo lịch
- Retrieval/index experimental cho `news` và `policy`

Tài liệu liên quan:
- [Kiến trúc](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/architecture.md)
- [Pipeline](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/pipelines.md)
- [AI agent](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/ai-agent.md)
- [Cách chạy local](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/run-local.md)
- [Kiểm thử](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/testing.md)
- [Tiến độ](/Users/lamhung/Downloads/codex_news_ai_guide-2/07_tien_do_va_task/PROGRESS.md)

## Kiến trúc ngắn gọn
Nguồn dữ liệu -> Fetch/Parse -> Raw storage -> Chuẩn hóa/Dedup -> Database -> Service/API -> AI chat -> UI demo

Các khối chính:
- `app/pipelines/*`: 5 pipeline ingestion
- `app/repositories/*`: truy cập dữ liệu
- `app/services/*`: business logic, retrieval, scheduler
- `app/api/*`: FastAPI routes
- `app/agent/*`: internal agent + OpenAI tool-calling
- `app/ui/*`: Streamlit demo

## Trạng thái 5 pipeline
1. `news`
Trạng thái: hoàn thành
Nguồn:
- Demo fixture RSS
- Live: `Tuổi Trẻ RSS + HTML detail`
- Live bổ sung: `VnExpress RSS`, `Dân Trí RSS`, `Thanh Niên RSS`

2. `price`
Trạng thái: hoàn thành
Nguồn:
- Demo fixture vàng, xăng, tỷ giá
- Live: `SJC Gold Price API chính thức`
- Live: `Petrolimex CMS Price API`
- Live: `SBV tỷ giá HTML`
- Live: `Vietcombank XML`

Lưu ý:
- `sjc_gold_prices` chỉ chạy trong `--demo-only`
- khi chạy live bình thường, giá vàng sẽ ưu tiên `sjc_gold_prices_live`
- `petrolimex_fuel_prices` chỉ chạy trong `--demo-only`
- `sbv_fx_rates` chỉ chạy trong `--demo-only`
- `petrolimex_fuel_prices_live` hiện lấy `Vùng 1` làm giá hiển thị mặc định cho lookup xăng dầu
- nếu cùng một `item_name` đã có cả demo và live trong DB, API/UI sẽ ưu tiên source live; source demo chỉ dùng fallback khi chưa có live

3. `weather`
Trạng thái: hoàn thành
Nguồn:
- Demo fixture thời tiết
- Live: `Open-Meteo JSON` cho `Hà Nội`, `TP.HCM`, `Đà Nẵng`

Lưu ý:
- `nchmf_weather_daily` chỉ chạy trong `--demo-only`

4. `policy`
Trạng thái: hoàn thành
Nguồn:
- Demo fixture chính sách
- Live: `Công báo Chính phủ`, `Thủ tướng Chính phủ`, `Quốc hội` trên `congbao.chinhphu.vn`

Lưu ý:
- `chinhphu_policy_updates` chỉ chạy trong `--demo-only`

5. `traffic`
Trạng thái: hoàn thành
Nguồn:
- Demo fixture giao thông
- Live: `VOV Giao thông HTML listing + detail`
- Live bổ sung: `VnExpress Giao thông HTML listing + detail`

Lưu ý:
- `vov_traffic_updates` chỉ chạy trong `--demo-only`
- parser và API `traffic` hiện có thêm lớp lọc độ liên quan để loại các bài lệch chủ đề giao thông từ source live

## Tính năng đã hoàn thành
- 5 pipeline ingestion chạy được ở chế độ demo.
- Parser live cho cả 5 nhóm nguồn đã được thêm và có smoke test.
- `price` đã có nguồn live chính thức cho vàng, xăng dầu Petrolimex và tỷ giá NHNN.
- Raw storage, crawl job logging, timeout, retry và fallback fixture đã có.
- API FastAPI cho `news`, `prices`, `weather`, `policies`, `traffic`, `chat`.
- UI Streamlit demo hoạt động với dữ liệu tiếng Việt có dấu.
- Truy vấn không dấu vẫn dùng được cho các case phổ biến.
- Local runtime hỗ trợ PostgreSQL hoặc SQLite fallback.
- `alembic upgrade head` đủ ổn định cho local SQLite.
- `/health` trả đúng database runtime thực tế.
- `/chat/query` không còn văng `500` khi OpenAI lỗi; có fallback nội bộ.
- Scheduler local đã hoàn thành cho demo/vận hành đơn giản.
- Bộ test parser live, conversation, retrieval experimental và scheduler local đã có.

## Những gì chạy được cho local/demo
- Chạy nhanh bằng SQLite mặc định, không cần PostgreSQL.
- Seed demo data cho toàn bộ 5 pipeline bằng một lệnh.
- Chạy API và UI độc lập để demo end-to-end.
- Chạy ingest tay theo từng pipeline hoặc từng source.
- Chạy scheduler local theo vòng lặp hoặc `--run-once`.
- Nếu OpenAI không sẵn sàng hoặc bị quota limit, chat vẫn trả lời bằng agent nội bộ.
- Nếu bật retrieval experimental, có thể demo `topic_summary` và semantic `policy_lookup` ngay trên dữ liệu local.

## Tính năng experimental
- Retrieval local-first cho `news` và `policy` đã được triển khai ở mức nhỏ gọn.
- Index được lưu trong bảng `document_embeddings` bằng vector thưa local (`embedding_vector_json`), không dùng `pgvector` ở pha này.
- New ingest của `news` và `policy` tự ghi experimental index.
- Có lệnh backfill index cho dữ liệu cũ:
```bash
.venv/bin/python scripts/build_retrieval_index.py --doc-type all
```
- Retrieval hiện chỉ được nối vào:
  - `topic_summary` trong internal fallback agent
  - `policy_lookup` ngữ nghĩa khi keyword/filter yếu
- Có feature flag để bật/tắt:
```bash
EXPERIMENTAL_RETRIEVAL_ENABLED=true
```

Lưu ý:
- Đây chưa phải RAG production-ready.
- Không thay thế structured lookup hiện có.
- Nếu retrieval tắt hoặc lỗi, hệ thống fallback về flow cũ.

## Hướng dẫn chạy local từng bước
### 1. Tạo môi trường và cài dependency
```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cp .env.example .env
```

### 2. Chọn database runtime
Mặc định local/demo dùng SQLite fallback, không cần sửa `.env`.

Nếu muốn dùng PostgreSQL thật:
```bash
docker compose up -d postgres
```

Sau đó đặt trong `.env`:
```bash
DATABASE_URL=postgresql+psycopg://app_user:app_password@localhost:5432/news_ai_db
```

### 3. Chạy migration
```bash
.venv/bin/alembic upgrade head
```

### 4. Nạp dữ liệu demo
```bash
.venv/bin/python scripts/seed_demo_data.py --demo-only
```

### 5. Bật retrieval experimental nếu muốn demo Phase D
Thêm vào `.env`:
```bash
EXPERIMENTAL_RETRIEVAL_ENABLED=true
```

Nếu database đã có dữ liệu cũ từ trước khi có Phase D, build lại index:
```bash
.venv/bin/python scripts/build_retrieval_index.py --doc-type all
```

### 6. Chạy API
```bash
.venv/bin/uvicorn app.main:app --reload
```

### 7. Chạy UI
```bash
.venv/bin/streamlit run app/ui/streamlit_app.py
```

### 8. Kiểm tra nhanh
```bash
curl http://localhost:8000/health
curl "http://localhost:8000/news/hot?limit=3"
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Tin hot hôm nay là gì?"}'
```

## Các lệnh quan trọng
### Migration
```bash
.venv/bin/alembic upgrade head
```

### Seed/demo data
```bash
.venv/bin/python scripts/seed_demo_data.py --demo-only
```

### Chạy API
```bash
.venv/bin/uvicorn app.main:app --reload
```

### Chạy UI
```bash
.venv/bin/streamlit run app/ui/streamlit_app.py
```

### Chạy ingest tay
```bash
.venv/bin/python scripts/run_pipeline.py --pipeline all --demo-only
.venv/bin/python scripts/run_pipeline.py --pipeline news --source tuoitre_rss_thoi_su
.venv/bin/python scripts/run_pipeline.py --pipeline price --source petrolimex_fuel_prices_live
.venv/bin/python scripts/run_pipeline.py --pipeline price --source sbv_fx_rates_live
.venv/bin/python scripts/run_pipeline.py --pipeline price --source vietcombank_fx_rates_live
.venv/bin/python scripts/run_pipeline.py --pipeline weather --source open_meteo_weather_hanoi_live
.venv/bin/python scripts/run_pipeline.py --pipeline policy --source congbao_policy_updates_live
.venv/bin/python scripts/run_pipeline.py --pipeline traffic --source vov_giaothong_traffic_live
.venv/bin/python scripts/run_pipeline.py --pipeline traffic --source vnexpress_traffic_live
```

### Build experimental retrieval index
```bash
.venv/bin/python scripts/build_retrieval_index.py --doc-type all
.venv/bin/python scripts/build_retrieval_index.py --doc-type news
.venv/bin/python scripts/build_retrieval_index.py --doc-type policy
```

### Chạy scheduler local
```bash
.venv/bin/python scripts/run_scheduler.py --demo-only --run-once
.venv/bin/python scripts/run_scheduler.py --show-status
.venv/bin/python scripts/run_scheduler.py --pipeline news --source vnexpress_rss_tin_moi --run-once
```

### Chạy test
```bash
.venv/bin/pytest -q
```

## Hành vi SQLite/PostgreSQL
- PostgreSQL là database chính cho local/dev/prod.
- Nếu `DATABASE_URL` trỏ vào PostgreSQL nhưng PostgreSQL local chưa chạy, app sẽ fallback sang SQLite theo `SQLITE_FALLBACK_URL`.
- Hành vi fallback này áp dụng cho API runtime, migration local, seed/demo flow và build retrieval index.
- Có thể kiểm tra database runtime thật qua:
```bash
curl http://localhost:8000/health
```

## Hành vi seed/demo data
- `scripts/seed_demo_data.py --demo-only` nạp dữ liệu demo cho cả 5 pipeline.
- Ở chế độ `demo_only`, source live không có fixture sẽ được bỏ qua thay vì cố gọi mạng.
- Dữ liệu demo hiện đã dùng tiếng Việt có dấu.
- Tìm kiếm không dấu vẫn hoạt động cho các case phổ biến như `giao duc`, `Ha Noi`, `gia vang`.
- Với code hiện tại, `news` và `policy` demo ingest sẽ tự ghi experimental retrieval index cho chunk mới.
- Với `price`, các source demo `sjc_gold_prices`, `petrolimex_fuel_prices`, `sbv_fx_rates` chỉ dùng trong `--demo-only`.

## AI chat và fallback OpenAI
- `POST /chat/query` ưu tiên dùng OpenAI khi có `OPENAI_API_KEY` và `CHAT_USE_OPENAI=true`.
- Nếu OpenAI không khả dụng, lỗi request, hoặc quota bị giới hạn, hệ thống tự fallback sang agent nội bộ.
- Fallback nội bộ đang hỗ trợ các intent:
  - `hot_news`
  - `price_lookup`
  - `price_compare`
  - `weather_lookup`
  - `policy_lookup`
  - `traffic_lookup`
  - `topic_summary`
  - `source_compare`
- Khi `EXPERIMENTAL_RETRIEVAL_ENABLED=true`, fallback agent có thể dùng retrieval cho:
  - `topic_summary`
  - `policy_lookup` ngữ nghĩa

Ví dụ demo retrieval:
```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Có những chủ đề nào về xe công cộng điện đang được nhiều báo nói tới?"}'
```

## Scheduler local
- Scheduler local đã hoàn thành cho mục đích demo/vận hành đơn giản.
- Scheduler đọc `fetch_interval_minutes` từ `config/sources.yml`.
- Có thể lọc theo `--pipeline` và `--source`.
- Có `--run-once` để chạy kiểu cron-friendly.
- Có `--show-status` để xem trạng thái mà không chạy job.
- Trạng thái mặc định được lưu ở:
```text
data/processed/scheduler_status.json
```

## Kiểm thử và trạng thái hiện tại
Kết quả xác minh gần nhất:
- `.venv/bin/ruff check app scripts tests`
- `.venv/bin/pytest -q`
- `.venv/bin/python scripts/seed_demo_data.py --demo-only`
- `.venv/bin/python scripts/build_retrieval_index.py --doc-type all`
- `.venv/bin/python scripts/run_pipeline.py --pipeline price`

Kết quả:
- `ruff`: pass
- `pytest`: `48 passed`
- Build experimental index: `article=6`, `policy=2`
- `price`: `sjc_gold_prices`, `petrolimex_fuel_prices`, `sbv_fx_rates` bị `skipped` ngoài `--demo-only`; các source live mới ingest thành công

## Giới hạn hiện tại
- Experimental retrieval hiện là sparse local index, chưa phải embedding vector thật.
- Chưa có `pgvector`, ANN search hoặc semantic ranking production-grade.
- OpenAI tool path hiện không thay structured lookup; retrieval chủ yếu phát huy trong internal fallback agent và `PolicyService`.
- Policy hiện ưu tiên metadata và trích yếu; chưa có luồng đọc toàn văn PDF/OCR.
- Scheduler hiện phù hợp local/demo, chưa phải bộ điều phối production-grade.
- Chưa có geocoding giao thông hoặc chuẩn hóa sâu theo tọa độ.
- Một số source live vẫn phụ thuộc cấu trúc HTML hiện tại của website nguồn.
- `petrolimex_fuel_prices_live` hiện mới surfacing giá `Vùng 1`; `Vùng 2` chưa có contract riêng ở API/UI.

## Hướng phát triển tiếp theo
- Nâng Phase D từ sparse local retrieval lên embedding/RAG thật.
- Bổ sung trích xuất toàn văn PDF cho `policy`.
- Mở rộng retrieval sang nhiều intent hơn sau khi đủ ổn định.
- Nâng scheduler từ local/demo lên hướng production nếu cần.
- Mở rộng chuẩn hóa và geocoding cho `traffic`.
