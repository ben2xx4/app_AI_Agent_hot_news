# Kich ban demo 5-10 phut

## Phan 1: Nap du lieu
```bash
alembic upgrade head
python3 scripts/seed_demo_data.py --demo-only
```

## Phan 2: Chay API
```bash
uvicorn app.main:app --reload
```

## Phan 3: Goi nhanh cac endpoint
```bash
curl http://localhost:8000/health
curl "http://localhost:8000/news/hot?limit=5"
curl "http://localhost:8000/prices/latest?item_name=gia-vang-sjc"
curl "http://localhost:8000/weather/latest?location=Ha%20Noi"
curl "http://localhost:8000/policies/search?query=giao+duc"
curl "http://localhost:8000/traffic/latest?location=TP.HCM"
```

## Phan 4: Demo AI Agent
```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Tin hot hom nay la gi?"}'

curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Gia vang hom nay tang hay giam?"}'

curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Ha Noi hom nay co mua khong?"}'
```

## Phan 5: Demo UI
```bash
streamlit run app/ui/streamlit_app.py
```
