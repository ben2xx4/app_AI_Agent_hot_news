# Pseudocode chat flow

```python
def answer_question(question: str):
    intent = detect_intent(question)

    if intent == "hot_news":
        data = get_hot_news(limit=5)
    elif intent == "price_lookup":
        item = extract_item(question)
        data = get_latest_price(item)
    elif intent == "weather_lookup":
        location = extract_location(question)
        data = get_weather(location)
    elif intent == "policy_lookup":
        topic = extract_topic(question)
        data = get_latest_policies(topic=topic)
    elif intent == "traffic_lookup":
        location = extract_location(question)
        data = get_traffic_updates(location=location)
    else:
        data = {"message": "Chưa xác định được intent"}

    return format_answer(question, data)
```
