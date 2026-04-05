# Tiến độ triển khai

## Trạng thái tổng quan
- MVP nền tảng đã hoàn thành.
- Phase A đã hoàn thành: parser live cho 5 nhóm nguồn.
- Phase B đã hoàn thành: bộ test conversation mẫu và test fallback chat.
- Phase C đã hoàn thành: scheduler local.
- Phase D đã được triển khai ở mức experimental, local-first và có thể demo.
- Phase E đã hoàn thành: retention theo source và recent ranking cho read-path.
- Phase F đã hoàn thành: cleanup dữ liệu cũ theo retention local.
- Phase G đã hoàn thành: hardening `policy` và `traffic` cho runtime chat/API.
- Phase H đã hoàn thành: chốt stack Docker full gồm `postgres`, `api`, `ui`, `scheduler`, `seed_demo`, kèm runbook và demo script.
- Phase I đã hoàn thành: tách `refresh_live_data`, mở rộng dashboard để hiển thị quy mô dữ liệu thực và preview thêm `policy`/`traffic`.
- Phase J đã hoàn thành: tổ chức lại UX cho người dùng thao tác với CTA bắt đầu nhanh, chat gợi ý theo nhóm và Data Browser có filter/sort.
- Phase K đã hoàn thành: làm mới giao diện dashboard theo hướng editorial hơn, dùng số liệu thật trong hero và gom mọi thao tác vào một trang chính duy nhất.
- Phase L đã hoàn thành: cải thiện trải nghiệm hội thoại trong chat nổi với gợi ý theo tab, câu hỏi gần đây và metadata rõ hơn.
- Phase M đã hoàn thành: làm chat dễ đọc hơn bằng bubble phân vai rõ hơn và follow-up suggestion theo intent.
- Phase N đã hoàn thành: redesign toàn bộ UI/UX thành 4 workspace `Tổng quan`, `Trợ lý AI`, `Explorer`, `Hệ thống` với sidebar navigation, quick actions và Explorer rõ ràng hơn.
- Phase O đã hoàn thành: sửa scheduler Docker để tránh lệch giờ giữa host/container bằng timezone-aware status và `TZ=Asia/Ho_Chi_Minh`.
- Phase P đã hoàn thành: chốt UI demo cuối với detail panel, CTA thật và chat `items[]` click được.

## Mốc hoàn thành theo phase
### Phase 0 đến Phase 9
Trạng thái: hoàn thành

Đã có:
- Skeleton dự án, cấu hình môi trường, migration, schema ORM
- 5 pipeline ingestion ở chế độ demo
- Raw storage, repository, service layer
- API FastAPI
- AI chat tiếng Việt
- UI Streamlit
- Seed/demo data
- Docker Compose, tài liệu local và handoff

### Phase A: Parser live cho nguồn thật
Trạng thái: hoàn thành

Đã có:
- `news`: `Tuổi Trẻ RSS + HTML detail`
- `price`: `SJC Gold API`, `Petrolimex CMS Price API`, `SBV tỷ giá HTML`, `Vietcombank XML`
- `weather`: `Open-Meteo JSON`
- `policy`: `Công báo Chính phủ HTML listing + detail`
- `traffic`: `VOV Giao thông HTML listing + detail`

Đi kèm:
- Timeout, retry, logging
- Fallback fixture khi phù hợp
- Lệnh ingest riêng theo `--pipeline` và `--source`
- Smoke test parser live

### Phase B: Bộ test conversation mẫu
Trạng thái: hoàn thành

Đã có test cho:
- `hot_news`
- `price_lookup`
- `price_compare`
- `weather_lookup`
- `policy_lookup`
- `traffic_lookup`
- `topic_summary`
- `source_compare`

Đi kèm:
- Test fallback khi OpenAI unavailable
- Điều chỉnh `demo_only` để không cố gọi mạng ngoài với fixture demo

### Phase C: Scheduler local
Trạng thái: hoàn thành

Đã có:
- `app/services/scheduler_service.py`
- `scripts/run_scheduler.py`
- Lọc theo `pipeline` và `source`
- `--run-once`
- `--show-status`
- File trạng thái local
- Unit test scheduler

### Phase D: Retrieval/index cơ bản cho `news` và `policy`
Trạng thái: hoàn thành ở mức experimental

Đã có:
- Vector thưa local-first lưu trong `document_embeddings.embedding_vector_json`
- `scripts/build_retrieval_index.py` để backfill index
- New ingest của `news` và `policy` tự ghi index experimental
- Retrieval cho `topic_summary`
- Semantic fallback cho `policy_lookup`
- Feature flag `EXPERIMENTAL_RETRIEVAL_ENABLED`
- Logging và fallback sạch về flow cũ

Chưa có:
- Embedding vector thật
- `pgvector`
- RAG production-ready
- Reranker

### Phase E: Retention theo source và recent ranking
Trạng thái: hoàn thành

Đã có:
- Helper retention dùng lại được ở `app/pipelines/common/processing.py`
- `news` giữ `max_age_days=30` theo source thay vì hardcode riêng trong parser
- `traffic` live dùng `max_age_days=14`, áp cả lúc ingest và lúc đọc dữ liệu
- `policy` không cắt ingest theo ngày; search ưu tiên recent nhưng vẫn giữ khả năng trả văn bản cũ còn liên quan
- `traffic` read-path ưu tiên source live trước demo khi cùng tồn tại trong DB
- `traffic` read-path đã bỏ phụ thuộc vào metadata source cũ trong DB bằng cách overlay config hiện tại từ `config/sources.yml`

Đi kèm:
- Test helper retention
- Test source config
- Test `policy` recent ranking
- Test `traffic` age window + live/demo filtering

### Phase F: Cleanup dữ liệu cũ theo retention local
Trạng thái: hoàn thành

Đã có:
- `CleanupService` riêng cho local ở `app/services/cleanup_service.py`
- `RetentionConfig` ở `app/services/retention_config.py`
- `config/retention.yml` làm nguồn cấu hình retention cleanup trung tâm
- Script `scripts/run_cleanup.py`
- Chế độ mặc định `dry-run`, chỉ xóa thật khi có `--apply`
- Cleanup cho:
  - `articles` cũ hơn `30 ngày`
  - `traffic_events` cũ hơn `14 ngày`
  - `raw_documents` cũ hơn `14 ngày`
  - `crawl_jobs` cũ hơn `14 ngày`
- Dọn kèm:
  - `document_embeddings` của article bị xóa
  - `article_clusters` mồ côi
  - file raw nằm trong `RAW_STORAGE_PATH`
- Có thể nối cleanup vào scheduler bằng `--cleanup-after-run`

Đi kèm:
- Test dry-run/apply cho DB row và file raw
- Test đọc retention cleanup từ config trung tâm
- Verify script cleanup trên PostgreSQL local ở chế độ dry-run

### Phase G: Hardening `policy` và `traffic`
Trạng thái: hoàn thành

Đã có:
- `policy` runtime ưu tiên source live hơn demo khi cùng có kết quả phù hợp
- `traffic_lookup` có thêm focus filter cho:
  - `cấm đường`
  - `ùn tắc`
  - `tai nạn`
- `traffic` focus hiện ưu tiên precision ở tiêu đề, tránh kéo các bài hạ tầng hoặc cảnh báo an toàn quá rộng
- Câu `Có tuyến đường nào đang bị cấm không?` và `Có tai nạn giao thông nào đáng chú ý không?` giờ trả `không có cập nhật` thay vì cố lôi bài lệch chủ đề

Đi kèm:
- Regression test cho `policy` live-preference
- Regression test cho `traffic` focus filtering ở service và chat

## Kết quả xác minh gần nhất
Thời điểm cập nhật: `2026-04-05`

### Kiểm thử
Đã chạy:
- `.venv/bin/ruff check app scripts tests`
- `.venv/bin/pytest -q`

Kết quả:
- `ruff`: pass
- `pytest`: `332 passed`

### Cập nhật UI gần nhất
Đã có:
- Hero dùng số lượng bản ghi thật từ database thay vì số liệu tĩnh
- Sidebar navigation cho 4 workspace:
  - `Tổng quan`
  - `Trợ lý AI`
  - `Explorer`
  - `Hệ thống`
- Khối `Bắt đầu nhanh` giờ điều hướng rõ sang AI hoặc Explorer thay vì nhồi thêm block trong một trang dài
- `Explorer` thay cho `Data Browser` kiểu cũ, tách:
  - `Dữ liệu nghiệp vụ`
  - `Bảng kỹ thuật`
- Sidebar đã có `Quick actions` để tìm nhanh trong Explorer hoặc đẩy thẳng câu hỏi sang AI
- Khu `Trợ lý AI` có workspace riêng, badge trạng thái runtime và dùng chung lịch sử với avatar chat nổi
- Khu `Hệ thống` tách riêng runtime status, source health và runbook local khỏi dashboard chính
- Chat nổi vẫn được giữ để thao tác nhanh, nhưng không còn là điểm vào duy nhất của AI
- Giao diện tổng thể được chỉnh lại palette, khoảng thở và nhịp hiển thị để bớt cảm giác dashboard thô
- Tin nhắn chat hiện có timestamp, meta và follow-up suggestion theo intent
- `Bản tin biên tập` đã được dàn lại thành cụm editorial rõ hơn với `1` tin dẫn lớn và cụm tin bổ trợ dạng grid
- Dashboard dùng nhãn nguồn dễ đọc hơn như `Thanh Niên · Thời sự`, `Vietcombank`, `Open-Meteo`
- Card `Giá` và `Thời tiết` đã chặn overflow của source title để không tràn ra ngoài ở màn hình desktop hẹp
- Loader UI hiện đã chuyển sang fetch theo workspace: chỉ `Tổng quan` mới gọi cụm preview `/news`, `/prices`, `/weather`, `/policies`, `/traffic`
- `GET` từ Streamlit sang API có cache ngắn hạn để giảm burst call trong Docker/local khi UI rerender
- Đã bổ sung file tài liệu tổng hợp `TOAN_BO_NOI_DUNG_GIAO_DIEN_HIEN_TAI.txt` để mô tả đầy đủ giao diện hiện tại phục vụ demo và bàn giao
- Detail panel nội bộ đã được nối vào `Tổng quan`, `Trợ lý AI`, `Explorer`
- CTA preview giờ đi đúng luồng:
  - `Xem chi tiết`
  - `Tóm tắt bằng AI`
  - `Hỏi AI về mục này`
  - `Mở Explorer`
  - `Mở nguồn`
- `POST /chat/query` đã có `items[]` click được và hỗ trợ `mode/context_item` theo cách backward-compatible
- Explorer đã cho phép chọn bản ghi trong preview để xem kỹ hơn và gửi sang AI

Đi kèm:
- `ruff check app/ui/streamlit_app.py`
- test UI nhắm đích:
  - `tests/unit/test_content_items.py`
  - `tests/unit/test_chat_clickable_items.py`
  - `tests/unit/test_ui_flow.py`
  - `tests/unit/test_data_browser.py`
  - `tests/unit/test_chat_ui_state.py`
  - `tests/unit/test_ui_experience.py`
  - `tests/unit/test_ui_navigation.py`
  - `tests/unit/test_ui_presentation.py`
  - `tests/unit/test_ui_runtime.py`
- `python -m compileall app`
- boot `streamlit run app/ui/streamlit_app.py --server.headless true --server.port 8513`
- `curl -I http://127.0.0.1:8513` -> `200 OK`

### Cập nhật Docker/scheduler gần nhất
Đã có:
- `SchedulerService` giờ chuẩn hóa toàn bộ mốc thời gian theo timezone cấu hình thay vì so sánh naive datetime
- file `scheduler_status.json` cũ không có offset vẫn được hiểu là giờ local `Asia/Ho_Chi_Minh`
- stack Docker đã thêm `TIMEZONE/TZ=Asia/Ho_Chi_Minh` cho `api`, `scheduler`, `ui`
- runbook đã bổ sung hướng dẫn reset `scheduler_status.json` nếu scheduler đứng ở `runs: []`

Đi kèm:
- test mới cho case legacy naive timestamp trong `tests/unit/test_scheduler_service.py`

### Cập nhật nguồn báo và tài liệu giao diện gần nhất
Đã có:
- mở rộng thêm feed `news` live cho `VnExpress` ở `thế giới`, `giáo dục`
- mở rộng thêm feed `news` live cho `Dân Trí` ở `giáo dục`, `thể thao`
- mở rộng thêm feed `news` live cho `Thanh Niên` ở `thế giới`, `giáo dục`
- bổ sung file tài liệu riêng mô tả chức năng của giao diện web để phục vụ demo và bàn giao
- siết lại `hot_news` để ưu tiên bài thời sự, kinh tế, giao thông và hạ các bài mềm/human-interest trong feed tổng hợp
- mở rộng router/chat để hiểu thêm biến thể hỏi `Tin hot`, `Top N`, `ở TP.HCM/Hà Nội`, `về giáo dục/tài chính`
- giải mã entity HTML trong title/summary `news` khi trả ra UI/chat để bớt tình trạng `&ocirc;`, `&agrave;`

Đi kèm:
- cập nhật test cấu hình source `news`
- kiểm tra boot Streamlit và helper UI sau khi thay đổi
- thêm test hồi quy cho ranking `Tin hot`
- thêm ma trận khoảng `185` case cho router/runtime chat, nâng tổng suite lên `311` test

### Xác minh live ingest
Đã chạy:
- `.venv/bin/python scripts/run_pipeline.py --pipeline all`
- `.venv/bin/python scripts/run_pipeline.py --pipeline price`
- `.venv/bin/python scripts/run_pipeline.py --pipeline price --source petrolimex_fuel_prices_live --source sbv_fx_rates_live`
- `.venv/bin/python scripts/run_pipeline.py --pipeline price --source vietcombank_fx_rates_live`
- `.venv/bin/python scripts/run_pipeline.py --pipeline weather --source open_meteo_weather_hanoi_live`
- `.venv/bin/python scripts/run_pipeline.py --pipeline policy --source congbao_policy_updates_live`
- `.venv/bin/python scripts/run_pipeline.py --pipeline traffic --source vov_giaothong_traffic_live`

Kết quả:
- `news`: mở rộng lên `4` nguồn live tiếng Việt, ingest thành công `232` bài live trong lần chạy gần nhất
- `news`: đã mở rộng thêm section feed từ `VnExpress`, `Dân Trí`, `Thanh Niên`, nâng tổng số source `news` live lên `10`
- `news`: toàn bộ source `news` hiện dùng cửa sổ ingest `max_age_days=30`, parser RSS đã đọc được `pubDate` kiểu RFC822 để lọc bài quá cũ
- `news`: debug live run cho thấy `dantri_rss_xa_hoi` là feed stale nên đã được thay bằng `dantri_rss_the_gioi`
- `news`: retention đã được tách ra helper dùng lại được, không còn hardcode ở parser riêng lẻ
- `price`: đã có live source chính thức cho `vàng`, `xăng dầu Petrolimex`, `tỷ giá NHNN`, `tỷ giá Vietcombank`
- `price`: full run hiện cho kết quả `sjc_gold_prices`, `petrolimex_fuel_prices`, `sbv_fx_rates` đều `skipped` ngoài `--demo-only`
- `price`: `sjc_gold_prices_live` ingest `2/2`, `petrolimex_fuel_prices_live` ingest `7/7`, `sbv_fx_rates_live` ingest `5/5`, `vietcombank_fx_rates_live` ingest `4/4`
- `price`: API đang trả đúng live data cho `gia-xang-ron95-iii = 26.970 VNĐ/lít` và `ty-gia-usd-ban-ra = 26.312 VNĐ/USD`
- `price`: lookup giá hiện ưu tiên source live ngay cả khi DB vừa seed lại demo; dữ liệu demo chỉ còn vai trò fallback khi chưa có live cùng `item_name`
- `weather`: thêm `TP.HCM`, `Đà Nẵng`, ingest live `3/3`
- `weather`: mở rộng thêm `Hải Phòng`, `Cần Thơ`, `Nha Trang`, nâng tổng số điểm `Open-Meteo` live lên `6`
- `weather`: alias chat/router và demo fixture đã được mở rộng, nên `Hải Phòng`, `Cần Thơ`, `Nha Trang` dùng được cả ở test local lẫn runtime live
- source demo `nchmf_weather_daily` đã được giới hạn cho `--demo-only`
- `policy`: mở rộng lên `3` nguồn live trên `congbao.chinhphu.vn`, mỗi nguồn ingest `10/10`
- source demo `chinhphu_policy_updates` đã được giới hạn cho `--demo-only`
- `policy`: search hiện ưu tiên recent bằng scoring, nhưng không cắt ingest theo ngày nên văn bản cũ vẫn tra cứu được nếu còn liên quan
- `policy`: runtime search hiện ưu tiên source live hơn demo khi cùng có kết quả phù hợp
- `traffic`: có thêm `VnExpress Giao thông` bên cạnh `VOV Giao thông`, ingest `18/18` từ source mới và giữ tiếng Việt có dấu
- source demo `vov_traffic_updates` đã được giới hạn cho `--demo-only`
- `traffic`: parser và repository đã có thêm lọc relevance để loại các bài lệch chủ đề khỏi ingest mới và khỏi API runtime
- `traffic`: source live hiện dùng `max_age_days=14`, áp cả lúc ingest và lúc đọc dữ liệu
- `traffic`: debug runtime đã phát hiện metadata DB cũ làm lẫn source demo vào API; read-path hiện đã ưu tiên config mới từ `config/sources.yml` để loại hiện tượng này
- `traffic`: debug runtime cũng đã siết điều kiện headline/summary để loại bớt bản tin quá rộng khi không có tín hiệu giao thông ngay từ tiêu đề
- `traffic`: sau khi restart API, `GET /traffic/latest?limit=5` không còn trả `vov_traffic_updates` trong top 5 mới nhất
- `cleanup`: dry-run bằng `scripts/run_cleanup.py` trên PostgreSQL local chạy thành công; tại thời điểm verify chưa có bản ghi nào vượt retention nên cả 4 nhóm đều `matched_rows=0`
- `cleanup`: retention cleanup hiện đã đọc qua `config/retention.yml`

### Xác minh scheduler local
Đã chạy:
- `.venv/bin/python scripts/run_scheduler.py --demo-only --run-once --pipeline news --source vnexpress_rss_tin_moi --status-file /tmp/scheduler-status.json`
- `.venv/bin/python scripts/run_scheduler.py --show-status --pipeline news --source vnexpress_rss_tin_moi --status-file /tmp/scheduler-status.json`

Kết quả:
- Chạy được một vòng scheduler local
- Có ghi `run_count`, `last_status`, `next_run_at`
- Scheduler status hiện có thêm `summary`, `health_state`, `failure_streak`, `attention_sources`
- File trạng thái đọc lại được đúng
- Đã sửa bug `last_duration_seconds` luôn bằng `0.0`; scheduler giờ đo duration theo `perf_counter()` nhưng vẫn giữ tương thích với test mô phỏng thời gian

### Xác minh Phase D experimental
Đã chạy:
- `.venv/bin/python scripts/seed_demo_data.py --demo-only`
- `.venv/bin/python scripts/build_retrieval_index.py --doc-type all`
- Test thủ công `topic_summary` với câu hỏi về `xe công cộng điện`
- Test thủ công `policy_lookup` với câu hỏi về `học đường`

Kết quả:
- Build index thành công: `article=6`, `policy=2`
- `topic_summary` dùng retrieval và trả về 2 bài về `buýt điện`
- `policy_lookup` dùng semantic fallback và trả về văn bản `tuyển sinh đầu cấp`

### Debug runtime gần nhất
Đã xử lý:
- `/traffic/latest` tổng quát giờ xếp hạng theo `traffic relevance score` thay vì chỉ ưu tiên thời gian
- Các bài thiên về `quy định`, `thủ tục`, `đăng kiểm`, `đề xuất` bị hạ điểm
- Các bài `cấm đường`, `ùn tắc`, `tai nạn`, `thông xe` được ưu tiên lên đầu feed tổng quát

### Deploy và handoff gần nhất
Đã có:
- `docker-compose.yml` root cho local/dev full stack
- `06_deployment/docker-compose.yml` cho biến thể triển khai tham chiếu
- service Docker:
  - `postgres`
  - `api`
  - `ui`
  - `scheduler`
  - `seed_demo`
  - `refresh_live_prices`
- `.env.production.example`
- `06_deployment/RUNBOOK.md`
- `06_deployment/DEMO_SCRIPT.md`

Lưu ý:
- `api` và `scheduler` tự chạy migration khi start
- `seed_demo` là service chạy một lần để reset và nạp lại demo data
- `refresh_live_prices` là service/lệnh riêng để làm mới lại giá live sau khi đã seed demo
- stack Docker hiện mặc định dùng PostgreSQL nội bộ, không đi theo SQLite fallback trong container
- Khi OpenAI không sẵn sàng, chat vẫn fallback nội bộ

## Những gì đã hoàn tất cho local/demo
- Chạy local bằng PostgreSQL hoặc SQLite fallback
- `alembic upgrade head` đủ ổn định cho local SQLite
- `/health` báo đúng database runtime thực tế
- `.env.example` an toàn hơn cho local
- Seed/demo data có tiếng Việt có dấu
- Query không dấu vẫn dùng được cho các case phổ biến
- `/chat/query` không còn văng `500`
- Khi OpenAI lỗi hoặc hết quota, chat fallback sang agent nội bộ
- `price` lookup mặc định hiện ưu tiên live source thật thay vì fixture cho `vàng`, `xăng`, `USD`
- Router chat không còn tự rơi về `hot_news` khi gặp nhãn UI hoặc câu hỏi quá mơ hồ
- Router chat đã mở rộng cho câu hỏi chủ đề `chính trị`, `tài chính` và trả thông báo rõ hơn khi hỏi thời tiết ở địa điểm chưa có dữ liệu
- Router chat đã xử lý đúng hơn cho `cảnh báo thời tiết`, `đường bị cấm`, alias policy `học đường`, và precision topic summary/source compare cho `tài chính`, `chính trị`, `giáo dục`
- `policy` lookup hiện ưu tiên source live hơn demo ở runtime
- `traffic` lookup hiện hiểu focus `cấm đường`, `ùn tắc`, `tai nạn` và ưu tiên precision hơn recall
- Agent hiện đã có thêm giao tiếp cơ bản cho `chào bạn`, `bạn là gì`, `bạn giúp được gì`, `cảm ơn`, `tạm biệt`
- UI demo chạy được với backend local
- UI Streamlit đã được làm lại theo dạng dashboard biên tập, có hero lớn, cụm tin nổi bật, bảng điều phối và tab `Data Browser`
- Khối `Tình trạng hệ thống` đã được tách thành dải full-width riêng, hiển thị rõ API, database runtime, chat mode và retrieval thay vì trộn với số liệu dữ liệu
- Dashboard hiện có thêm khối `Sức khỏe nguồn dữ liệu`, đọc trực tiếp từ `scheduler_status.json` để hiển thị `health_state`, `failure_streak` và `attention_sources`
- Các block HTML của dashboard đã được chuẩn hóa render để không còn bị Streamlit hiển thị như code thô khi thay đổi layout
- UI đã chuyển sang `st.html` cho các block HTML chính và thay API `use_container_width` cũ bằng `width="stretch"` để tránh warning runtime
- Chat launcher hiển thị dưới dạng avatar tròn nổi, có bubble gợi ý và mở hộp chat trực tiếp từ giao diện
- Luồng chat UI đã được làm mượt hơn: giữ câu hỏi ngay khi gửi, hiển thị trạng thái đang tìm thông tin, rồi mới chèn câu trả lời
- UI hiện có thêm `Data Browser` để xem dữ liệu theo bảng ngay trong Streamlit mà không cần viết SQL
- Có thể demo Phase D experimental bằng feature flag

## Hạn chế hiện tại
- Retrieval hiện là sparse local index, chưa phải embedding/RAG thật
- OpenAI tool path chưa được mở rộng toàn bộ để dùng retrieval ở mọi intent
- Policy hiện ưu tiên metadata và trích yếu, chưa đọc toàn văn PDF/OCR
- Scheduler hiện phù hợp local/demo, chưa phải production scheduler
- Traffic chưa có geocoding hoặc chuẩn hóa theo tọa độ
- Một số parser live vẫn phụ thuộc cấu trúc HTML của website nguồn
- `petrolimex_fuel_prices_live` hiện lấy giá `Vùng 1`; `Vùng 2` chưa được surfaced riêng ở API/UI

## Experimental
- Phase D: retrieval/index local-first cho `news` và `policy`

Phạm vi experimental hiện tại:
- Chỉ dùng cho `topic_summary`
- Chỉ dùng cho semantic `policy_lookup`
- Bật/tắt bằng feature flag
- Luôn có fallback về flow cũ khi retrieval tắt hoặc lỗi

## TODO hợp lý tiếp theo
1. Nâng Phase D từ sparse local retrieval lên embedding/RAG thật.
2. Bổ sung trích xuất toàn văn PDF cho `policy`.
3. Cân nhắc geocoding cho `traffic` nếu muốn nâng chất lượng lọc theo khu vực.
4. Nếu muốn cleanup linh hoạt hơn, mở rộng `config/retention.yml` theo từng pipeline hoặc từng source.
5. Nếu chuyển sang môi trường lâu dài, thay scheduler local bằng công cụ điều phối phù hợp hơn.

## Blocker hiện tại
- Không có blocker kỹ thuật lớn cho local/demo.
- Nếu muốn dùng OpenAI thật, cần `OPENAI_API_KEY` hợp lệ và có quota.
- 2026-04-05: Hoàn thiện thêm vòng UX cuối cho chat và dashboard.
  - Chat hiểu tốt hơn các câu hỏi kiểu tiêu đề bài báo/câu tự nhiên dài, không còn dễ rơi về `Chưa hiểu rõ câu hỏi`.
  - Khối `Mục liên quan` trong chat đã thu gọn về font, spacing và nút bấm để đồng bộ hơn với phần trả lời của trợ lý.
  - Dashboard có thêm `Biểu đồ nhanh` cho quy mô dữ liệu, nguồn trong tin hot và biên độ nhiệt độ theo điểm.
- 2026-04-05: Chuyển nhóm thao tác item sang kiểu menu ngữ cảnh gọn.
  - Các card preview và item trong chat không còn đổ nhiều nút trực tiếp dưới nội dung.
  - Thay vào đó dùng `Thao tác` / `Tác vụ` để mở menu gồm `Xem chi tiết`, `Tóm tắt bằng AI`, `Hỏi AI`, `Mở nguồn` tùy ngữ cảnh.
- 2026-04-05: Chỉnh lại menu thao tác theo hướng nhìn thấy rõ hơn.
  - Không còn phụ thuộc `popover` để mở action.
  - Mỗi item giờ có nút hiện rõ `Thao tác ▼`, bấm vào sẽ bung ra các action thật bên dưới.
  - Đã audit lại dữ liệu live: `news`, `price`, `weather` vẫn đang cập nhật; `policy` và `traffic` đang chạy thành công nhưng nhiều vòng gần đây không phát sinh bản ghi mới nên `total_success=0`.
- 2026-04-05: Bổ sung tài liệu `.txt` tổng hợp về AI agent, pipeline, lưu trữ, UI flow và hướng phát triển để phục vụ handoff/demo.
- 2026-04-05: Cập nhật tài liệu hướng dẫn người dùng cuối.
  - Thêm `docs/huong-dan-nguoi-dung.md`.
  - README, run-local, hướng dẫn chạy nhanh và tài liệu UI đều đã trỏ tới luồng thao tác mới với `Thao tác ▼`.
