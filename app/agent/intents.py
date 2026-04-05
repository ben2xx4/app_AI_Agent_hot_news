from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

KNOWN_LOCATIONS = {
    "ha noi": "Hà Nội",
    "hanoi": "Hà Nội",
    "tp hcm": "TP.HCM",
    "tphcm": "TP.HCM",
    "ho chi minh": "TP.HCM",
    "da nang": "Đà Nẵng",
    "hai phong": "Hải Phòng",
    "can tho": "Cần Thơ",
    "nha trang": "Nha Trang",
}

UI_LABEL_PHRASES = {
    "hoi dap bang tieng viet",
    "nhap cau hoi",
}

GREETING_PATTERNS = [
    r"^(xin\s+)?chao\b",
    r"^chao\s+ban\b",
    r"^hello\b",
    r"^hi\b",
    r"^hey\b",
]

IDENTITY_PHRASES = {
    "ban la ai",
    "ban la gi",
    "tro ly la ai",
    "tro ly la gi",
    "gioi thieu ve ban",
}

CAPABILITY_PHRASES = {
    "ban giup duoc gi",
    "ban co the lam gi",
    "ban ho tro gi",
    "ban biet gi",
    "ban lam duoc gi",
}

THANKS_PHRASES = {
    "cam on",
    "cam on ban",
    "thank you",
    "thanks",
}

FAREWELL_PHRASES = {
    "tam biet",
    "hen gap lai",
    "bye",
    "bye bye",
}


PRICE_ITEM_MAP = {
    "xang": "gia-xang-ron95-iii",
    "vang": "gia-vang-sjc",
    "usd": "ty-gia-usd-ban-ra",
    "ty gia": "ty-gia-usd-ban-ra",
}


@dataclass(slots=True)
class IntentResult:
    intent: str
    query: str | None = None
    location: str | None = None
    item_name: str | None = None
    focus: str | None = None
    limit: int | None = None


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    stripped = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    stripped = re.sub(r"[^a-z0-9]+", " ", stripped)
    return re.sub(r"\s+", " ", stripped).strip()


def extract_location(question: str) -> str | None:
    folded = _fold(question)
    for key, value in KNOWN_LOCATIONS.items():
        if key in folded:
            return value
    return None


def extract_item_name(question: str) -> str | None:
    folded = _fold(question)
    for keyword, value in PRICE_ITEM_MAP.items():
        if keyword in folded:
            return value
    return None


TEXTUAL_LIMIT_MAP = {
    "mot": 1,
    "hai": 2,
    "ba": 3,
    "bon": 4,
    "tu": 4,
    "nam": 5,
    "sau": 6,
    "bay": 7,
    "tam": 8,
    "chin": 9,
    "muoi": 10,
}


def extract_limit(question: str) -> int | None:
    folded = _fold(question)
    digit_patterns = [
        r"\btop\s+(\d{1,2})\b",
        r"\b(\d{1,2})\s+(?:tin|bai|ban tin)\b",
        r"\b(\d{1,2})\s+tin hot\b",
        r"\blay\s+(\d{1,2})\b",
    ]
    for pattern in digit_patterns:
        match = re.search(pattern, folded)
        if not match:
            continue
        value = int(match.group(1))
        return max(1, min(value, 20))

    text_patterns = [
        r"\btop\s+(mot|hai|ba|bon|tu|nam|sau|bay|tam|chin|muoi)\b",
        r"\b(mot|hai|ba|bon|tu|nam|sau|bay|tam|chin|muoi)\s+tin hot\b",
    ]
    for pattern in text_patterns:
        match = re.search(pattern, folded)
        if not match:
            continue
        return TEXTUAL_LIMIT_MAP.get(match.group(1))
    return None


def extract_topic(question: str) -> str | None:
    folded = _fold(question)
    keywords = [
        "chinh tri",
        "giao duc",
        "y te",
        "tai chinh",
        "kinh te",
        "giao thong",
        "giai tri",
        "suc khoe",
    ]
    for keyword in keywords:
        if keyword in folded:
            return keyword
    match = re.search(
        r"\bve\s+([a-z0-9\s]+?)(?:\s+(?:dang duoc|duoc|khong|hom nay|la gi|nao)\b|$)",
        folded,
    )
    if match:
        topic = match.group(1).strip()
        if topic:
            return topic
    return None


def extract_freeform_weather_location(question: str) -> str | None:
    folded = _fold(question)
    patterns = [
        r"thoi tiet\s+([a-z0-9\s]+?)(?:\s+(?:hom nay|ngay mai|the nao|ra sao|co|la)\b|$)",
        r"^([a-z0-9\s]+?)\s+(?:hom nay|ngay mai)\s+co\s+(?:mua|nong|lanh|gio|bao)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, folded)
        if not match:
            continue
        candidate = re.sub(r"^(o|tai|khu vuc)\s+", "", match.group(1)).strip()
        if candidate:
            return " ".join(part.capitalize() for part in candidate.split())
    return None


def extract_traffic_focus(question: str) -> str | None:
    folded = _fold(question)
    if any(keyword in folded for keyword in ["cam duong", "bi cam", "cam xe", "phan luong"]):
        return "blocked_road"
    if any(keyword in folded for keyword in ["ket xe", "un tac", "dong xe"]):
        return "congestion"
    if any(keyword in folded for keyword in ["tai nan", "va cham", "truot nga"]):
        return "accident"
    return None


def is_hot_news_question(question: str) -> bool:
    folded = _fold(question)
    hot_news_keywords = [
        "tin hot",
        "tin nong",
        "bai hot",
        "tin moi",
        "moi nhat",
        "noi bat",
        "tin dang chu y",
        "su kien chinh",
    ]
    return any(keyword in folded for keyword in hot_news_keywords)


def looks_like_freeform_news_query(question: str) -> bool:
    folded = _fold(question)
    words = folded.split()
    if len(words) < 6:
        return False

    news_like_markers = [
        "la gi",
        "co gi",
        "the nao",
        "ra sao",
        "can luu y",
        "dieu gi",
        "vi sao",
    ]
    if any(marker in folded for marker in news_like_markers):
        return True

    return len(question.strip()) >= 45


def detect_smalltalk_kind(question: str) -> str | None:
    folded = _fold(question)
    if any(re.search(pattern, folded) for pattern in GREETING_PATTERNS):
        return "greeting"
    if folded in IDENTITY_PHRASES or "ban la ai" in folded or "ban la gi" in folded:
        return "identity"
    if folded in CAPABILITY_PHRASES or "giup duoc gi" in folded or "co the lam gi" in folded:
        return "capabilities"
    if folded in THANKS_PHRASES or folded.startswith("cam on"):
        return "thanks"
    if folded in FAREWELL_PHRASES or folded.startswith("tam biet"):
        return "farewell"
    return None


class IntentRouter:
    def detect(self, question: str) -> IntentResult:
        folded = _fold(question)
        if folded in UI_LABEL_PHRASES:
            return IntentResult(intent="unknown", query=question)
        smalltalk_kind = detect_smalltalk_kind(question)
        if smalltalk_kind:
            return IntentResult(intent="smalltalk", query=smalltalk_kind)

        location = extract_location(question)
        item_name = extract_item_name(question)
        limit = extract_limit(question)
        topic = extract_topic(question)
        freeform_weather_location = extract_freeform_weather_location(question)
        traffic_focus = extract_traffic_focus(question)

        if "so sanh nguon" in folded or "bao nao" in folded:
            return IntentResult(intent="source_compare", query=topic)
        if "chu de" in folded or "tom tat" in folded or "nhieu bao" in folded:
            return IntentResult(intent="topic_summary", query=topic)
        if is_hot_news_question(question):
            return IntentResult(
                intent="hot_news",
                query=topic,
                location=location,
                limit=limit,
            )
        if (
            "giao thong" in folded
            or "cam duong" in folded
            or "luong tuyen" in folded
            or "han che luu thong" in folded
            or "cam xe" in folded
            or "ket xe" in folded
            or "un tac" in folded
            or "tai nan" in folded
            or "va cham" in folded
            or "tuyen duong" in folded
            or ("duong" in folded and "bi cam" in folded)
        ):
            return IntentResult(
                intent="traffic_lookup",
                location=location,
                focus=traffic_focus,
            )
        if "chinh sach" in folded or "van ban" in folded or "thong bao" in folded:
            return IntentResult(intent="policy_lookup", query=topic or question)
        if "thoi tiet" in folded or "mua" in folded or "nong" in folded or "lanh" in folded:
            if "canh bao" in folded:
                return IntentResult(intent="weather_lookup", query="warning")
            return IntentResult(
                intent="weather_lookup",
                location=location or freeform_weather_location,
            )
        if item_name:
            if "tang" in folded or "giam" in folded or "so voi" in folded or "compare" in folded:
                return IntentResult(intent="price_compare", item_name=item_name)
            return IntentResult(intent="price_lookup", item_name=item_name)
        if topic:
            return IntentResult(intent="topic_summary", query=topic)
        if looks_like_freeform_news_query(question):
            return IntentResult(
                intent="hot_news",
                query=question,
                location=location,
                limit=limit,
            )
        return IntentResult(intent="unknown", query=question)
