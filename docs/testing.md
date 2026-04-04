# Kiểm thử

## Mục tiêu
- Đảm bảo pipeline, service, API và chat chạy được end-to-end trong môi trường local.
- Giữ ổn định luồng demo ngay cả khi PostgreSQL, OpenAI hoặc retrieval experimental không sẵn sàng.
- Phát hiện sớm lỗi parser khi source live đổi cấu trúc.

## Cách chạy test
### Chạy toàn bộ test
```bash
.venv/bin/pytest -q
```

### Chạy smoke test parser live
```bash
.venv/bin/pytest -q tests/unit/test_live_parsers.py
```

### Chạy test conversation và fallback chat
```bash
.venv/bin/pytest -q tests/unit/test_chat_conversations.py tests/unit/test_chat_agent.py
```

### Chạy test retrieval experimental
```bash
.venv/bin/pytest -q tests/unit/test_retrieval_experimental.py
```

### Chạy test scheduler local
```bash
.venv/bin/pytest -q tests/unit/test_scheduler_service.py
```

### Chạy test API integration
```bash
.venv/bin/pytest -q tests/integration
```

## Nhóm test hiện có
### 1. Unit test cho pipeline và parser
- `tests/unit/test_news_pipeline.py`
- `tests/unit/test_price_pipeline.py`
- `tests/unit/test_processing.py`
- `tests/unit/test_live_parsers.py`

Bao phủ:
- Parser demo cho `news` và `price`
- Xử lý chuẩn hóa và dedup cơ bản
- Smoke test cho parser live của cả 5 pipeline

### 2. Unit test cho chat
- `tests/unit/test_chat_agent.py`
- `tests/unit/test_chat_conversations.py`

Bao phủ:
- Tool schema strict cho OpenAI tool-calling
- Fallback khi OpenAI unavailable
- Bộ câu hỏi hội thoại mẫu theo intent

### 3. Unit test cho retrieval experimental
- `tests/unit/test_retrieval_experimental.py`

Bao phủ:
- Build index cho `news` và `policy`
- Semantic retrieval cơ bản
- Fallback khi retrieval tắt
- Fallback khi retrieval lỗi
- Chat flow cho `topic_summary` và `policy_lookup` có dùng retrieval

### 4. Unit test cho scheduler local
- `tests/unit/test_scheduler_service.py`

Bao phủ:
- Chạy job đến hạn
- Ghi file trạng thái
- Lọc theo `pipeline` và `source`

### 5. Integration test cho API
- `tests/integration/test_api_endpoints.py`
- `tests/integration/test_api_health.py`

Bao phủ:
- `/health`
- `news`, `prices`, `weather`, `policies`, `traffic`
- `POST /chat/query`

## Conversation test coverage theo intent
Hiện đã có test tự động cho các intent sau:
- `hot_news`
- `price_lookup`
- `price_compare`
- `weather_lookup`
- `policy_lookup`
- `traffic_lookup`
- `topic_summary`
- `source_compare`

Đặc điểm của bộ test:
- Không so khớp từng chữ của câu trả lời
- Chỉ assert ý chính, tool được gọi và dữ liệu trả về đúng nhóm
- Phù hợp với fallback nội bộ hiện tại

## Test fallback khi OpenAI unavailable
Đã có test mô phỏng OpenAI lỗi để xác nhận:
- `ChatService` không làm văng lỗi `500`
- Agent tự fallback sang logic nội bộ
- Payload trả về vẫn có `answer`, `tool_called`, `data`

## Test retrieval experimental
### Phạm vi hiện có
- `news`: retrieval local-first cho `topic_summary`
- `policy`: semantic fallback cho `policy_lookup`

### Điều được kiểm tra
- Index được ghi vào `document_embeddings`
- `embedding_model` đúng là `experimental-local-sparse-v1`
- Query semantic đơn giản như `xe cong cong dien` và `hoc duong` trả về đúng nhóm tài liệu
- Khi retrieval tắt hoặc lỗi, service quay về keyword flow cũ

### Giới hạn test
- Đây chưa phải benchmark semantic search.
- Chưa có recall/precision test ở quy mô lớn.
- Chưa có test cho Phase D production-grade vì chưa triển khai.

## Smoke test cho live parsers
`tests/unit/test_live_parsers.py` dùng fixture HTML/XML/JSON đã chụp sẵn để test:
- `news`: `Tuổi Trẻ RSS + detail HTML`
- `price`: `Vietcombank XML`
- `weather`: `Open-Meteo JSON`
- `policy`: `Công báo Chính phủ HTML`
- `traffic`: `VOV Giao thông HTML`

Mục tiêu của smoke test:
- Không phụ thuộc mạng khi chạy test
- Bắt lỗi selector/parser khi code thay đổi
- Xác nhận record parse ra có trường chính đúng

## Cách đọc kết quả test
### Khi pass
Ví dụ:
```text
33 passed in 2.62s
```

Ý nghĩa:
- Toàn bộ suite local hiện tại chạy thành công
- Có thể tiếp tục demo hoặc bàn giao

### Khi fail
Ưu tiên đọc theo nhóm:
- Nếu fail ở `test_live_parsers.py`: thường là parser/source schema
- Nếu fail ở `test_chat_conversations.py`: thường là intent routing hoặc format payload chat
- Nếu fail ở `test_retrieval_experimental.py`: thường là feature flag, index chưa build hoặc semantic threshold
- Nếu fail ở `test_scheduler_service.py`: thường là logic lịch chạy hoặc state file
- Nếu fail ở `tests/integration`: thường là service/API hoặc seed dữ liệu

## Trạng thái kiểm thử hiện tại
Kết quả xác minh gần nhất:
```bash
.venv/bin/ruff check app scripts tests
.venv/bin/pytest -q
```

Kết quả:
```text
ruff: pass
pytest: 33 passed
```

## Lưu ý khi chạy test
- Test dùng SQLite để giảm phụ thuộc hệ thống.
- Seed test đi từ fixture/demo data, không yêu cầu PostgreSQL.
- Test parser live không gọi mạng ngoài.
- Test retrieval experimental không yêu cầu OpenAI.
- Nếu muốn kiểm tra live ingest thật, dùng `scripts/run_pipeline.py` thay vì test suite.

## Trạng thái hiện tại
### Đã hoàn thành
- Unit test cho parser/demo flow
- Smoke test parser live
- Conversation test cho 8 intent chính
- Test fallback khi OpenAI unavailable
- Integration test cho API chính
- Unit test cho scheduler local
- Test retrieval experimental cơ bản

### Experimental
- Retrieval `news` và `policy` chỉ đang ở mức local sparse index

### TODO
- Benchmark chất lượng retrieval ngữ nghĩa
- Test cho embedding/RAG thật khi Phase D được nâng cấp tiếp
