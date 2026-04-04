# Thiết kế tool calling

## Các tool đề xuất
- get_hot_news
- search_news
- get_latest_price
- compare_price
- get_weather
- get_latest_policies
- get_traffic_updates

## Ví dụ mapping intent
- hot_news -> get_hot_news
- price_lookup -> get_latest_price
- price_compare -> compare_price
- weather_lookup -> get_weather
- policy_lookup -> get_latest_policies
- traffic_lookup -> get_traffic_updates

## Mục tiêu
Model chỉ cần:
- hiểu ý định
- chọn tool
- format câu trả lời
