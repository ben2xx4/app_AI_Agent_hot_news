from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.news_service import NewsService
from app.services.policy_service import PolicyService
from app.services.price_service import PriceService
from app.services.traffic_service import TrafficService
from app.services.weather_service import WeatherService


class ToolRegistry:
    def __init__(self, db: Session) -> None:
        self.news_service = NewsService(db)
        self.price_service = PriceService(db)
        self.weather_service = WeatherService(db)
        self.policy_service = PolicyService(db)
        self.traffic_service = TrafficService(db)

    def _nullable(self, schema: dict[str, Any]) -> dict[str, Any]:
        return {"anyOf": [schema, {"type": "null"}]}

    def _strict_schema(
        self, properties: dict[str, dict[str, Any]], required: list[str]
    ) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    def _get_limit(self, args: dict[str, Any], default: int = 5) -> int:
        value = args.get("limit")
        return default if value is None else int(value)

    def definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "name": "get_hot_news",
                "description": "Lay danh sach tin hot moi nhat.",
                "parameters": self._strict_schema(
                    properties={
                        "limit": self._nullable(
                            {"type": "integer", "minimum": 1, "maximum": 10}
                        )
                    },
                    required=["limit"],
                ),
                "strict": True,
            },
            {
                "type": "function",
                "name": "search_news",
                "description": "Tim bai viet theo chu de hoac tu khoa.",
                "parameters": self._strict_schema(
                    properties={
                        "query": {"type": "string"},
                        "limit": self._nullable(
                            {"type": "integer", "minimum": 1, "maximum": 10}
                        ),
                    },
                    required=["query", "limit"],
                ),
                "strict": True,
            },
            {
                "type": "function",
                "name": "get_latest_price",
                "description": "Lay gia moi nhat cho mat hang co cau truc.",
                "parameters": self._strict_schema(
                    properties={"item_name": {"type": "string"}},
                    required=["item_name"],
                ),
                "strict": True,
            },
            {
                "type": "function",
                "name": "compare_price",
                "description": "So sanh gia moi nhat voi lan truoc.",
                "parameters": self._strict_schema(
                    properties={"item_name": {"type": "string"}},
                    required=["item_name"],
                ),
                "strict": True,
            },
            {
                "type": "function",
                "name": "get_weather",
                "description": "Lay thoi tiet moi nhat theo dia diem.",
                "parameters": self._strict_schema(
                    properties={"location": {"type": "string"}},
                    required=["location"],
                ),
                "strict": True,
            },
            {
                "type": "function",
                "name": "search_policy",
                "description": "Tim chinh sach va van ban theo chu de.",
                "parameters": self._strict_schema(
                    properties={"query": {"type": "string"}},
                    required=["query"],
                ),
                "strict": True,
            },
            {
                "type": "function",
                "name": "get_traffic_updates",
                "description": "Lay cap nhat giao thong moi nhat theo khu vuc.",
                "parameters": self._strict_schema(
                    properties={"location": self._nullable({"type": "string"})},
                    required=["location"],
                ),
                "strict": True,
            },
        ]

    def call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "get_hot_news":
            return self.news_service.get_hot_news(limit=self._get_limit(args))
        if name == "search_news":
            return self.news_service.search_news(query=args["query"], limit=self._get_limit(args))
        if name == "get_latest_price":
            return self.price_service.get_latest_price(item_name=args["item_name"])
        if name == "compare_price":
            return self.price_service.compare_price(item_name=args["item_name"])
        if name == "get_weather":
            return self.weather_service.get_weather(location=args["location"]) or {}
        if name == "search_policy":
            return self.policy_service.search_policy(query=args["query"])
        if name == "get_traffic_updates":
            return self.traffic_service.get_traffic_updates(location=args.get("location"))
        raise ValueError(f"Tool khong ton tai: {name}")
