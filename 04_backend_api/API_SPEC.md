# API Spec đề xuất

## Nhóm health
- `GET /health`
- `GET /version`

## Nhóm tin tức
- `GET /api/news/hot?limit=10`
- `GET /api/news/search?q=...`
- `GET /api/news/{id}`
- `GET /api/news/cluster/{cluster_id}`

## Nhóm giá cả
- `GET /api/prices/latest?item=xang`
- `GET /api/prices/latest?item=vang`
- `GET /api/prices/compare?item=vang&period=1d`

## Nhóm thời tiết
- `GET /api/weather/latest?location=Ha%20Noi`
- `GET /api/weather/warnings`

## Nhóm chính sách
- `GET /api/policies/latest`
- `GET /api/policies/search?q=giao%20duc`

## Nhóm giao thông
- `GET /api/traffic/latest`
- `GET /api/traffic/search?location=Ha%20Noi`

## Nhóm AI chat
- `POST /api/chat/query`
