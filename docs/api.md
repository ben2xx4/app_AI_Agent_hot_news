# API backend

## Nguyen tac
- Response JSON ro rang
- Co `updated_at` va `sources` neu phu hop
- Input duoc validation bang Pydantic
- Loi nghiep vu tra ve HTTP status hop ly

## Endpoint bat buoc
- `GET /health`
- `GET /news/hot`
- `GET /news/search`
- `GET /prices/latest`
- `GET /prices/compare`
- `GET /weather/latest`
- `GET /policies/search`
- `GET /traffic/latest`
- `POST /chat/query`

## Mot so tham so chinh
- `/news/hot?limit=5`
- `/news/search?q=giao+duc&limit=10`
- `/prices/latest?item_name=gia-vang-sjc`
- `/prices/compare?item_name=gia-vang-sjc`
- `/weather/latest?location=Ha%20Noi`
- `/policies/search?query=giao+duc`
- `/traffic/latest?location=TP.HCM`

## Swagger
Khi chay API, tai lieu OpenAPI co san tai:
- `/docs`
- `/openapi.json`
