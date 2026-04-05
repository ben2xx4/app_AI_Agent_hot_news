from __future__ import annotations


def test_api_endpoints(client) -> None:
    news_response = client.get("/news/hot", params={"limit": 3})
    assert news_response.status_code == 200
    first_title = news_response.json()["items"][0]["title"].lower()
    assert not any(
        phrase in first_title
        for phrase in ["hạt lanh", "claude monet", "gen z", "cánh rừng gỗ quý"]
    )
    assert any(
        phrase in first_title
        for phrase in ["hà nội", "tp.hcm", "giá vàng", "mưa dông", "luồng xe"]
    )

    search_response = client.get("/news/search", params={"q": "giao duc"})
    assert search_response.status_code == 200
    assert any("Giáo dục" in item["title"] for item in search_response.json()["items"])

    latest_price_response = client.get("/prices/latest", params={"item_name": "gia-vang-sjc"})
    assert latest_price_response.status_code == 200
    assert latest_price_response.json()["items"][0]["display_name"] == "Giá vàng SJC"

    compare_price_response = client.get("/prices/compare", params={"item_name": "gia-vang-sjc"})
    assert compare_price_response.status_code == 200
    assert compare_price_response.json()["display_name"] == "Giá vàng SJC"

    weather_response = client.get("/weather/latest", params={"location": "Ha Noi"})
    assert weather_response.status_code == 200
    assert weather_response.json()["location"] == "Hà Nội"

    weather_response_haiphong = client.get("/weather/latest", params={"location": "Hai Phong"})
    assert weather_response_haiphong.status_code == 200
    assert weather_response_haiphong.json()["location"] == "Hải Phòng"

    policy_response = client.get("/policies/search", params={"query": "giao duc"})
    assert policy_response.status_code == 200
    assert any(
        "giáo dục" in (item["field"] or "").lower() for item in policy_response.json()["items"]
    )

    traffic_response = client.get("/traffic/latest", params={"location": "Ha Noi"})
    assert traffic_response.status_code == 200
    assert traffic_response.json()["items"][0]["location"] == "Hà Nội"


def test_chat_endpoint(client) -> None:
    response = client.post("/chat/query", json={"question": "Tin hot hom nay la gi?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert body["tool_called"] in {"get_hot_news", "search_news"}
    assert body["items"]
