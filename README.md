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
- [Hướng dẫn chạy nhanh](/Users/lamhung/Downloads/codex_news_ai_guide-2/HUONG_DAN_CHAY_NHANH.md)
- [Kiến trúc](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/architecture.md)
- [Pipeline](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/pipelines.md)
- [AI agent](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/ai-agent.md)
- [UI/UX hiện tại](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/ui.md)
- [Hướng dẫn người dùng](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/huong-dan-nguoi-dung.md)
- [Bản đồ chức năng giao diện](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/ui-functional-map.md)
- [Cách chạy local](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/run-local.md)
- [Kiểm thử](/Users/lamhung/Downloads/codex_news_ai_guide-2/docs/testing.md)
- [Runbook Docker/full stack](/Users/lamhung/Downloads/codex_news_ai_guide-2/06_deployment/RUNBOOK.md)
- [Demo script](/Users/lamhung/Downloads/codex_news_ai_guide-2/06_deployment/DEMO_SCRIPT.md)
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
- Live bổ sung: `VnExpress RSS` (`tin mới`, `thời sự`, `kinh doanh`, `thế giới`, `giáo dục`)
- Live bổ sung: `Dân Trí RSS` (`trang chủ`, `thế giới`, `kinh doanh`, `giáo dục`, `thể thao`)
- Live bổ sung: `Thanh Niên RSS` (`trang chủ`, `thời sự`, `kinh tế`, `thế giới`, `giáo dục`)

Lưu ý:
- Toàn bộ nguồn `news` hiện có `max_age_days=30`, chỉ ingest bài nằm trong cửa sổ 30 ngày gần nhất nếu feed còn cung cấp.
- Logic retention của `news` hiện đi qua helper dùng lại được, không còn hardcode riêng trong parser.
- `Tuổi Trẻ` vẫn là nguồn duy nhất đang enrich detail HTML; các RSS section feed còn lại đi theo parser `rss_basic`.
- Một số RSS section có thể stale theo từng thời điểm; repo hiện đã loại feed `Dân Trí Xã hội` vì không còn cập nhật trong cửa sổ 30 ngày.

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
- Live: `Open-Meteo JSON` cho `Hà Nội`, `TP.HCM`, `Đà Nẵng`, `Hải Phòng`, `Cần Thơ`, `Nha Trang`

Lưu ý:
- `nchmf_weather_daily` chỉ chạy trong `--demo-only`
- Demo fixture hiện cũng đã có `Hải Phòng`, `Cần Thơ`, `Nha Trang` để test/chat local không phụ thuộc hoàn toàn vào live ingest

4. `policy`
Trạng thái: hoàn thành
Nguồn:
- Demo fixture chính sách
- Live: `Công báo Chính phủ`, `Thủ tướng Chính phủ`, `Quốc hội` trên `congbao.chinhphu.vn`

Lưu ý:
- `chinhphu_policy_updates` chỉ chạy trong `--demo-only`
- `policy` không cắt ingest theo `max_age_days`; search sẽ ưu tiên văn bản mới hơn nhưng vẫn giữ khả năng trả văn bản cũ còn liên quan.
- Nếu cùng một truy vấn có cả source live và demo, runtime `policy` sẽ ưu tiên kết quả từ source live.

5. `traffic`
Trạng thái: hoàn thành
Nguồn:
- Demo fixture giao thông
- Live: `VOV Giao thông HTML listing + detail`
- Live bổ sung: `VnExpress Giao thông HTML listing + detail`

Lưu ý:
- `vov_traffic_updates` chỉ chạy trong `--demo-only`
- parser và API `traffic` hiện có thêm lớp lọc độ liên quan để loại các bài lệch chủ đề giao thông từ source live
- Hai source live `traffic` hiện dùng `max_age_days=14`
- Read-path `traffic` cũng áp cửa sổ 14 ngày theo metadata source và ưu tiên bản ghi live trước bản ghi demo nếu cùng tồn tại trong DB
- Chat và service `traffic` hiện đã hiểu rõ hơn các focus `cấm đường`, `ùn tắc`, `tai nạn`

## Tính năng đã hoàn thành
- 5 pipeline ingestion chạy được ở chế độ demo.
- Parser live cho cả 5 nhóm nguồn đã được thêm và có smoke test.
- `price` đã có nguồn live chính thức cho vàng, xăng dầu Petrolimex và tỷ giá NHNN.
- Raw storage, crawl job logging, timeout, retry và fallback fixture đã có.
- API FastAPI cho `news`, `prices`, `weather`, `policies`, `traffic`, `chat`.
- UI Streamlit demo hoạt động với dữ liệu tiếng Việt có dấu.
- UI đã được tổ chức lại thành 4 workspace rõ ràng trong sidebar:
  - `Tổng quan`
  - `Trợ lý AI`
  - `Explorer`
  - `Hệ thống`
- Dashboard `Tổng quan` hiện đã dùng nhãn nguồn dễ đọc hơn thay cho source id thô như `thanhnien_rss_thoi_su` hoặc `open_meteo_weather_hanoi_live`.
- CTA chính hiện đã đi theo luồng thật:
  - preview -> `Xem chi tiết`
  - `Tóm tắt bằng AI` hoặc `Hỏi AI về mục này`
  - `Mở Explorer`
  - `Mở nguồn`
- Truy vấn không dấu vẫn dùng được cho các case phổ biến.
- Local runtime hỗ trợ PostgreSQL hoặc SQLite fallback.
- `alembic upgrade head` đủ ổn định cho local SQLite.
- `/health` trả đúng database runtime thực tế.
- `/chat/query` không còn văng `500` khi OpenAI lỗi; có fallback nội bộ.
- Chat đã hiểu thêm nhiều biến thể câu hỏi `tin hot`:
  - `Tin hot hôm nay là gì?`
  - `Top 5 tin hot`
  - `Top 10 tin hot`
  - `Ở TP.HCM có tin hot gì?`
  - `Top 5 tin hot về giáo dục`
- Scheduler local đã hoàn thành cho demo/vận hành đơn giản.
- Bộ test parser live, conversation, retrieval experimental và scheduler local đã có.
- Bộ test hiện cũng đã bao phủ retention theo source cho `news`, `traffic` và xếp hạng recent cho `policy`.
- Cleanup local đã đọc retention từ `config/retention.yml` thay vì giữ mặc định cố định trong script.
- `policy` search đã ưu tiên source live hơn demo.
- `traffic` đã có focus filter cho `cấm đường`, `ùn tắc`, `tai nạn`.
- `/chat/query` hiện hỗ trợ backward-compatible:
  - `mode`
  - `context_item`
  - `items[]` click được trong response

## Những gì chạy được cho local/demo
- Chạy nhanh bằng SQLite mặc định, không cần PostgreSQL.
- Seed demo data cho toàn bộ 5 pipeline bằng một lệnh.
- Chạy API và UI độc lập để demo end-to-end.
- UI mới có điều hướng rõ bằng sidebar:
  - `Tổng quan` để xem tín hiệu nổi bật
  - `Trợ lý AI` để hội thoại đầy đủ
  - `Explorer` để tra cứu sâu
  - `Hệ thống` để xem runtime và source health
- Dashboard có khối `Bắt đầu nhanh`, CTA theo tác vụ, preview `policy`/`traffic` và chỉ báo quy mô dữ liệu thực.
- Dashboard hiện có thêm khối `Biểu đồ nhanh` để nhìn nhanh quy mô dữ liệu, nguồn trong cụm tin hot và biên độ nhiệt độ theo từng điểm.
- `Bản tin biên tập` đã được dàn lại theo kiểu editorial: `1` tin dẫn lớn và cụm tin bổ trợ dạng grid để dễ scan hơn khi demo trên màn hình lớn.
- Từ preview card `Tin tức`, `Giá`, `Thời tiết`, `Chính sách`, `Giao thông`, người dùng hiện có thể mở chi tiết nội bộ thay vì chỉ xem tĩnh.
- Chat có workspace riêng, gợi ý câu hỏi theo nhóm, câu hỏi gần đây, follow-up suggestion và vẫn có avatar nổi để thao tác nhanh.
- Câu trả lời chat hiện render được `items[]` click được:
  - mở chi tiết nội bộ
  - tóm tắt lại bằng AI
  - mở Explorer
  - mở link nguồn nếu item có URL
- Card `Giá` và `Thời tiết` đã chặn overflow của tiêu đề nguồn, dùng provider label ngắn gọn hơn như `Vietcombank`, `Open-Meteo`, `SJC`.
- UI hiện chỉ fetch dữ liệu preview của `Dashboard` khi workspace `Tổng quan` đang mở; các workspace khác không còn bắn cả cụm `/news`, `/prices`, `/weather`, `/policies`, `/traffic` mỗi lần rerun.
- Các `GET` từ UI sang API hiện có cache ngắn hạn để giảm burst request khi Streamlit rerender trong Docker/local.
- Chat hiện hỗ trợ rõ hơn các cách hỏi tự nhiên theo:
  - số lượng `top N`
  - địa điểm `ở TP.HCM`, `ở Hà Nội`
- chủ đề `về giáo dục`, `về tài chính`
- Chat cũng đã hiểu tốt hơn các câu hỏi kiểu tiêu đề bài báo hoặc câu hỏi tự nhiên dài, ví dụ `Hôm nay 5.4 là Tết Thanh minh 2026, người Việt cần lưu ý gì?`
- Explorer đã thay cho Data Browser kiểu cũ, có thêm filter theo `pipeline`, `source`, `location`, `item_name`, sort `mới nhất/cũ nhất` và tách `dữ liệu nghiệp vụ` với `bảng kỹ thuật`.
- Explorer hiện cho phép chọn ngay một bản ghi trong preview để xem kỹ hơn và gửi bản ghi đó sang AI.
- Chạy ingest tay theo từng pipeline hoặc từng source.
- Chạy scheduler local theo vòng lặp hoặc `--run-once`.
- Chạy cleanup dry-run hoặc apply theo retention config trung tâm.
- Nếu OpenAI không sẵn sàng hoặc bị quota limit, chat vẫn trả lời bằng agent nội bộ.
- Nếu bật retrieval experimental, có thể demo `topic_summary` và semantic `policy_lookup` ngay trên dữ liệu local.
- Có thể thay retention theo source trong `config/sources.yml` mà không cần sửa parser business logic.

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

## Chạy full stack bằng Docker Compose
Đây là cách phù hợp khi cần demo hoặc bàn giao nhanh mà không muốn chạy nhiều terminal local.

### 1. Tạo `.env` cho stack Docker
```bash
cp .env.production.example .env
```

### 2. Bật PostgreSQL, API, UI, scheduler
```bash
docker compose up -d postgres api ui scheduler
```

### 3. Nạp dữ liệu demo một lần
```bash
docker compose --profile demo run --rm seed_demo
```

### 4. Kiểm tra stack
```bash
docker compose ps
curl http://127.0.0.1:8000/health
```

### 5. Mở giao diện
- API docs: `http://127.0.0.1:8000/docs`
- UI: `http://127.0.0.1:8501`

Lưu ý:
- stack Docker chuẩn hiện dùng PostgreSQL nội bộ, không đi theo SQLite fallback
- `api` và `scheduler` tự chạy `alembic upgrade head` khi khởi động
- stack Docker hiện đã cố định `TIMEZONE/TZ=Asia/Ho_Chi_Minh` cho `api`, `scheduler`, `ui`
- `seed_demo` là service chạy một lần, không nên để chạy lặp sau mỗi restart

Nếu scheduler trong Docker từng bị đứng ở trạng thái `runs: []` do file status cũ:
```bash
rm data/processed/scheduler_status.json
docker compose restart scheduler
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

### Làm mới giá live sau khi đã seed demo
```bash
.venv/bin/python scripts/refresh_live_prices.py
```

### Làm mới toàn bộ dữ liệu live sau khi đã seed demo
```bash
.venv/bin/python scripts/refresh_live_data.py
```

### Chạy API
```bash
.venv/bin/uvicorn app.main:app --reload
```

### Chạy UI
```bash
.venv/bin/streamlit run app/ui/streamlit_app.py
```

### Chạy full stack Docker
```bash
cp .env.production.example .env
docker compose up -d postgres api ui scheduler
docker compose --profile demo run --rm seed_demo
```

### Làm mới giá live trong Docker
```bash
docker compose --profile ops run --rm refresh_live_prices
```

### Làm mới toàn bộ dữ liệu live trong Docker
```bash
docker compose --profile ops run --rm refresh_live_data
```

### Chạy ingest tay
```bash
.venv/bin/python scripts/run_pipeline.py --pipeline all --demo-only
.venv/bin/python scripts/run_pipeline.py --pipeline news
.venv/bin/python scripts/run_pipeline.py --pipeline news --source tuoitre_rss_thoi_su
.venv/bin/python scripts/run_pipeline.py --pipeline price --source petrolimex_fuel_prices_live
.venv/bin/python scripts/run_pipeline.py --pipeline price --source sbv_fx_rates_live
.venv/bin/python scripts/run_pipeline.py --pipeline price --source vietcombank_fx_rates_live
.venv/bin/python scripts/run_pipeline.py --pipeline weather --source open_meteo_weather_hanoi_live
.venv/bin/python scripts/run_pipeline.py --pipeline policy --source congbao_policy_updates_live
.venv/bin/python scripts/run_pipeline.py --pipeline traffic
.venv/bin/python scripts/run_pipeline.py --pipeline traffic --source vov_giaothong_traffic_live
.venv/bin/python scripts/run_pipeline.py --pipeline traffic --source vnexpress_traffic_live
```

### Chạy cleanup dữ liệu cũ
```bash
.venv/bin/python scripts/run_cleanup.py
.venv/bin/python scripts/run_cleanup.py --apply
```

Mặc định cleanup sẽ:
- xóa `articles` cũ hơn `30 ngày`
- xóa `traffic_events` cũ hơn `14 ngày`
- xóa `raw_documents` cũ hơn `14 ngày`
- xóa `crawl_jobs` cũ hơn `14 ngày`

Retention cleanup hiện được đọc từ:
```text
config/retention.yml
```

Lưu ý:
- Mặc định script chạy ở `dry-run`
- Chỉ khi có `--apply` mới xóa thật
- Cleanup `articles` sẽ dọn kèm `document_embeddings` liên quan và `article_clusters` mồ côi

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
.venv/bin/python scripts/run_scheduler.py --run-once --cleanup-after-run
.venv/bin/python scripts/run_scheduler.py --run-once --cleanup-after-run --cleanup-apply
```

Output scheduler hiện có thêm:
- `summary`
- `health_state`
- `failure_streak`
- `attention_sources`

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

## Retention theo source
- `news`: mặc định `30 ngày` cho toàn bộ source RSS live hiện tại.
- `traffic`: mặc định `14 ngày` cho source live, áp cả lúc ingest và lúc đọc dữ liệu.
- `policy`: không cắt ingest theo ngày; search chỉ ưu tiên recent.
- `price` và `weather`: chưa dùng `max_age_days` ở pha hiện tại.

Retention cleanup theo bảng hiện đặt tại:
```text
config/retention.yml
```

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
- `traffic_lookup` hiện có thêm focus filter cho các câu như:
  - `Có tuyến đường nào đang bị cấm không?`
  - `Có ùn tắc nào đáng chú ý không?`
  - `Có tai nạn giao thông nào đáng chú ý không?`
- `policy_lookup` hiện ưu tiên source live hơn demo khi cùng có kết quả phù hợp.

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
- Có thể gắn cleanup dữ liệu cũ sau mỗi vòng bằng `--cleanup-after-run`.
- Cleanup qua scheduler mặc định cũng là `dry-run`; chỉ xóa thật khi thêm `--cleanup-apply`.
- Có `source health summary` để nhìn nhanh source nào đang `healthy`, `due`, `pending` hoặc `failing`.
- Có `failure_streak` và `last_duration_seconds` cho từng source trong file trạng thái.
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
- `.venv/bin/python scripts/run_pipeline.py --pipeline news`
- `.venv/bin/python scripts/run_pipeline.py --pipeline traffic`
- `.venv/bin/python scripts/run_cleanup.py`

Kết quả:
- `ruff`: pass
- `pytest`: `332 passed`
- Build experimental index: `article=6`, `policy=2`
- `news`: toàn bộ source live vẫn ingest ổn với cửa sổ `30 ngày`
- `traffic`: source live ingest ổn với cửa sổ `14 ngày`; endpoint runtime đã bỏ source demo khỏi top kết quả mới nhất sau khi reload server
- `cleanup`: dry-run trên PostgreSQL local chạy thành công, hiện chưa có bản ghi nào vượt retention nên `matched_rows=0` cho cả 4 nhóm
- `policy`: runtime search đã ưu tiên source live hơn demo khi cùng có kết quả phù hợp
- `traffic`: runtime chat/API đã có focus filter cho `cấm đường`, `ùn tắc`, `tai nạn`
- `chat`: đã có ma trận kiểm thử lớn cho biến thể câu hỏi `tin hot`, `top N`, `địa điểm`, `giá`, `thời tiết`, `policy`, `traffic`
- `chat`: đã hiểu tốt hơn các câu hỏi kiểu tiêu đề bài báo và câu tự nhiên dài; dashboard cũng có thêm `Biểu đồ nhanh` cho demo

## Giới hạn hiện tại
- Experimental retrieval hiện là sparse local index, chưa phải embedding vector thật.
- Chưa có `pgvector`, ANN search hoặc semantic ranking production-grade.
- OpenAI tool path hiện không thay structured lookup; retrieval chủ yếu phát huy trong internal fallback agent và `PolicyService`.
- Policy hiện ưu tiên metadata và trích yếu; chưa có luồng đọc toàn văn PDF/OCR.
- Scheduler hiện phù hợp local/demo, chưa phải bộ điều phối production-grade.
- Chưa có geocoding giao thông hoặc chuẩn hóa sâu theo tọa độ.
- Một số source live vẫn phụ thuộc cấu trúc HTML hiện tại của website nguồn.
- `petrolimex_fuel_prices_live` hiện mới surfacing giá `Vùng 1`; `Vùng 2` chưa có contract riêng ở API/UI.
- `traffic` vẫn dùng heuristic relevance; độ chính xác đã tốt hơn nhưng chưa phải phân loại ngữ nghĩa hoàn chỉnh.

## Hướng phát triển tiếp theo
- Nâng Phase D từ sparse local retrieval lên embedding/RAG thật.
- Bổ sung trích xuất toàn văn PDF cho `policy`.
- Mở rộng retrieval sang nhiều intent hơn sau khi đủ ổn định.
- Nâng scheduler từ local/demo lên hướng production nếu cần.
- Mở rộng chuẩn hóa và geocoding cho `traffic`.
- Nếu muốn cleanup lâu dài hơn, mở rộng `config/retention.yml` theo từng pipeline hoặc từng source thay vì mới dừng ở mức bảng chính.
