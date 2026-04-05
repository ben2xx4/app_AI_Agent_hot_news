# Stack triển khai hiện tại

## Mục tiêu
Stack hiện tại ưu tiên:
- chạy full local bằng Docker
- dễ demo
- dễ bàn giao
- không thêm thành phần hạ tầng ngoài phạm vi cần thiết

## Thành phần chính
### 1. Database
- PostgreSQL 16
- image: `pgvector/pgvector:pg16`

Lưu ý:
- retrieval experimental hiện chưa dùng `pgvector`
- image `pgvector` vẫn được giữ vì phù hợp nếu sau này nâng retrieval

### 2. Backend API
- Python 3.12
- FastAPI
- SQLAlchemy
- Alembic
- Uvicorn

Vai trò:
- phục vụ endpoint dữ liệu
- phục vụ `POST /chat/query`
- đọc/ghi PostgreSQL
- fallback nội bộ khi OpenAI không sẵn sàng

### 3. UI
- Streamlit

Vai trò:
- dashboard demo
- chat UI
- data browser
- source health

### 4. Scheduler
- Python script local:
  - `scripts/run_scheduler.py`

Vai trò:
- chạy source theo `fetch_interval_minutes`
- lưu trạng thái job
- health summary
- có thể gắn cleanup dry-run/apply

### 5. Seed demo
- service chạy một lần
- gọi:
  - `python scripts/seed_demo_data.py --demo-only`

Vai trò:
- reset dữ liệu nghiệp vụ
- nạp lại dữ liệu demo end-to-end

## Những gì không có trong stack hiện tại
- Redis
- Celery
- Airflow
- MinIO
- Nginx reverse proxy
- pgvector query runtime
- queue phân tán

Lý do:
- chưa cần cho local/demo
- ưu tiên stack gọn, dễ hiểu, dễ bàn giao

## Compose hiện dùng
### Bản local/dev
- `docker-compose.yml`

Đặc điểm:
- mount source code vào container
- phù hợp local debug

### Bản triển khai tham chiếu
- `06_deployment/docker-compose.yml`

Đặc điểm:
- build từ repo root
- không phụ thuộc local venv
- dùng cùng image logic với bản local/dev

## Chuẩn chạy khuyến nghị
1. `cp .env.production.example .env`
2. `docker compose up -d postgres api ui scheduler`
3. `docker compose --profile demo run --rm seed_demo`
4. kiểm tra `/health`
5. mở UI

## Hướng mở rộng sau này
- thêm reverse proxy
- tách scheduler riêng theo môi trường
- log tập trung
- cảnh báo khi source fail liên tục
- nâng retrieval từ sparse local lên vector search thật
