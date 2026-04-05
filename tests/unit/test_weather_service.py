from __future__ import annotations

from app.services.weather_service import WeatherService


def test_weather_service_lists_expanded_demo_locations(seeded_db) -> None:
    with seeded_db() as db:
        locations = WeatherService(db).list_available_locations()

    assert "Hà Nội" in locations
    assert "Hải Phòng" in locations
    assert "Cần Thơ" in locations
    assert "Nha Trang" in locations


def test_weather_service_can_lookup_new_city_from_demo_data(seeded_db) -> None:
    with seeded_db() as db:
        payload = WeatherService(db).get_weather("Cần Thơ")

    assert payload is not None
    assert payload["location"] == "Cần Thơ"
    assert payload["weather_text"]
