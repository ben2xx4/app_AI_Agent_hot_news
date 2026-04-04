# Tiến độ triển khai

## Trạng thái tổng quan
- MVP nền tảng đã hoàn thành.
- Phase A đã hoàn thành: parser live cho 5 nhóm nguồn.
- Phase B đã hoàn thành: bộ test conversation mẫu và test fallback chat.
- Phase C đã hoàn thành: scheduler local.
- Phase D đã được triển khai ở mức experimental, local-first và có thể demo.

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

## Kết quả xác minh gần nhất
Thời điểm cập nhật: `2026-04-04`

### Kiểm thử
Đã chạy:
- `.venv/bin/ruff check app scripts tests`
- `.venv/bin/pytest -q`

Kết quả:
- `ruff`: pass
- `pytest`: `48 passed`

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
- `price`: đã có live source chính thức cho `vàng`, `xăng dầu Petrolimex`, `tỷ giá NHNN`, `tỷ giá Vietcombank`
- `price`: full run hiện cho kết quả `sjc_gold_prices`, `petrolimex_fuel_prices`, `sbv_fx_rates` đều `skipped` ngoài `--demo-only`
- `price`: `sjc_gold_prices_live` ingest `2/2`, `petrolimex_fuel_prices_live` ingest `7/7`, `sbv_fx_rates_live` ingest `5/5`, `vietcombank_fx_rates_live` ingest `4/4`
- `price`: API đang trả đúng live data cho `gia-xang-ron95-iii = 26.970 VNĐ/lít` và `ty-gia-usd-ban-ra = 26.312 VNĐ/USD`
- `price`: lookup giá hiện ưu tiên source live ngay cả khi DB vừa seed lại demo; dữ liệu demo chỉ còn vai trò fallback khi chưa có live cùng `item_name`
- `weather`: thêm `TP.HCM`, `Đà Nẵng`, ingest live `3/3`
- source demo `nchmf_weather_daily` đã được giới hạn cho `--demo-only`
- `policy`: mở rộng lên `3` nguồn live trên `congbao.chinhphu.vn`, mỗi nguồn ingest `10/10`
- source demo `chinhphu_policy_updates` đã được giới hạn cho `--demo-only`
- `traffic`: có thêm `VnExpress Giao thông` bên cạnh `VOV Giao thông`, ingest `18/18` từ source mới và giữ tiếng Việt có dấu
- source demo `vov_traffic_updates` đã được giới hạn cho `--demo-only`
- `traffic`: parser và repository đã có thêm lọc relevance để loại các bài lệch chủ đề khỏi ingest mới và khỏi API runtime

### Xác minh scheduler local
Đã chạy:
- `.venv/bin/python scripts/run_scheduler.py --demo-only --run-once --pipeline news --source vnexpress_rss_tin_moi --status-file /tmp/scheduler-status.json`
- `.venv/bin/python scripts/run_scheduler.py --show-status --pipeline news --source vnexpress_rss_tin_moi --status-file /tmp/scheduler-status.json`

Kết quả:
- Chạy được một vòng scheduler local
- Có ghi `run_count`, `last_status`, `next_run_at`
- File trạng thái đọc lại được đúng

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
- Agent hiện đã có thêm giao tiếp cơ bản cho `chào bạn`, `bạn là gì`, `bạn giúp được gì`, `cảm ơn`, `tạm biệt`
- UI demo chạy được với backend local
- UI Streamlit đã được làm lại theo dạng dashboard card và có avatar chat tròn nổi, kèm bubble gợi ý để mở hộp chat nhanh
- Luồng chat UI đã được làm mượt hơn: giữ câu hỏi ngay khi gửi, hiển thị trạng thái đang tìm thông tin, rồi mới chèn câu trả lời
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
4. Nếu chuyển sang môi trường lâu dài, thay scheduler local bằng công cụ điều phối phù hợp hơn.

## Blocker hiện tại
- Không có blocker kỹ thuật lớn cho local/demo.
- Nếu muốn dùng OpenAI thật, cần `OPENAI_API_KEY` hợp lệ và có quota.
