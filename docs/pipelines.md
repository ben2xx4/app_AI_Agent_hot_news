# Thiet ke 5 pipeline

## Quy uoc chung
- Nguon du lieu cau hinh trong `config/sources.yml`
- Moi pipeline deu co:
  - `fetch`
  - `parse`
  - `normalize`
  - `store`
  - `tests`
- Raw payload luon duoc ghi truoc khi parse vao `data/raw`
- Moi lan chay sinh `crawl_jobs`

## Pipeline tin tuc
- Dau vao: RSS va HTML chi tiet neu co
- Dau ra: `articles`, `article_clusters`, `document_embeddings`
- Xu ly:
  - Parse RSS item
  - Lay title, summary, published_at, source, category, url
  - Exact dedup bang canonical URL/hash
  - Near dedup bang title similarity + thoi gian gan nhau
  - Tao cluster key don gian theo token tieu de
- Nguon live dang dung:
  - `tuoitre_rss_thoi_su`: RSS + fetch HTML detail de lay summary, noi dung, tac gia, ngay dang

## Pipeline gia ca
- Dau vao: JSON/HTML bang gia
- Dau ra: `price_snapshots`
- Xu ly:
  - Chuan hoa `item_type`, `item_name`, `buy_price`, `sell_price`, `unit`, `region`, `effective_at`
  - Snapshot hoa theo timestamp
  - So sanh voi ban ghi gan nhat truoc do qua service
- Nguon live dang dung:
  - `vietcombank_fx_rates_live`: XML ty gia Vietcombank, co `query_params` trong `config/sources.yml`

## Pipeline thoi tiet
- Dau vao: JSON/HTML theo dia phuong
- Dau ra: `weather_snapshots`
- Xu ly:
  - Chuan hoa location, forecast_time, nhiet do, do am, gio, mo ta, canh bao
  - Truy van latest theo dia phuong
- Nguon live dang dung:
  - `open_meteo_weather_hanoi_live`: Open-Meteo, lay current + daily de tao snapshot thoi tiet

## Pipeline chinh sach
- Dau vao: RSS/HTML/JSON thong bao va van ban
- Dau ra: `policy_documents`, `document_embeddings`
- Xu ly:
  - Trich metadata bat buoc
  - Clean noi dung
  - Chia chunk van ban de phuc vu retrieval
- Nguon live dang dung:
  - `congbao_policy_updates_live`: parse listing HTML va detail HTML tu Cong bao Chinh phu
  - Hien tai uu tien metadata + trich yeu; chua OCR/PDF text full

## Pipeline giao thong
- Dau vao: RSS/HTML/JSON su kien giao thong
- Dau ra: `traffic_events`
- Xu ly:
  - Chuan hoa loai su kien, khu vuc, thoi gian, mo ta
  - Ho tro loc theo thanh pho/khu vuc
- Nguon live dang dung:
  - `vov_giaothong_traffic_live`: parse danh sach bai viet va detail HTML tu VOV Giao thong

## Cach chay
```bash
python3 scripts/run_pipeline.py --pipeline all --demo-only
python3 scripts/run_scheduler.py --demo-only
```

Chay va verify rieng tung nguon live:
```bash
.venv/bin/python scripts/run_pipeline.py --pipeline news --source tuoitre_rss_thoi_su
.venv/bin/python scripts/run_pipeline.py --pipeline price --source vietcombank_fx_rates_live
.venv/bin/python scripts/run_pipeline.py --pipeline weather --source open_meteo_weather_hanoi_live
.venv/bin/python scripts/run_pipeline.py --pipeline policy --source congbao_policy_updates_live
.venv/bin/python scripts/run_pipeline.py --pipeline traffic --source vov_giaothong_traffic_live
```

Smoke test parser live:
```bash
.venv/bin/pytest -q tests/unit/test_live_parsers.py
```

Scheduler local:
```bash
.venv/bin/python scripts/run_scheduler.py --demo-only --run-once
.venv/bin/python scripts/run_scheduler.py --show-status
.venv/bin/python scripts/run_scheduler.py --pipeline news --source vnexpress_rss_tin_moi --run-once
```

Trang thai scheduler duoc ghi vao:
```text
data/processed/scheduler_status.json
```

## TODO mo rong
- Them geocoding khu vuc giao thong
- Them embedding that va semantic search cho tong hop chu de
- Nang cap parser policy de doc PDF/toan van khi can
