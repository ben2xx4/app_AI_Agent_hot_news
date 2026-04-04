# Kế hoạch triển khai

## Nguyên tắc
- Triển khai theo phase, không nhảy cóc UI trước backend và storage.
- PostgreSQL là database chính cho môi trường local/dev/prod.
- Cho phép fallback sang fixture/seed để bảo toàn luồng end-to-end khi nguồn ngoài lỗi hoặc thay đổi format.
- Mọi tài liệu kỹ thuật, comment mô tả ngắn và hướng dẫn vận hành viết bằng tiếng Việt.

## Tổng quan stack đã chốt
- Backend: FastAPI
- Database: PostgreSQL, SQLAlchemy, Alembic
- Raw storage: filesystem cục bộ theo cây thư mục pipeline/source/date
- Pipeline: Python, httpx, feedparser, BeautifulSoup
- AI: OpenAI Responses API với function calling, có fallback nội bộ khi chưa cấu hình API key
- UI demo: Streamlit
- Test: pytest
- Đóng gói local: Docker Compose

## Phase 0: Khảo sát repo và lập kế hoạch
- Mục tiêu:
  - Đọc toàn bộ tài liệu chỉ dẫn
  - Chốt kiến trúc MVP và giả định kỹ thuật
  - Tạo `PLAN.md`
  - Chốt cây thư mục, cấu hình `.env`, cách chạy local
- File tạo/sửa:
  - `PLAN.md`
  - `README.md`
  - `docs/architecture.md`
  - `docs/run-local.md`
- Cách chạy kiểm tra:
  - Đối chiếu tài liệu trong repo
  - Kiểm tra cây thư mục và file cấu hình nền tảng đã xuất hiện
- Tiêu chí hoàn thành:
  - Có kế hoạch đầy đủ theo phase
  - Có mô tả phụ thuộc giữa các phase
  - Có quyết định kỹ thuật cốt lõi được ghi lại
- Trạng thái: `hoàn thành`

## Phase 1: Setup nền tảng dự án
- Mục tiêu:
  - Tạo skeleton FastAPI
  - Cấu hình môi trường, logging, lint, format, test
  - Tạo `.env.example`, `pyproject.toml`, `docker-compose.yml`
  - Tạo migration đầu tiên
- File tạo/sửa:
  - `pyproject.toml`
  - `.env.example`
  - `docker-compose.yml`
  - `Makefile`
  - `alembic.ini`
  - `alembic/`
  - `app/core/*`
  - `app/main.py`
- Cách chạy kiểm tra:
  - `python3 -m compileall app scripts tests`
  - `alembic upgrade head`
  - `uvicorn app.main:app --reload`
- Tiêu chí hoàn thành:
  - App khởi động được
  - Có cấu hình DB và logging
  - Có migration đầu tiên
- Trạng thái: `hoàn thành`

## Phase 2: Storage và database
- Mục tiêu:
  - Hoàn thiện schema bắt buộc
  - Tạo repository layer
  - Tạo raw storage abstraction
  - Có seed dữ liệu và kiểm tra kết nối DB
- File tạo/sửa:
  - `app/db/*`
  - `app/models/*`
  - `app/repositories/*`
  - `docs/database.md`
  - `scripts/seed_demo_data.py`
- Cách chạy kiểm tra:
  - `python3 scripts/seed_demo_data.py --demo-only`
  - `pytest tests/integration/test_api_health.py`
- Tiêu chí hoàn thành:
  - Schema đồng bộ với migration
  - Raw storage ghi được file
  - Seed đẩy được dữ liệu vào DB
- Trạng thái: `hoàn thành`

## Phase 3: 5 pipeline ingestion
- Mục tiêu:
  - Tạo 5 pipeline độc lập
  - Mỗi pipeline có parser, retry, timeout, logging
  - Chạy được ở chế độ demo và có thể thử live
- File tạo/sửa:
  - `app/pipelines/common/*`
  - `app/pipelines/news/*`
  - `app/pipelines/price/*`
  - `app/pipelines/weather/*`
  - `app/pipelines/policy/*`
  - `app/pipelines/traffic/*`
  - `config/sources.yml`
  - `data/fixtures/*`
- Cách chạy kiểm tra:
  - `python3 scripts/run_pipeline.py --pipeline news --demo-only`
  - `python3 scripts/run_pipeline.py --pipeline all --demo-only`
- Tiêu chí hoàn thành:
  - Mỗi pipeline chèn được dữ liệu sạch vào DB
  - Có raw storage và crawl_jobs tương ứng
  - Có test parser/demo cho từng pipeline
- Trạng thái: `hoàn thành`

## Phase 4: Processing và chuẩn hóa dữ liệu
- Mục tiêu:
  - Cleaner, normalizer, validator
  - Exact duplicate và near duplicate cho news
  - Chunk document cho AI retrieval
- File tạo/sửa:
  - `app/pipelines/common/processing.py`
  - `app/services/retrieval_service.py`
  - `docs/pipelines.md`
- Cách chạy kiểm tra:
  - `pytest tests/unit/test_news_pipeline.py`
  - `pytest tests/unit/test_processing.py`
- Tiêu chí hoàn thành:
  - News dedup hoạt động
  - Chính sách có chunk để truy xuất
  - Dữ liệu chuẩn hóa nhất quán
- Trạng thái: `hoàn thành`

## Phase 5: Backend API
- Mục tiêu:
  - Mở toàn bộ endpoint bắt buộc
  - Chuẩn hóa schema request/response
  - Có OpenAPI và test endpoint
- File tạo/sửa:
  - `app/api/*`
  - `app/schemas/*`
  - `app/services/*`
  - `docs/api.md`
- Cách chạy kiểm tra:
  - `pytest tests/integration/test_api_endpoints.py`
  - `uvicorn app.main:app --reload`
- Tiêu chí hoàn thành:
  - Endpoint phản hồi JSON rõ ràng
  - Có validation
  - Có xử lý lỗi chuẩn
- Trạng thái: `hoàn thành`

## Phase 6: AI layer
- Mục tiêu:
  - Intent router
  - Internal tool registry
  - Tích hợp OpenAI API và fallback không cần API key
  - `POST /chat/query` trả lời bằng tiếng Việt từ dữ liệu nội bộ
- File tạo/sửa:
  - `app/agent/*`
  - `app/services/chat_service.py`
  - `docs/ai-agent.md`
- Cách chạy kiểm tra:
  - `pytest tests/unit/test_chat_agent.py`
  - `python3 scripts/demo_chat.py`
- Tiêu chí hoàn thành:
  - Có 8 intent tối thiểu
  - Có tool nội bộ tối thiểu
  - Không hardcode câu trả lời
- Trạng thái: `hoàn thành`

## Phase 7: UI demo
- Mục tiêu:
  - Trang xem tin hot
  - Trang xem giá mới nhất
  - Ô hỏi đáp tiếng Việt
- File tạo/sửa:
  - `app/ui/streamlit_app.py`
- Cách chạy kiểm tra:
  - `streamlit run app/ui/streamlit_app.py`
- Tiêu chí hoàn thành:
  - UI chạy local
  - Kết nối được API backend
- Trạng thái: `hoàn thành`

## Phase 8: Testing end-to-end
- Mục tiêu:
  - Unit test parser/service chính
  - Integration test API
  - Kiểm tra flow ingest -> store -> query -> answer
- File tạo/sửa:
  - `tests/*`
  - `docs/testing.md`
  - `scripts/quick_test.sh`
- Cách chạy kiểm tra:
  - `pytest`
  - `bash scripts/quick_test.sh`
- Tiêu chí hoàn thành:
  - Có test cho parser/service/API/chat
  - Có script test nhanh
- Trạng thái: `hoàn thành`

## Phase 9: Deployment và handoff
- Mục tiêu:
  - Hoàn thiện Docker Compose
  - Tạo runbook local
  - Tạo checklist bàn giao và kịch bản demo
- File tạo/sửa:
  - `docker-compose.yml`
  - `docker/*`
  - `docs/run-local.md`
  - `FINAL_HANDOFF.md`
  - `DEMO_SCRIPT.md`
- Cách chạy kiểm tra:
  - `docker compose up -d postgres`
  - `make run-api`
  - `make run-ui`
- Tiêu chí hoàn thành:
  - Có hướng dẫn dựng local rõ ràng
  - Có checklist nghiệm thu
  - Có ghi rõ giới hạn còn lại
- Trạng thái: `hoàn thành`

## Phase 10A: Parser live cho nguồn thật
- Mục tiêu:
  - Bổ sung ít nhất 1 nguồn live thật cho mỗi pipeline: news, price, weather, policy, traffic
  - Tách cấu hình nguồn và metadata parse ra rõ ràng trong `config/sources.yml`
  - Có timeout, retry, logging và fallback fixture khi nguồn live lỗi
  - Không làm vỡ luồng local đang chạy với SQLite fallback và demo seed
- File dự kiến tạo/sửa:
  - `config/sources.yml`
  - `app/pipelines/common/*`
  - `app/pipelines/news/*`
  - `app/pipelines/price/*`
  - `app/pipelines/weather/*`
  - `app/pipelines/policy/*`
  - `app/pipelines/traffic/*`
  - `scripts/run_pipeline.py`
  - `README.md`
  - `docs/pipelines.md`
  - `docs/run-local.md`
  - `tests/unit/*`
- Cách chạy kiểm tra:
  - `.venv/bin/python scripts/run_pipeline.py --pipeline news`
  - `.venv/bin/python scripts/run_pipeline.py --pipeline price`
  - `.venv/bin/python scripts/run_pipeline.py --pipeline weather`
  - `.venv/bin/python scripts/run_pipeline.py --pipeline policy`
  - `.venv/bin/python scripts/run_pipeline.py --pipeline traffic`
  - `.venv/bin/pytest -q tests/unit`
- Tiêu chí hoàn thành:
  - Mỗi nhóm có ít nhất 1 parser live chạy được khi mạng ngoài phản hồi bình thường
  - Nếu nguồn ngoài lỗi, pipeline không crash toàn app và vẫn fallback demo nếu được cấu hình
  - Có smoke test parser cho từng nguồn
- Trạng thái: `hoàn thành`

## Phase 10B: Bộ test conversation mẫu
- Mục tiêu:
  - Tạo bộ test hội thoại bám `08_prompts/CAU_HOI_MAU.md`
  - Bao phủ `hot_news`, `price_lookup`, `price_compare`, `weather_lookup`, `policy_lookup`, `traffic_lookup`, `topic_summary`, `source_compare`
  - Có trường hợp OpenAI unavailable để kiểm tra fallback nội bộ
- File dự kiến tạo/sửa:
  - `tests/unit/test_chat_agent.py`
  - `tests/integration/*chat*`
  - `data/fixtures/chat/*`
  - `docs/testing.md`
- Cách chạy kiểm tra:
  - `.venv/bin/pytest -q tests/unit/test_chat_agent.py`
  - `.venv/bin/pytest -q tests/integration`
- Tiêu chí hoàn thành:
  - Test không so từng chữ nhưng xác nhận đúng ý chính
  - Có fixture hoặc stub rõ ràng cho dữ liệu nền
  - Có test fallback khi OpenAI lỗi/quota
- Trạng thái: `hoàn thành`

## Phase 10C: Scheduler local
- Mục tiêu:
  - Có scheduler local đơn giản để chạy từng pipeline theo lịch riêng
  - Có logging job run và trạng thái cơ bản
  - Có hướng dẫn chạy scheduler local
- File dự kiến tạo/sửa:
  - `scripts/run_scheduler.py`
  - `app/services/*scheduler*`
  - `README.md`
  - `docs/run-local.md`
  - `docs/pipelines.md`
- Cách chạy kiểm tra:
  - `.venv/bin/python scripts/run_scheduler.py`
  - `.venv/bin/python scripts/run_pipeline.py --pipeline all --demo-only`
- Tiêu chí hoàn thành:
  - Có thể chạy lặp theo lịch riêng cho từng pipeline
  - Có log dễ đọc và quan sát trạng thái job
  - Không làm cứng hóa môi trường local
- Trạng thái: `hoàn thành`

## Phase 10D: Embedding/RAG cơ bản
- Mục tiêu:
  - Tạo indexing cơ bản cho bài báo và chính sách
  - Bổ sung retrieval ngữ nghĩa cho `topic_summary` hoặc `policy lookup`
  - Giữ nguyên lookup structured hiện có
  - Đánh dấu `experimental` nếu chưa đủ ổn định
- File dự kiến tạo/sửa:
  - `app/services/retrieval_service.py`
  - `app/services/retrieval_index_service.py`
  - `app/agent/*`
  - `app/repositories/embedding_repository.py`
  - `scripts/build_retrieval_index.py`
  - `docs/ai-agent.md`
  - `docs/testing.md`
  - `tests/*`
- Cách chạy kiểm tra:
  - `.venv/bin/python scripts/build_retrieval_index.py --doc-type all`
  - `.venv/bin/python scripts/demo_chat.py`
  - `.venv/bin/pytest -q tests/unit/test_chat_agent.py`
  - `.venv/bin/pytest -q tests/unit/test_retrieval_experimental.py`
- Tiêu chí hoàn thành:
  - Có flow index và retrieval cơ bản
  - Không phá API/chat fallback hiện có
  - Tính năng được ghi rõ giới hạn
- Trạng thái: `hoàn thành ở mức experimental`

## TODO còn lại sau bản audit ngày 2026-04-04
- Nâng Phase 10D từ sparse local retrieval sang embedding/RAG thật.
- Bổ sung đọc toàn văn PDF/OCR cho `policy`.
- Cân nhắc mở rộng retrieval sang nhiều intent hơn sau khi đủ ổn định.
- Nâng scheduler local từ demo/local sang mức production nếu cần.
