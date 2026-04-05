from __future__ import annotations

from sqlalchemy.orm import Session

from app.agent.intents import IntentResult, IntentRouter
from app.core.text import display_field
from app.services.news_service import NewsService
from app.services.policy_service import PolicyService
from app.services.price_service import PriceService
from app.services.traffic_service import TrafficService
from app.services.weather_service import WeatherService


class FallbackAgent:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.router = IntentRouter()
        self.news_service = NewsService(db)
        self.price_service = PriceService(db)
        self.weather_service = WeatherService(db)
        self.policy_service = PolicyService(db)
        self.traffic_service = TrafficService(db)

    def answer(self, question: str) -> dict:
        intent = self.router.detect(question)
        tool_name, payload = self._dispatch(intent)
        answer = self._format_answer(intent, payload)
        sources = payload.get("sources", [])
        if not sources:
            sources = self._extract_sources(payload)
        return {
            "question": question,
            "intent": intent.intent,
            "tool_called": tool_name,
            "answer": answer,
            "sources": sources,
            "updated_at": payload.get("updated_at"),
            "data": payload,
        }

    def _dispatch(self, intent: IntentResult) -> tuple[str, dict]:
        if intent.intent == "smalltalk":
            return (
                "smalltalk",
                {
                    "kind": intent.query,
                    "suggestions": [
                        "Tin hot hôm nay là gì?",
                        "Giá vàng SJC hôm nay bao nhiêu?",
                        "Có cảnh báo thời tiết nào không?",
                        "Có chính sách mới nào về giáo dục không?",
                    ],
                },
            )
        if intent.intent == "unknown":
            return (
                "none",
                {
                    "message": "Câu hỏi chưa đủ rõ để chọn đúng nhóm dữ liệu.",
                    "suggestions": [
                        "Tin hot hôm nay là gì?",
                        "Tỷ giá USD hôm nay là bao nhiêu?",
                        "Hà Nội hôm nay có mưa không?",
                        "Có chính sách mới nào về giáo dục không?",
                        "Có tin giao thông nào đáng chú ý không?",
                    ],
                },
            )
        if intent.intent == "hot_news":
            return "get_hot_news", self.news_service.get_hot_news(
                limit=intent.limit or 5,
                location=intent.location,
                query=intent.query,
            )
        if intent.intent == "price_lookup":
            return "get_latest_price", self.price_service.get_latest_price(
                item_name=intent.item_name
            )
        if intent.intent == "price_compare":
            return "compare_price", self.price_service.compare_price(
                item_name=intent.item_name or "gia-vang-sjc"
            )
        if intent.intent == "weather_lookup":
            if intent.query == "warning":
                return "get_weather", self.weather_service.get_warning_summary()
            requested_location = intent.location or "Hà Nội"
            payload = self.weather_service.get_weather(location=requested_location)
            if payload:
                payload["requested_location"] = requested_location
                return "get_weather", payload
            return (
                "get_weather",
                {
                    "found": False,
                    "requested_location": requested_location,
                    "available_locations": self.weather_service.list_available_locations(),
                },
            )
        if intent.intent == "policy_lookup":
            return "search_policy", self.policy_service.search_policy(
                query=intent.query or "giao duc"
            )
        if intent.intent == "traffic_lookup":
            return "get_traffic_updates", self.traffic_service.get_traffic_updates(
                location=intent.location,
                focus=intent.focus,
            )
        if intent.intent == "source_compare":
            return "search_news", self.news_service.compare_sources(query=intent.query or "tin hot")
        return "search_news", self.news_service.summarize_topic(query=intent.query)

    def _format_answer(self, intent: IntentResult, payload: dict) -> str:
        if intent.intent == "smalltalk":
            kind = payload.get("kind")
            if kind == "greeting":
                return (
                    "Chào bạn. Tôi là trợ lý hỏi đáp thông tin trong ngày. "
                    "Bạn có thể hỏi về tin hot, giá cả, thời tiết, chính sách hoặc giao thông."
                )
            if kind == "identity":
                return (
                    "Tôi là trợ lý AI của nền tảng dữ liệu tin tức và thông tin hằng ngày. "
                    "Tôi dùng dữ liệu local của hệ thống để trả lời bằng tiếng Việt."
                )
            if kind == "capabilities":
                return self._format_bulleted_section(
                    "Tôi có thể hỗ trợ:",
                    payload.get("suggestions", []),
                )
            if kind == "thanks":
                return "Không có gì. Nếu cần, bạn cứ hỏi tiếp."
            if kind == "farewell":
                return "Chào bạn. Khi cần tra cứu thông tin trong ngày, bạn cứ quay lại."
            return "Mình đang sẵn sàng hỗ trợ bạn."
        if intent.intent == "unknown":
            suggestions = payload.get("suggestions", [])
            if suggestions:
                return self._format_bulleted_section(
                    "Chưa hiểu rõ câu hỏi. Bạn có thể thử:",
                    suggestions,
                )
            return "Chưa hiểu rõ câu hỏi. Bạn hãy hỏi cụ thể hơn."
        if intent.intent == "hot_news":
            titles = [item["title"] for item in payload.get("items", [])]
            requested_topic = display_field(payload.get("requested_query")) or payload.get(
                "requested_query"
            )
            is_freeform_query = bool(
                requested_topic and len(str(requested_topic).split()) >= 6
            )
            if not titles:
                location_text = (
                    f" tại {payload.get('requested_location')}"
                    if payload.get("requested_location")
                    else ""
                )
                topic_text = (
                    " liên quan đến câu hỏi của bạn"
                    if is_freeform_query
                    else f" về {requested_topic}"
                    if requested_topic
                    else ""
                )
                return self._format_guided_empty_state(
                    f"Hiện chưa có dữ liệu tin{topic_text}{location_text}.",
                    [
                        "Thử hỏi: Có gì mới về tài chính hôm nay?",
                        "Thử hỏi: Báo nào đang nói nhiều về giáo dục?",
                    ],
                )
            heading = "Tin hot gần nhất:"
            if is_freeform_query and payload.get("requested_location"):
                heading = f"Tin liên quan tại {payload['requested_location']}:"
            elif is_freeform_query:
                heading = "Tin liên quan đến câu hỏi của bạn:"
            elif requested_topic and payload.get("requested_location"):
                heading = (
                    f"Tin hot về {requested_topic} tại "
                    f"{payload['requested_location']}:"
                )
            elif requested_topic:
                heading = f"Tin hot về {requested_topic}:"
            elif payload.get("requested_location"):
                heading = f"Tin hot tại {payload['requested_location']}:"
            return self._format_bulleted_section(heading, titles)
        if intent.intent == "price_lookup":
            items = payload.get("items", [])
            if not items:
                return "Hiện chưa có dữ liệu giá mới nhất."
            item = items[0]
            value = item.get("display_value") or item.get("sell_price") or item.get("buy_price")
            return (
                f"{item.get('display_name') or item['item_name']} hiện có mức giá "
                f"{value}"
            ).strip()
        if intent.intent == "price_compare":
            current = payload.get("current")
            if not current:
                return "Hiện chưa đủ dữ liệu để so sánh giá."
            display_name = payload.get("display_name") or payload["item_name"]
            value = (
                current.get("display_value")
                or current.get("sell_price")
                or current.get("buy_price")
            )
            delta = payload.get("delta")
            if delta is None:
                return f"{display_name} hiện ở mức {value}, chưa có bản ghi trước để so sánh."
            return (
                f"{display_name} hiện ở mức {value}, "
                f"xu hướng {payload['trend']} {payload.get('display_delta') or abs(delta)}."
            )
        if intent.intent == "weather_lookup":
            if payload.get("warning_query"):
                warning_items = payload.get("items", [])
                if not warning_items:
                    available_locations = payload.get("available_locations", [])
                    if available_locations:
                        return (
                            "Hiện chưa có cảnh báo thời tiết nổi bật. "
                            f"Các địa điểm đang theo dõi: {', '.join(available_locations)}."
                        )
                    return "Hiện chưa có cảnh báo thời tiết nổi bật."
                return self._format_bulleted_section(
                    "Cảnh báo thời tiết:",
                    [
                        f"{item['location']}: {item['warning_text']}"
                        for item in warning_items[:5]
                    ],
                )
            if payload.get("found") is False:
                available_locations = payload.get("available_locations", [])
                if available_locations:
                    return (
                        f"Hiện chưa có dữ liệu thời tiết cho {payload.get('requested_location')}. "
                        f"Các địa điểm hiện có: {', '.join(available_locations)}."
                    )
                return (
                    f"Hiện chưa có dữ liệu thời tiết cho {payload.get('requested_location')}."
                )
            return (
                f"{payload['location']} có trạng thái '{payload.get('weather_text')}', "
                f"nhiệt độ {payload.get('min_temp')}-{payload.get('max_temp')} độ C."
            )
        if intent.intent == "policy_lookup":
            titles = [item["title"] for item in payload.get("items", [])[:3]]
            if not titles:
                return self._format_guided_empty_state(
                    "Hiện chưa có văn bản phù hợp.",
                    [
                        "Thử hỏi: Có chính sách mới nào về giáo dục không?",
                        "Thử hỏi: Có thông báo mới nào từ Bộ Y tế không?",
                    ],
                )
            return self._format_bulleted_section("Văn bản liên quan:", titles)
        if intent.intent == "traffic_lookup":
            titles = [item["title"] for item in payload.get("items", [])[:3]]
            if not titles:
                empty_message = {
                    "blocked_road": "Hiện chưa có cập nhật cấm đường đáng chú ý.",
                    "congestion": "Hiện chưa có cập nhật ùn tắc đáng chú ý.",
                    "accident": "Hiện chưa có cập nhật tai nạn đáng chú ý.",
                }.get(intent.focus, "Hiện chưa có cập nhật giao thông đáng chú ý.")
                return self._format_guided_empty_state(
                    empty_message,
                    [
                        "Thử hỏi: Có tin giao thông nào đáng chú ý hôm nay không?",
                        "Thử hỏi: Có tuyến đường nào đang bị cấm không?",
                    ],
                )
            return self._format_bulleted_section(
                {
                    "blocked_road": "Cập nhật cấm đường:",
                    "congestion": "Cập nhật ùn tắc:",
                    "accident": "Cập nhật tai nạn:",
                }.get(intent.focus, "Cập nhật giao thông:"),
                titles,
            )
        if intent.intent == "source_compare":
            comparisons = payload.get("comparisons", [])
            if not comparisons:
                query = payload.get("query") or "chủ đề này"
                return f"Chưa có dữ liệu để so sánh nguồn cho {query}."
            lines = [f"{item['source']}: {item['count']} bai" for item in comparisons]
            return self._format_bulleted_section("So sánh nguồn:", lines)
        lines = payload.get("summary_lines", [])
        if not lines:
            topic = payload.get("topic") or "chủ đề này"
            return self._format_guided_empty_state(
                f"Chưa có dữ liệu tổng hợp cho {topic}.",
                [
                    "Thử hỏi: Tin hot hôm nay là gì?",
                    "Thử hỏi: Báo nào đang nói nhiều về giáo dục?",
                ],
            )
        return self._format_bulleted_section("Tóm tắt nhanh:", lines[:5])

    def _format_bulleted_section(self, title: str, lines: list[str]) -> str:
        cleaned_lines = [line.strip() for line in lines if line and line.strip()]
        if not cleaned_lines:
            return title
        return "\n".join([title, *[f"- {line}" for line in cleaned_lines]])

    def _format_guided_empty_state(self, title: str, suggestions: list[str]) -> str:
        return self._format_bulleted_section(title, suggestions)

    def _extract_sources(self, payload: dict) -> list[str]:
        if "items" in payload:
            return sorted({item.get("source") for item in payload["items"] if item.get("source")})
        if "comparisons" in payload:
            return sorted(
                {item.get("source") for item in payload["comparisons"] if item.get("source")}
            )
        current = payload.get("current")
        if current and current.get("source"):
            return [current["source"]]
        if payload.get("source"):
            return [payload["source"]]
        return []
