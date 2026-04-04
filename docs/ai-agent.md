# AI Agent và lớp hỏi đáp

## Mục tiêu
AI agent nhận câu hỏi tiếng Việt, phân loại intent, gọi tool nội bộ, sau đó tổng hợp câu trả lời dựa trên dữ liệu trong database.

## Intent hiện có
- `hot_news`
- `price_lookup`
- `price_compare`
- `weather_lookup`
- `policy_lookup`
- `traffic_lookup`
- `topic_summary`
- `source_compare`

## Tool nội bộ hiện có
- `get_hot_news`
- `search_news`
- `get_latest_price`
- `compare_price`
- `get_weather`
- `search_policy`
- `get_traffic_updates`

## Hai chế độ vận hành
### 1. Fallback nội bộ
- Dùng intent router rule-based
- Dùng service layer trả JSON
- Format câu trả lời bằng Python
- Là đường fallback mặc định khi OpenAI lỗi hoặc không có key

### 2. OpenAI mode
- Bật khi `CHAT_USE_OPENAI=true` và có `OPENAI_API_KEY`
- Dùng Responses API function calling
- Tool schema đang ở strict mode để tránh lỗi schema
- Nếu OpenAI request fail hoặc quota giới hạn, hệ thống quay lại fallback nội bộ

## Hành vi hiện tại của `POST /chat/query`
- Không đổi contract API hiện có
- Payload luôn có:
  - `question`
  - `intent`
  - `tool_called`
  - `answer`
  - `sources`
  - `updated_at`
  - `data`
- Nếu OpenAI không sẵn sàng, endpoint không nên trả `500` cho các case đã hỗ trợ; hệ thống sẽ fallback nội bộ

## Retrieval experimental của Phase D
### Trạng thái
- Đã triển khai ở mức nhỏ gọn
- Đang được gắn nhãn experimental
- Không thay thế structured lookup hiện có

### Cách hoạt động
- `news` và `policy` được chia chunk vào `document_embeddings`
- `embedding_vector_json` lưu vector thưa local-first
- Không dùng `pgvector` ở pha này
- New ingest của `news` và `policy` tự ghi index experimental
- Có thể backfill bằng:
```bash
.venv/bin/python scripts/build_retrieval_index.py --doc-type all
```

### Feature flag
```bash
EXPERIMENTAL_RETRIEVAL_ENABLED=true
```

### Nơi retrieval đang được dùng
- `topic_summary` trong fallback nội bộ
- `policy_lookup` khi keyword/filter yếu

### Nơi retrieval chưa được dùng
- Không thay structured lookup cho `price`, `weather`, `traffic`
- Không mở rộng toàn bộ OpenAI tool path ở pha này

### Fallback
- Nếu feature flag tắt, chat dùng flow cũ
- Nếu chưa có index, chat dùng flow cũ
- Nếu retrieval lỗi, service log warning và trả về flow cũ

## Ví dụ demo retrieval
Khi bật `EXPERIMENTAL_RETRIEVAL_ENABLED=true`, có thể thử:
```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Có những chủ đề nào về xe công cộng điện đang được nhiều báo nói tới?"}'
```

Hoặc:
```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Có văn bản nào về học đường không?"}'
```

## Nguyên tắc an toàn
- Không crawl web trực tiếp từ agent
- Không cho model tự viết SQL
- Nếu dữ liệu quá cũ, câu trả lời phải nêu rõ thời điểm cập nhật
- Nếu không đủ dữ liệu, phải nói rõ chưa có dữ liệu
- Retrieval experimental phải luôn có fallback sạch về flow cũ

## Giới hạn hiện tại
- Retrieval hiện là sparse local index, chưa phải embedding vector thật
- Chưa có reranker hoặc semantic search production-grade
- Chưa có đọc toàn văn PDF/OCR cho `policy`
- Chưa có memory hoặc multi-turn conversation phức tạp

## Hướng phát triển tiếp theo
- Nâng Phase D sang embedding/RAG thật
- Cân nhắc `pgvector` hoặc vector store phù hợp khi cần production
- Mở rộng retrieval cho nhiều intent hơn sau khi đủ ổn định
