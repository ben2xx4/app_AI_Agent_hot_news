# Service layer

## Mục tiêu
Tách AI Agent khỏi truy vấn DB trực tiếp.

## Các service chính
- NewsService
- PriceService
- WeatherService
- PolicyService
- TrafficService
- ChatService

## Các hàm tool-friendly nên có
- `get_hot_news(limit=10)`
- `search_news(keyword, from_time=None, to_time=None)`
- `get_latest_price(item_name)`
- `compare_price(item_name, period)`
- `get_weather(location)`
- `get_latest_policies(topic=None)`
- `get_traffic_updates(location=None)`
