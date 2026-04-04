# Ban giao cuoi

## Thanh phan da hoan tat
- Backend FastAPI theo domain
- PostgreSQL schema + Alembic migration
- Raw storage local
- 5 pipeline ingestion doc lap
- Processing layer gom cleaner, dedup, normalizer, validator, chunking
- API truy van va chat
- AI agent tool-calling/fallback
- UI demo Streamlit
- Test unit, integration va script test nhanh
- Docker Compose va runbook local

## Cach chay de demo nhanh
1. `python3 -m pip install -e .[dev]`
2. `cp .env.example .env`
3. `docker compose up -d postgres`
4. `alembic upgrade head`
5. `python3 scripts/seed_demo_data.py --demo-only`
6. `uvicorn app.main:app --reload`
7. `streamlit run app/ui/streamlit_app.py`

## Gioi han hien tai
- Nhieu nguon HTML live moi o muc parser tong quat, chua toi uu rieng tung site.
- Retrieval nguu nghia hien tai uu tien keyword/chunk, embedding that se bat khi co OpenAI API.
- Scheduler hien tai la loop don gian, phu hop local/demo hon la production quy mo lon.

## Huong mo rong
- Them parser live chat che cho tung site nguon
- Dung pgvector/embedding that cho semantic search
- Them dashboard quan tri job, source va do tuoi du lieu
