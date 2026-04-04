# Database va storage

## Chon PostgreSQL
PostgreSQL la database chinh vi phu hop du lieu co cau truc, de mo rong them JSON va retrieval. SQLite chi duoc dung cho test/fallback.

## Bang chinh
- `sources`
- `crawl_jobs`
- `raw_documents`
- `articles`
- `article_clusters`
- `price_snapshots`
- `weather_snapshots`
- `policy_documents`
- `traffic_events`
- `document_embeddings`

## Mo rong nho so voi schema goc
- Them `pipeline_name` vao `sources` de truy van va dat lich theo pipeline de hon.
- Them `fetch_metadata` vao `raw_documents` de luu thong tin fetch.
- Them `url`/`updated_at` va mot so chi so de phuc vu API va quan tri.

## Migration
Migration dau tien nam trong `alembic/versions/0001_initial_schema.py`.

Lenh chay:
```bash
alembic upgrade head
```

## Raw storage
- Duong dan mac dinh: `data/raw`
- Cau truc:
```text
data/raw/{pipeline}/{source}/{YYYY}/{MM}/{DD}/{timestamp}_{hash}.txt
```
- Moi raw document co metadata JSON di kem trong bang `raw_documents`

## Seed data
```bash
python3 scripts/seed_demo_data.py --demo-only
```

Script seed se:
- dong bo danh sach source tu `config/sources.yml`
- chay ca 5 pipeline tren fixture
- tao du lieu du de API va chat demo tra loi
