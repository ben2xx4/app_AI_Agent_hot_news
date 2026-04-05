from __future__ import annotations

from collections import Counter
from datetime import datetime
from html import escape
from textwrap import dedent
from urllib.parse import urlparse

import httpx
import pandas as pd
import streamlit as st

from app.core.content_items import (
    build_content_item,
    build_content_item_from_dataset_record,
    shorten_preview_text,
)
from app.core.settings import get_settings
from app.ui.chat_state import (
    append_chat_message,
    build_chat_meta,
    build_chat_request,
    build_default_chat_messages,
    ensure_pending_user_visible,
    extract_recent_user_questions,
    reset_chat_messages,
)
from app.ui.data_browser import (
    list_dataset_definitions,
    load_core_dataset_overview,
    load_dataset_preview,
)
from app.ui.experience import (
    CHAT_SUGGESTION_GROUPS,
    QUICK_START_ACTIONS,
    build_sparse_data_notice,
    flatten_chat_suggestions,
    get_follow_up_suggestions,
)
from app.ui.flow import (
    build_browser_prefill,
    build_browser_prefill_from_item,
    build_detail_state,
    get_latest_clickable_item,
)
from app.ui.navigation import (
    NAVIGATION_ITEMS,
    build_navigation_state,
    navigation_key_from_label,
    navigation_label_from_key,
    navigation_labels,
)
from app.ui.presentation import (
    build_dataset_overview_chart_frame,
    build_news_board_model,
    build_news_source_chart_frame,
    build_weather_chart_frame,
    format_ui_source_label,
)
from app.ui.runtime import should_load_dashboard_payloads, summarize_sidebar_runtime
from app.ui.source_health import load_scheduler_health_snapshot

settings = get_settings()
API_BASE_URL = settings.api_base_url
PRICE_HIGHLIGHT_ORDER = [
    "gia-vang-sjc",
    "gia-vang-nhan-9999",
    "ty-gia-usd-ban-ra",
    "gia-xang-ron95-iii",
]
WEATHER_LOCATIONS = ["Hà Nội", "TP.HCM", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Nha Trang"]
BROWSER_FILTER_FIELDS = ("pipeline_name", "source_name", "location", "item_name")
BUSINESS_DATASET_DEFAULT = "Tin tức"
TECHNICAL_DATASET_DEFAULT = "Nguồn dữ liệu"
CHAT_AVATAR_DATA = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "viewBox='0 0 120 120'%3E"
    "%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E"
    "%3Cstop stop-color='%23f7d9b1'/%3E"
    "%3Cstop offset='1' stop-color='%23ef7d3d'/%3E"
    "%3C/linearGradient%3E%3C/defs%3E"
    "%3Crect width='120' height='120' rx='60' fill='url(%23g)'/%3E"
    "%3Ccircle cx='60' cy='46' r='21' fill='%23fff6ea'/%3E"
    "%3Cpath d='M27 98c6-19 19-30 33-30s27 11 33 30' fill='%23fff6ea'/%3E"
    "%3Cpath d='M31 56c0-19 12-34 29-34 18 0 29 15 29 34' fill='none' "
    "stroke='%231e6a73' stroke-width='10' stroke-linecap='round'/%3E"
    "%3Crect x='18' y='56' width='14' height='24' rx='7' fill='%231e6a73'/%3E"
    "%3Crect x='88' y='56' width='14' height='24' rx='7' fill='%231e6a73'/%3E"
    "%3Ccircle cx='52' cy='46' r='3.2' fill='%231e6a73'/%3E"
    "%3Ccircle cx='68' cy='46' r='3.2' fill='%231e6a73'/%3E"
    "%3Cpath d='M52 58c4 4 12 4 16 0' fill='none' stroke='%231e6a73' "
    "stroke-width='4' stroke-linecap='round'/%3E"
    "%3Cpath d='M92 26h-7a6 6 0 0 0-6 6v5c0 3 3 6 6 6h2l6 6v-6h-1"
    " a6 6 0 0 0 6-6v-5c0-3-3-6-6-6Z' fill='%23fff6ea'/%3E"
    "%3C/svg%3E"
)
CHAT_HISTORY_LIMIT = 10


@st.cache_data(ttl=15, show_spinner=False)
def get_json(path: str, params: dict | None = None) -> dict:
    response = httpx.get(f"{API_BASE_URL}{path}", params=params, timeout=20.0)
    response.raise_for_status()
    return response.json()


def post_json(path: str, payload: dict) -> dict:
    response = httpx.post(f"{API_BASE_URL}{path}", json=payload, timeout=30.0)
    response.raise_for_status()
    return response.json()


def fetch_payload(path: str, params: dict | None = None) -> tuple[dict | None, str | None]:
    try:
        return get_json(path, params=params), None
    except Exception as exc:
        return None, str(exc)


def build_empty_weather_payloads() -> list[tuple[str, dict | None, str | None]]:
    return [(location, None, None) for location in WEATHER_LOCATIONS]


def fetch_weather_payloads() -> list[tuple[str, dict | None, str | None]]:
    return [
        (location, *fetch_payload("/weather/latest", params={"location": location}))
        for location in WEATHER_LOCATIONS
    ]


def format_datetime(value: str | None) -> str:
    if not value:
        return "Chưa có thời điểm"
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).strftime("%H:%M %d/%m/%Y")
    except ValueError:
        return value


def format_database_driver_label(driver: str | None) -> str:
    if not driver:
        return "Không rõ"
    lowered = driver.lower()
    if "postgresql" in lowered:
        return "PostgreSQL"
    if "sqlite" in lowered:
        return "SQLite"
    return driver


def format_database_target(database_url: str | None) -> str:
    if not database_url:
        return "Chưa có thông tin kết nối"
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "", 1)
    parsed = urlparse(database_url)
    host = parsed.hostname or "localhost"
    port = f":{parsed.port}" if parsed.port else ""
    db_name = parsed.path.lstrip("/") or "default"
    return f"{host}{port} / {db_name}"


def format_api_base_label(api_base_url: str) -> str:
    parsed = urlparse(api_base_url)
    if not parsed.scheme:
        return api_base_url
    host = parsed.hostname or api_base_url
    port = f":{parsed.port}" if parsed.port else ""
    return f"{host}{port}"


def display_health_state_label(value: str) -> str:
    return {
        "healthy": "Ổn định",
        "due": "Đến lịch chạy",
        "pending": "Chưa có snapshot",
        "failing": "Đang lỗi",
        "running": "Đang chạy",
    }.get(value, value)


def format_record_count(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def dataset_count_map(dataset_overview: list[dict] | None) -> dict[str, int]:
    if not dataset_overview:
        return {}
    return {
        item["key"]: int(item.get("total_rows", 0))
        for item in dataset_overview
    }


def browser_state_key(name: str, *, technical_scope: bool) -> str:
    scope_label = "technical" if technical_scope else "business"
    return f"browser_{scope_label}_{name}"


def render_html_block(html: str) -> None:
    normalized_html = dedent(html).strip()
    html_renderer = getattr(st, "html", None)
    if html_renderer is not None:
        html_renderer(normalized_html, width="stretch")
        return
    st.markdown(normalized_html, unsafe_allow_html=True)


def render_styles() -> None:
    styles = """
        <style>
        :root {
            --bg: #efe5d4;
            --ink: #201a15;
            --muted: #6d6358;
            --paper: rgba(255, 250, 244, 0.86);
            --line: rgba(94, 72, 48, 0.16);
            --accent: #bb4f1d;
            --accent-soft: #f2d0b3;
            --support: #175f68;
            --support-soft: #d6eced;
            --deep: #18323b;
            --shadow: 0 22px 64px rgba(60, 39, 23, 0.12);
            --radius-lg: 28px;
            --radius-md: 20px;
            --chat-avatar: url("__CHAT_AVATAR_DATA__");
        }

        html, body, [class*="css"] {
            font-family: "Avenir Next", "IBM Plex Sans", "Segoe UI", "Helvetica Neue", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(242, 208, 179, 0.92), transparent 30%),
                radial-gradient(circle at top right, rgba(214, 236, 237, 0.96), transparent 28%),
                linear-gradient(180deg, #fcf7f0 0%, #efe5d4 100%);
            color: var(--ink);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stAppViewContainer"] > .main {
            padding-top: 1.15rem;
        }

        .hero-shell {
            padding: 1.9rem 2rem;
            border: 1px solid var(--line);
            border-radius: 34px;
            background:
                linear-gradient(135deg, rgba(255, 250, 242, 0.96), rgba(249, 238, 222, 0.82)),
                linear-gradient(120deg, rgba(198, 90, 30, 0.08), rgba(30, 106, 115, 0.10));
            box-shadow: var(--shadow);
            overflow: hidden;
        }

        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.42rem 0.8rem;
            border-radius: 999px;
            background: rgba(30, 106, 115, 0.10);
            color: var(--support);
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }

        .hero-title {
            margin: 0.9rem 0 0.7rem;
            font-size: clamp(2rem, 4vw, 3.4rem);
            line-height: 1.05;
            letter-spacing: -0.04em;
        }

        .hero-copy {
            max-width: 48rem;
            margin: 0;
            color: var(--muted);
            font-size: 1.04rem;
            line-height: 1.7;
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-top: 1.25rem;
        }

        .page-shell {
            padding: 1.25rem 1.35rem;
            border-radius: 30px;
            background: rgba(255, 251, 246, 0.82);
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
        }

        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1.5rem;
            margin-bottom: 0.8rem;
        }

        .page-title {
            margin: 0.3rem 0 0.35rem;
            font-size: clamp(1.55rem, 2vw, 2.1rem);
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .page-copy {
            margin: 0;
            max-width: 48rem;
            color: var(--muted);
            line-height: 1.65;
        }

        .page-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            justify-content: flex-end;
        }

        .sidebar-shell {
            padding: 1rem 1rem 1.05rem;
            border-radius: 24px;
            background: linear-gradient(
                180deg,
                rgba(255, 251, 246, 0.98),
                rgba(245, 236, 223, 0.92)
            );
            border: 1px solid rgba(94, 72, 48, 0.14);
            box-shadow: 0 14px 36px rgba(60, 39, 23, 0.08);
            margin-bottom: 1rem;
        }

        .sidebar-title {
            margin: 0.25rem 0 0.3rem;
            font-size: 1rem;
            font-weight: 800;
        }

        .sidebar-copy {
            margin: 0;
            color: var(--muted);
            line-height: 1.55;
            font-size: 0.92rem;
        }

        .status-chip {
            padding: 0.62rem 0.92rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.75);
            border: 1px solid var(--line);
            font-size: 0.9rem;
            color: var(--ink);
        }

        .status-chip strong {
            color: var(--accent);
            font-weight: 800;
        }

        .section-heading {
            margin: 0.35rem 0 0.85rem;
            font-size: 1.2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }

        .card-surface {
            border-radius: var(--radius-lg);
            background: var(--paper);
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
            padding: 1.2rem 1.25rem;
            backdrop-filter: blur(12px);
        }

        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 999px;
            border: 1px solid rgba(32, 26, 21, 0.08);
            background:
                linear-gradient(
                    135deg,
                    rgba(255, 252, 248, 0.98),
                    rgba(244, 233, 220, 0.96)
                );
            color: var(--ink);
            box-shadow: 0 10px 30px rgba(60, 39, 23, 0.08);
            font-weight: 700;
            transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
        }

        div.stButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: rgba(187, 79, 29, 0.22);
            box-shadow: 0 14px 34px rgba(60, 39, 23, 0.12);
            transform: translateY(-1px);
            color: var(--accent);
        }

        div[data-testid="stChatMessage"] {
            padding: 0.9rem 1rem;
            border-radius: 24px;
            border: 1px solid rgba(94, 72, 48, 0.14);
            box-shadow: 0 14px 32px rgba(60, 39, 23, 0.08);
            margin-bottom: 0.8rem;
        }

        div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
            background:
                linear-gradient(
                    180deg,
                    rgba(255, 251, 246, 0.98),
                    rgba(244, 234, 219, 0.9)
                );
        }

        div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
            background: linear-gradient(135deg, rgba(29, 99, 108, 0.96), rgba(24, 50, 59, 0.98));
            border-color: rgba(23, 95, 104, 0.28);
        }

        div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
            color: var(--ink);
        }

        div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
        [data-testid="stChatMessageContent"] {
            color: #fff8ef;
        }

        div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p:last-child {
            margin-bottom: 0;
        }

        .chat-role-label {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.22rem 0.58rem;
            border-radius: 999px;
            background: rgba(23, 95, 104, 0.1);
            color: var(--support);
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.45rem;
        }

        .chat-role-label.user {
            background: rgba(255, 248, 239, 0.18);
            color: #fff4e6;
        }

        .feature-card {
            padding: 1.2rem 1.25rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.72);
            box-shadow: 0 16px 40px rgba(73, 48, 24, 0.08);
            margin-bottom: 0.95rem;
        }

        .feature-card a {
            color: var(--ink);
            text-decoration: none;
        }

        .feature-card a:hover {
            color: var(--accent);
        }

        .feature-title {
            margin: 0 0 0.5rem;
            font-size: 1.08rem;
            line-height: 1.35;
            font-weight: 800;
            letter-spacing: -0.02em;
            overflow-wrap: anywhere;
        }

        .feature-summary {
            margin: 0 0 0.8rem;
            color: var(--muted);
            font-size: 0.95rem;
            line-height: 1.6;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .meta-line {
            color: var(--muted);
            font-size: 0.84rem;
        }

        .stat-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem;
        }

        .stat-card {
            padding: 1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid var(--line);
        }

        .stat-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--muted);
            margin-bottom: 0.35rem;
        }

        .stat-value {
            font-size: 1.2rem;
            font-weight: 800;
            color: var(--ink);
        }

        .mini-card {
            padding: 1rem 1.05rem;
            border-radius: 18px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.78);
            min-height: 154px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 0.6rem;
            min-width: 0;
        }

        .mini-kicker {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--support);
            font-weight: 800;
            display: block;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .mini-title {
            margin-top: 0.55rem;
            font-size: 1rem;
            font-weight: 800;
            line-height: 1.35;
            overflow-wrap: anywhere;
        }

        .mini-value {
            font-size: 1.45rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin: 0.35rem 0;
        }

        .mini-copy {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .inline-note {
            margin-top: 0.85rem;
            padding: 0.85rem 1rem;
            border-radius: 18px;
            background: rgba(198, 90, 30, 0.08);
            border: 1px dashed rgba(198, 90, 30, 0.28);
            color: var(--ink);
        }

        .system-shell {
            padding: 1.2rem 1.25rem;
            border-radius: 28px;
            background:
                linear-gradient(180deg, rgba(255, 252, 247, 0.98), rgba(246, 236, 221, 0.9));
            border: 1px solid rgba(102, 84, 62, 0.18);
            box-shadow: var(--shadow);
        }

        .system-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 1rem;
        }

        .system-card {
            padding: 1rem;
            border-radius: 20px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.82);
        }

        .system-card.system-good {
            background: linear-gradient(
                180deg,
                rgba(217, 237, 240, 0.68),
                rgba(255, 255, 255, 0.96)
            );
            border-color: rgba(30, 106, 115, 0.18);
        }

        .system-card.system-warm {
            background: linear-gradient(
                180deg,
                rgba(243, 215, 191, 0.74),
                rgba(255, 255, 255, 0.96)
            );
            border-color: rgba(198, 90, 30, 0.18);
        }

        .system-card.system-neutral {
            background: rgba(255, 255, 255, 0.88);
        }

        .system-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin-bottom: 0.35rem;
        }

        .system-value {
            font-size: 1.22rem;
            font-weight: 800;
            line-height: 1.2;
            letter-spacing: -0.03em;
        }

        .system-meta {
            margin-top: 0.35rem;
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .signal-grid {
            display: grid;
            gap: 0.82rem;
            margin-top: 0.9rem;
        }

        .signal-card {
            padding: 0.95rem 1rem;
            border-radius: 20px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.8);
        }

        .signal-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--support);
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .signal-value {
            font-size: 1rem;
            line-height: 1.45;
            font-weight: 800;
            overflow-wrap: anywhere;
        }

        .signal-copy {
            margin: 0.38rem 0 0;
            color: var(--muted);
            line-height: 1.58;
            font-size: 0.92rem;
        }

        .health-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 0.95rem;
        }

        .health-card {
            padding: 1rem;
            border-radius: 20px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.82);
        }

        .health-card.health-good {
            background: linear-gradient(
                180deg,
                rgba(217, 237, 240, 0.72),
                rgba(255, 255, 255, 0.96)
            );
            border-color: rgba(30, 106, 115, 0.18);
        }

        .health-card.health-warn {
            background: linear-gradient(
                180deg,
                rgba(243, 215, 191, 0.74),
                rgba(255, 255, 255, 0.96)
            );
            border-color: rgba(198, 90, 30, 0.18);
        }

        .health-card.health-danger {
            background: linear-gradient(
                180deg,
                rgba(245, 213, 213, 0.8),
                rgba(255, 255, 255, 0.96)
            );
            border-color: rgba(152, 42, 42, 0.18);
        }

        .health-title {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin-bottom: 0.35rem;
        }

        .health-value {
            font-size: 1.45rem;
            font-weight: 800;
            letter-spacing: -0.04em;
        }

        .health-copy {
            margin-top: 0.35rem;
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .attention-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 0.95rem;
        }

        .attention-card {
            padding: 1rem;
            border-radius: 20px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.84);
        }

        .attention-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.45rem;
        }

        .attention-source {
            font-size: 1rem;
            font-weight: 800;
            line-height: 1.35;
            overflow-wrap: anywhere;
        }

        .health-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.35rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            white-space: nowrap;
        }

        .health-pill.state-healthy {
            background: rgba(30, 106, 115, 0.12);
            color: var(--support);
        }

        .health-pill.state-due,
        .health-pill.state-pending {
            background: rgba(198, 90, 30, 0.12);
            color: var(--accent);
        }

        .health-pill.state-failing {
            background: rgba(152, 42, 42, 0.14);
            color: #982a2a;
        }

        .health-pill.state-running {
            background: rgba(86, 86, 86, 0.12);
            color: #4f4a42;
        }

        .attention-meta {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .hero-shell {
            padding: 2.2rem 2.25rem;
            border-radius: 38px;
            background:
                linear-gradient(135deg, rgba(255, 252, 247, 0.98), rgba(248, 237, 222, 0.84)),
                linear-gradient(120deg, rgba(187, 79, 29, 0.08), rgba(23, 95, 104, 0.12));
            position: relative;
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            inset: auto 2rem 1.6rem auto;
            width: 9rem;
            height: 9rem;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(187, 79, 29, 0.14), transparent 66%);
            pointer-events: none;
        }

        .hero-grid {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 1.42fr 0.86fr;
            gap: 1.25rem;
            align-items: stretch;
        }

        .hero-title {
            font-size: clamp(2.25rem, 4vw, 4rem);
            line-height: 0.95;
        }

        .hero-support-card {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 1rem;
            padding: 1.28rem;
            border-radius: 26px;
            background:
                linear-gradient(
                    180deg,
                    rgba(255, 255, 255, 0.78),
                    rgba(244, 235, 225, 0.84)
                );
            border: 1px solid rgba(102, 84, 62, 0.12);
            box-shadow: 0 18px 42px rgba(73, 48, 24, 0.1);
        }

        .hero-support-title {
            margin: 0;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--support);
            font-weight: 800;
        }

        .hero-support-copy {
            margin: 0.55rem 0 0;
            color: var(--muted);
            line-height: 1.65;
        }

        .hero-metric-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.8rem;
        }

        .hero-metric {
            padding: 0.92rem 0.95rem;
            border-radius: 18px;
            background: rgba(255, 250, 244, 0.94);
            border: 1px solid var(--line);
        }

        .hero-metric-label {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin-bottom: 0.32rem;
        }

        .hero-metric-value {
            font-size: 1.06rem;
            font-weight: 800;
            color: var(--ink);
        }

        .section-shell {
            padding: 1.15rem 1.2rem;
            border-radius: 28px;
            background: rgba(255, 250, 244, 0.82);
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
        }

        .mode-shell {
            padding: 1rem 1.15rem 1.05rem;
            border-radius: 24px;
            background:
                linear-gradient(
                    135deg,
                    rgba(255, 250, 244, 0.92),
                    rgba(239, 229, 212, 0.82)
                );
            border: 1px solid var(--line);
            box-shadow: 0 16px 38px rgba(60, 39, 23, 0.08);
        }

        .mode-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 1rem;
            margin-bottom: 0.75rem;
        }

        .mode-title {
            margin: 0;
            font-size: 1.15rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }

        .mode-copy {
            margin: 0.25rem 0 0;
            color: var(--muted);
            line-height: 1.55;
        }

        .mode-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.72rem;
            border-radius: 999px;
            background: rgba(23, 95, 104, 0.09);
            color: var(--support);
            font-size: 0.82rem;
            font-weight: 800;
            white-space: nowrap;
        }

        .quickstart-shell {
            padding: 1.2rem 1.2rem 0.2rem;
            border-radius: 28px;
            background:
                linear-gradient(
                    180deg,
                    rgba(255, 252, 248, 0.92),
                    rgba(246, 236, 223, 0.86)
                );
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
        }

        .workspace-shell {
            padding: 1.15rem 1.2rem;
            border-radius: 28px;
            background: linear-gradient(180deg, rgba(24, 50, 59, 0.96), rgba(28, 61, 72, 0.92));
            color: #f9f2e8;
            box-shadow: 0 24px 58px rgba(24, 50, 59, 0.18);
        }

        .workspace-kicker {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: rgba(249, 242, 232, 0.68);
            font-weight: 700;
        }

        .workspace-title {
            margin: 0.35rem 0 0.4rem;
            font-size: 1.32rem;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .workspace-copy {
            margin: 0;
            color: rgba(249, 242, 232, 0.78);
            line-height: 1.65;
        }

        .section-kicker {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--support);
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .section-title {
            margin: 0;
            font-size: 1.38rem;
            line-height: 1.2;
            letter-spacing: -0.03em;
            font-weight: 800;
        }

        .section-copy {
            margin: 0.45rem 0 0;
            color: var(--muted);
            line-height: 1.64;
        }

        .news-board-shell {
            padding: 1.25rem;
        }

        .news-board-layout {
            display: grid;
            grid-template-columns: minmax(0, 1.12fr) minmax(0, 0.88fr);
            gap: 1rem;
            margin-top: 1rem;
            align-items: stretch;
        }

        .spotlight-card {
            height: 100%;
            display: flex;
            flex-direction: column;
            gap: 0.82rem;
            padding: 1.35rem;
            border-radius: 26px;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 236, 222, 0.92));
            border: 1px solid rgba(198, 90, 30, 0.16);
            box-shadow: 0 18px 42px rgba(73, 48, 24, 0.08);
        }

        .spotlight-label {
            display: inline-flex;
            align-items: center;
            padding: 0.38rem 0.7rem;
            border-radius: 999px;
            background: rgba(198, 90, 30, 0.1);
            color: var(--accent);
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .spotlight-title {
            margin: 0.1rem 0 0.15rem;
            font-size: 1.55rem;
            line-height: 1.14;
            letter-spacing: -0.04em;
            font-weight: 800;
            overflow-wrap: anywhere;
        }

        .spotlight-title a {
            color: var(--ink);
            text-decoration: none;
        }

        .spotlight-title a:hover {
            color: var(--accent);
        }

        .spotlight-summary {
            margin: 0;
            color: var(--muted);
            line-height: 1.74;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .spotlight-meta-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            align-items: center;
            margin-top: auto;
        }

        .spotlight-meta-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.38rem 0.7rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.84);
            border: 1px solid rgba(94, 72, 48, 0.12);
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
        }

        .news-stack-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem;
        }

        .news-stack-card {
            height: 100%;
            display: flex;
            flex-direction: column;
            gap: 0.55rem;
            padding: 1rem 1.05rem;
            border-radius: 20px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.84);
            box-shadow: 0 14px 34px rgba(73, 48, 24, 0.07);
            min-width: 0;
        }

        .news-stack-title {
            margin: 0 0 0.4rem;
            font-size: 1rem;
            line-height: 1.4;
            font-weight: 800;
            overflow-wrap: anywhere;
        }

        .news-stack-title a {
            color: var(--ink);
            text-decoration: none;
        }

        .news-stack-title a:hover {
            color: var(--accent);
        }

        .command-card {
            padding: 1rem 1.05rem;
            border-radius: 20px;
            background: linear-gradient(180deg, rgba(30, 106, 115, 0.08), rgba(255, 255, 255, 0.9));
            border: 1px solid rgba(30, 106, 115, 0.12);
            box-shadow: 0 14px 34px rgba(73, 48, 24, 0.07);
            margin-bottom: 0.9rem;
        }

        .detail-shell {
            margin-bottom: 1rem;
            background: linear-gradient(
                180deg,
                rgba(255, 252, 247, 0.96),
                rgba(244, 235, 225, 0.92)
            );
        }

        .detail-summary {
            margin: 0.55rem 0 0;
            color: var(--muted);
            line-height: 1.72;
        }

        .detail-meta-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin-top: 0.9rem;
        }

        .detail-meta-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.45rem 0.75rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(102, 84, 62, 0.12);
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.4;
        }

        .chat-result-card {
            padding: 0.62rem 0.72rem;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(255, 255, 255, 0.05);
            margin: 0.35rem 0 0.45rem;
        }

        .chat-result-card .mini-kicker {
            font-size: 0.68rem;
            margin-bottom: 0.22rem;
        }

        .chat-result-title {
            margin: 0;
            font-size: 0.95rem;
            line-height: 1.35;
            font-weight: 800;
        }

        .chat-result-summary {
            margin: 0.25rem 0 0.35rem;
            color: var(--muted);
            font-size: 0.86rem;
            line-height: 1.45;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .command-title {
            margin: 0;
            font-size: 1rem;
            line-height: 1.35;
            font-weight: 800;
        }

        .command-copy {
            margin: 0.45rem 0 0;
            color: var(--muted);
            line-height: 1.58;
            font-size: 0.92rem;
        }

        .prompt-list {
            margin: 0.6rem 0 0;
            padding-left: 1.1rem;
            color: var(--muted);
        }

        .prompt-list li {
            margin-bottom: 0.35rem;
        }

        @keyframes chatPulse {
            0% {
                transform: scale(1);
                box-shadow: 0 24px 50px rgba(166, 69, 24, 0.35);
            }

            50% {
                transform: scale(1.03);
                box-shadow: 0 26px 58px rgba(166, 69, 24, 0.44);
            }

            100% {
                transform: scale(1);
                box-shadow: 0 24px 50px rgba(166, 69, 24, 0.35);
            }
        }

        div[data-testid="stPopover"] {
            position: fixed;
            right: 1.4rem;
            bottom: 1.4rem;
            z-index: 999991;
        }

        div[data-testid="stPopover"] button,
        div[data-testid="stPopover"] [role="button"] {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 5.4rem !important;
            min-width: 5.4rem !important;
            max-width: 5.4rem !important;
            height: 5.4rem !important;
            min-height: 5.4rem !important;
            max-height: 5.4rem !important;
            padding: 0 !important;
            aspect-ratio: 1 / 1;
            border-radius: 50% !important;
            border: 3px solid rgba(255, 250, 242, 0.96) !important;
            background:
                radial-gradient(circle at 28% 22%, rgba(255, 255, 255, 0.88), transparent 20%),
                linear-gradient(135deg, #cf5f22, #a34617);
            color: transparent !important;
            box-shadow: 0 24px 50px rgba(166, 69, 24, 0.35);
            font-size: 0 !important;
            animation: chatPulse 2.8s ease-in-out infinite;
            overflow: visible;
        }

        div[data-testid="stPopover"] button *,
        div[data-testid="stPopover"] [role="button"] * {
            opacity: 0;
            font-size: 0 !important;
            line-height: 0 !important;
        }

        div[data-testid="stPopover"] button::before,
        div[data-testid="stPopover"] [role="button"]::before {
            content: "";
            position: absolute;
            inset: 0.22rem;
            border-radius: 50%;
            background-image: var(--chat-avatar);
            background-size: cover;
            background-position: center;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.28);
            pointer-events: none;
        }

        div[data-testid="stPopover"] button::after,
        div[data-testid="stPopover"] [role="button"]::after {
            content: "Bạn cần tìm kiếm thông tin gì trong ngày, tôi có thể giúp bạn";
            position: absolute;
            right: calc(100% + 0.95rem);
            top: 50%;
            transform: translateY(-50%);
            width: 16rem;
            padding: 0.9rem 1rem;
            border-radius: 1.2rem;
            background: rgba(255, 250, 242, 0.97);
            border: 1px solid rgba(102, 84, 62, 0.16);
            box-shadow: 0 18px 40px rgba(73, 48, 24, 0.18);
            color: var(--ink);
            font-size: 0.93rem;
            font-weight: 700;
            line-height: 1.45;
            text-align: left;
            pointer-events: none;
        }

        div[data-testid="stPopover"] button:hover,
        div[data-testid="stPopover"] [role="button"]:hover {
            background: linear-gradient(135deg, #db6d31, #b14d1c);
        }

        div[data-testid="stPopover"] button:hover::after,
        div[data-testid="stPopover"] [role="button"]:hover::after {
            background: rgba(255, 248, 238, 0.99);
        }

        [data-testid="stTabs"] button {
            border-radius: 999px;
            padding: 0.55rem 1rem;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(102, 84, 62, 0.14);
            color: var(--muted);
            font-weight: 700;
        }

        [data-testid="stTabs"] button[aria-selected="true"] {
            background: linear-gradient(135deg, rgba(198, 90, 30, 0.12), rgba(30, 106, 115, 0.12));
            color: var(--ink);
            border-color: rgba(198, 90, 30, 0.18);
        }

        div[data-testid="stDataFrame"] {
            border-radius: 22px;
            overflow: hidden;
            border: 1px solid var(--line);
            box-shadow: 0 14px 34px rgba(73, 48, 24, 0.08);
        }

        div.stDownloadButton > button {
            border-radius: 999px;
            background: linear-gradient(135deg, #cf5f22, #9f4213);
            color: white;
            border: none;
            font-weight: 700;
            padding: 0.6rem 1rem;
        }

        div.stDownloadButton > button:hover {
            background: linear-gradient(135deg, #dd6f31, #b14b17);
            color: white;
        }

        @media (max-width: 900px) {
            .hero-shell {
                padding: 1.4rem 1.2rem;
            }

            .hero-grid {
                grid-template-columns: 1fr;
            }

            .hero-metric-grid {
                grid-template-columns: 1fr 1fr;
            }

            .health-grid {
                grid-template-columns: 1fr 1fr;
            }

            .attention-grid {
                grid-template-columns: 1fr;
            }

            .system-grid {
                grid-template-columns: 1fr 1fr;
            }

            .stat-grid {
                grid-template-columns: 1fr;
            }

            .news-board-layout,
            .news-stack-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 760px) {
            .health-grid {
                grid-template-columns: 1fr;
            }

            .system-grid {
                grid-template-columns: 1fr;
            }

            div[data-testid="stPopover"] {
                right: 1rem;
                bottom: 1rem;
            }

            div[data-testid="stPopover"] button::after,
            div[data-testid="stPopover"] [role="button"]::after {
                right: 0;
                top: auto;
                bottom: calc(100% + 0.8rem);
                transform: none;
                width: 13.5rem;
            }
        }
        </style>
        """
    render_html_block(styles.replace("__CHAT_AVATAR_DATA__", CHAT_AVATAR_DATA))


def build_status_chip(label: str, value: str) -> str:
    return f"<span class='status-chip'>{escape(label)} <strong>{escape(value)}</strong></span>"


def render_hero(health_payload: dict | None, dataset_overview: list[dict] | None = None) -> None:
    db_driver = format_database_driver_label(
        health_payload.get("database_driver")
        if health_payload
        else None
    )
    counts = dataset_count_map(dataset_overview)
    retrieval_label = "bật" if settings.experimental_retrieval_enabled else "tắt"
    chat_label = "OpenAI + fallback" if settings.chat_use_openai else "agent nội bộ"
    api_label = format_api_base_label(API_BASE_URL)
    today_label = datetime.now().strftime("%d/%m/%Y")
    hero_html = f"""
    <section class="hero-shell">
        <div class="hero-grid">
            <div>
                <span class="hero-eyebrow">Phòng điều phối dữ liệu trong ngày • {today_label}</span>
                <h1 class="hero-title">
                    Một newsroom dữ liệu gọn, đủ để xem dòng chảy thông tin và hỏi đáp ngay.
                </h1>
                <p class="hero-copy">
                    Màn hình này ưu tiên ba việc: nhìn thấy tín hiệu quan trọng ngay,
                    kiểm tra dữ liệu đã ingest mà không cần SQL, và chuyển nhanh
                    giữa Dashboard, Trợ lý AI, Explorer, Hệ thống bằng sidebar.
                </p>
                <div class="chip-row">
                    {build_status_chip("Database", db_driver)}
                    {build_status_chip("Retrieval", retrieval_label)}
                    {build_status_chip("Chat", chat_label)}
                    {build_status_chip("API", api_label)}
                </div>
            </div>
            <div class="hero-support-card">
                <div>
                    <p class="hero-support-title">Sẵn sàng cho demo</p>
                    <p class="hero-support-copy">
                        Giao diện đã tách thành các workspace rõ ràng:
                        Dashboard để xem nhanh, Trợ lý AI để hội thoại,
                        Explorer để tra cứu sâu và Hệ thống để kiểm tra runtime.
                    </p>
                </div>
                <div class="hero-metric-grid">
                    <div class="hero-metric">
                        <div class="hero-metric-label">Tin tức</div>
                        <div class="hero-metric-value">
                            {format_record_count(counts.get("articles", 0))} bài
                        </div>
                    </div>
                    <div class="hero-metric">
                        <div class="hero-metric-label">Giá cả</div>
                        <div class="hero-metric-value">
                            {format_record_count(counts.get("price_snapshots", 0))} mốc giá
                        </div>
                    </div>
                    <div class="hero-metric">
                        <div class="hero-metric-label">Chính sách</div>
                        <div class="hero-metric-value">
                            {format_record_count(counts.get("policy_documents", 0))} văn bản
                        </div>
                    </div>
                    <div class="hero-metric">
                        <div class="hero-metric-label">Giao thông</div>
                        <div class="hero-metric-value">
                            {format_record_count(counts.get("traffic_events", 0))} sự kiện
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """
    render_html_block(hero_html)


def render_system_status(
    health_payload: dict | None,
    health_error: str | None,
) -> None:
    st.markdown("### Tình trạng hệ thống")
    if health_error:
        st.error(f"Không đọc được /health: {health_error}")
        return

    if not health_payload:
        st.info("Chưa có dữ liệu health.")
        return

    database_driver = format_database_driver_label(
        health_payload.get("database_driver")
    )
    database_target = format_database_target(health_payload.get("database_url"))
    api_status = health_payload.get("status", "unknown")
    api_label = "Sẵn sàng" if api_status == "ok" else api_status
    api_meta = f"Kết nối tới {format_api_base_label(API_BASE_URL)}"
    if database_driver == "SQLite":
        database_meta = (
            f"{database_target}. Ứng dụng đang chạy fallback local thay vì PostgreSQL."
        )
        database_tone = "system-warm"
    else:
        database_meta = database_target
        database_tone = "system-good"
    retrieval_label = (
        "Experimental bật"
        if settings.experimental_retrieval_enabled
        else "Đang tắt"
    )
    retrieval_meta = (
        "Chỉ dùng cho topic_summary và semantic policy lookup."
        if settings.experimental_retrieval_enabled
        else "Structured lookup và fallback cũ đang là đường chính."
    )
    chat_label = "OpenAI + fallback" if settings.chat_use_openai else "Agent nội bộ"
    chat_meta = (
        "Nếu OpenAI lỗi hoặc hết quota, chat sẽ tự quay về agent nội bộ."
        if settings.chat_use_openai
        else "Không gọi OpenAI ở runtime hiện tại."
    )

    system_cards = [
        ("API local", api_label, api_meta, "system-good"),
        ("Database runtime", database_driver, database_meta, database_tone),
        ("Chat runtime", chat_label, chat_meta, "system-neutral"),
        ("Retrieval", retrieval_label, retrieval_meta, "system-neutral"),
    ]
    system_html = """
    <section class="system-shell">
        <div class="section-kicker">Runtime overview</div>
        <h3 class="section-title">Các dịch vụ chính đang ở trạng thái nào</h3>
        <p class="section-copy">
            Khối này chỉ hiển thị trạng thái hệ thống thật: API, database,
            chế độ chat và experimental retrieval.
        </p>
        <div class="system-grid">
    """
    for label, value, meta, tone in system_cards:
        system_html += f"""
            <div class="system-card {escape(tone)}">
                <div class="system-label">{escape(label)}</div>
                <div class="system-value">{escape(value)}</div>
                <div class="system-meta">{escape(meta)}</div>
            </div>
        """
    system_html += """
        </div>
    </section>
    """
    render_html_block(system_html)


def render_source_health() -> None:
    st.markdown("### Sức khỏe nguồn dữ liệu")
    snapshot = load_scheduler_health_snapshot()
    if not snapshot["initialized"]:
        st.info(
            "Chưa có snapshot scheduler. Hãy chạy `scripts/run_scheduler.py --run-once` "
            "để tạo trạng thái theo dõi source."
        )
        st.caption(
            f"Hiện có {snapshot['configured_sources']} source live được cấu hình cho scheduler."
        )
        return

    summary = snapshot["summary"] or {}
    health_cards = [
        (
            "Ổn định",
            str(summary.get("healthy_jobs", 0)),
            "Source đã chạy thành công và chưa đến lịch chạy tiếp.",
            "health-good",
        ),
        (
            "Đến lịch",
            str(summary.get("due_jobs", 0)),
            "Source đã tới lịch chạy lại theo fetch_interval_minutes.",
            "health-warn",
        ),
        (
            "Chưa có snapshot",
            str(summary.get("pending_jobs", 0)),
            "Source đã cấu hình nhưng scheduler chưa ghi trạng thái lần đầu.",
            "health-warn",
        ),
        (
            "Đang lỗi",
            str(summary.get("failing_jobs", 0)),
            "Source có failure_streak > 0 hoặc lần chạy gần nhất bị failed.",
            "health-danger",
        ),
    ]
    summary_html = """
    <section class="section-shell">
        <div class="section-kicker">Scheduler health</div>
        <h3 class="section-title">Nguồn nào cần chú ý ngay trên local</h3>
        <p class="section-copy">
            Khối này đọc trực tiếp từ file scheduler status local và giúp nhìn nhanh
            source nào đang ổn, source nào đã đến lịch hoặc đang lỗi.
        </p>
        <div class="health-grid">
    """
    for title, value, copy, tone in health_cards:
        summary_html += f"""
            <div class="health-card {escape(tone)}">
                <div class="health-title">{escape(title)}</div>
                <div class="health-value">{escape(value)}</div>
                <div class="health-copy">{escape(copy)}</div>
            </div>
        """
    summary_html += "</div></section>"
    render_html_block(summary_html)

    attention_jobs = snapshot["attention_jobs"][:6]
    if not attention_jobs:
        st.success("Hiện không có source nào cần chú ý. Scheduler local đang sạch.")
        st.caption(f"Đọc từ: {snapshot['status_path']}")
        return

    attention_html = """
    <section class="section-shell">
        <div class="section-kicker">Attention</div>
        <h3 class="section-title">Nguồn cần kiểm tra trước khi demo</h3>
        <div class="attention-grid">
    """
    for job in attention_jobs:
        health_state = job["health_state"]
        next_run = format_datetime(job.get("next_run_at"))
        last_finished = format_datetime(job.get("last_finished_at"))
        error_message = job.get("last_error_message") or "Không có lỗi chi tiết."
        source_label = f"{job['pipeline']} / {job['source_name']}"
        attention_html += f"""
            <div class="attention-card">
                <div class="attention-header">
                    <div class="attention-source">{escape(source_label)}</div>
                    <span class="health-pill state-{escape(health_state)}">
                        {escape(display_health_state_label(health_state))}
                    </span>
                </div>
                <div class="attention-meta">
                    Last status: {escape(str(job.get('last_status') or 'chưa chạy'))}<br/>
                    Failure streak: {escape(str(job.get('failure_streak', 0)))}<br/>
                    Last finished: {escape(last_finished)}<br/>
                    Next run: {escape(next_run)}<br/>
                    Error: {escape(error_message)}
                </div>
            </div>
        """
    attention_html += "</div></section>"
    render_html_block(attention_html)
    st.caption(f"Đọc từ: {snapshot['status_path']}")


def render_news_board(news_payload: dict | None, error_message: str | None) -> None:
    st.markdown("### Bản tin biên tập")
    if error_message:
        st.error(f"Không tải được tin hot: {error_message}")
        return

    items = (news_payload or {}).get("items", [])
    board_model = build_news_board_model(items, secondary_limit=4)
    if not board_model.featured:
        st.info("Hiện chưa có dữ liệu tin hot.")
        return

    featured = board_model.featured
    others = board_model.secondary_items
    section_copy = (
        f"Cụm này chọn 1 tin dẫn và {len(others)} tin bổ trợ từ "
        f"{board_model.source_count} nguồn để người xem nắm bối cảnh nhanh hơn."
    )
    featured_item = build_content_item("news", featured)
    featured_source = format_ui_source_label(str(featured_item.get("source") or ""))
    featured_summary = shorten_preview_text(featured_item.get("summary"), limit=220)
    render_html_block(
        f"""
        <section class="section-shell news-board-shell">
            <div class="section-kicker">Tin tức &amp; biên tập</div>
            <h3 class="section-title">Những câu chuyện nên xem đầu tiên</h3>
            <p class="section-copy">{escape(section_copy)}</p>
        </section>
        """
    )
    spotlight_col, stack_col = st.columns([1.12, 0.88], gap="large")
    with spotlight_col:
        render_html_block(
            f"""
            <article class="spotlight-card">
                <span class="spotlight-label">Tin dẫn</span>
                <div class="spotlight-title">
                    {escape(str(featured_item.get('title') or 'Chưa có tiêu đề'))}
                </div>
                <p class="spotlight-summary">{escape(featured_summary)}</p>
                <div class="spotlight-meta-row">
                    <span class="spotlight-meta-pill">{escape(featured_source)}</span>
                    <span class="spotlight-meta-pill">
                        {escape(format_datetime(str(featured_item.get('updated_at') or '')))}
                    </span>
                </div>
            </article>
            """
        )
        render_item_actions(
            featured_item,
            key_prefix="news_featured",
            origin="dashboard",
            show_explorer=True,
            show_source=False,
            action_style="menu",
        )
    with stack_col:
        grid_cols = st.columns(2, gap="small")
        for index, item in enumerate(others):
            with grid_cols[index % 2]:
                content_item = build_content_item("news", item)
                render_html_block(
                    f"""
                    <article class="news-stack-card">
                        <div class="mini-kicker">
                            {escape(format_ui_source_label(str(content_item.get("source") or "")))}
                        </div>
                        <div class="news-stack-title">
                            {escape(str(content_item.get("title") or "Chưa có tiêu đề"))}
                        </div>
                        <p class="feature-summary">
                            {escape(shorten_preview_text(content_item.get("summary"), limit=140))}
                        </p>
                        <div class="meta-line">
                            {escape(format_datetime(str(content_item.get("updated_at") or '')))}
                        </div>
                    </article>
                    """
                )
                render_item_actions(
                    content_item,
                    key_prefix=f"news_secondary_{index}",
                    origin="dashboard",
                    show_explorer=False,
                    show_source=False,
                    ai_label="Hỏi AI",
                    ai_mode="ask",
                    action_style="menu",
                )


def render_data_volume_board(
    dataset_overview: list[dict],
    error_message: str | None = None,
) -> None:
    st.markdown("### Quy mô dữ liệu hiện có")
    if error_message:
        st.error(f"Không đọc được quy mô dữ liệu: {error_message}")
        return

    if not dataset_overview:
        st.info("Chưa đọc được số lượng bản ghi trong database.")
        return

    overview_html = """
    <section class="section-shell">
        <div class="section-kicker">Database snapshot</div>
        <h3 class="section-title">Database hiện có bao nhiêu bản ghi theo từng pipeline</h3>
        <p class="section-copy">
            Khối này đọc trực tiếp từ database. Dashboard bên dưới chỉ hiển thị preview,
            không phải toàn bộ dữ liệu hiện có.
        </p>
        <div class="signal-grid">
    """
    for item in dataset_overview:
        overview_html += f"""
            <div class="signal-card">
                <div class="signal-label">{escape(item['title'])}</div>
                <div class="signal-value">{format_record_count(item['total_rows'])} bản ghi</div>
                <p class="signal-copy">{escape(item['description'])}</p>
            </div>
        """
    overview_html += """
        </div>
    </section>
    """
    render_html_block(overview_html)
    sparse_notice = build_sparse_data_notice(dataset_overview)
    if sparse_notice:
        st.warning(sparse_notice)
    else:
        st.caption(
            "Dashboard chỉ hiển thị preview. Muốn xem đầy đủ, "
            "chuyển sang workspace Explorer từ sidebar."
        )


def ensure_ui_state() -> None:
    st.session_state.setdefault("nav_section", "dashboard")
    st.session_state.setdefault("nav_request", None)
    st.session_state.setdefault("browser_include_technical", False)
    st.session_state.setdefault("floating_chat_input", "")
    st.session_state.setdefault("assistant_chat_input", "")
    st.session_state.setdefault("quick_action_query", "")
    st.session_state.setdefault("pending_chat_request", None)
    st.session_state.setdefault("active_detail_item", None)
    st.session_state.setdefault("active_detail_origin", None)
    for technical_scope, default_dataset in (
        (False, BUSINESS_DATASET_DEFAULT),
        (True, TECHNICAL_DATASET_DEFAULT),
    ):
        st.session_state.setdefault(
            browser_state_key("dataset_title", technical_scope=technical_scope),
            default_dataset,
        )
        st.session_state.setdefault(
            browser_state_key("keyword", technical_scope=technical_scope),
            "",
        )
        st.session_state.setdefault(
            browser_state_key("row_limit", technical_scope=technical_scope),
            50,
        )
        st.session_state.setdefault(
            browser_state_key("sort_label", technical_scope=technical_scope),
            "Mới nhất trước",
        )
        for field in BROWSER_FILTER_FIELDS:
            st.session_state.setdefault(
                browser_state_key(f"filter_{field}", technical_scope=technical_scope),
                "Tất cả",
            )
        st.session_state.setdefault(
            browser_state_key("detail_record", technical_scope=technical_scope),
            "",
        )


def reset_browser_filters(*, technical_scope: bool = False) -> None:
    for field in BROWSER_FILTER_FIELDS:
        st.session_state[
            browser_state_key(f"filter_{field}", technical_scope=technical_scope)
        ] = "Tất cả"


def apply_pending_navigation_request() -> None:
    requested_section = st.session_state.pop("nav_request", None)
    if requested_section:
        st.session_state.update(build_navigation_state(requested_section))


def queue_navigation(section_key: str) -> None:
    st.session_state["nav_request"] = section_key


def switch_to_data_browser(dataset_title: str, *, keyword: str = "") -> None:
    apply_browser_prefill(build_browser_prefill(dataset_title, keyword=keyword))


def apply_browser_prefill(prefill: dict[str, object]) -> None:
    queue_navigation("explorer")
    technical_scope = False
    st.session_state[browser_state_key("dataset_title", technical_scope=technical_scope)] = str(
        prefill.get("dataset_title") or BUSINESS_DATASET_DEFAULT
    )
    st.session_state[browser_state_key("keyword", technical_scope=technical_scope)] = str(
        prefill.get("keyword") or ""
    )
    st.session_state[browser_state_key("sort_label", technical_scope=technical_scope)] = str(
        prefill.get("sort_label") or "Mới nhất trước"
    )
    reset_browser_filters(technical_scope=technical_scope)
    structured_filters = prefill.get("structured_filters") or {}
    if isinstance(structured_filters, dict):
        for field in BROWSER_FILTER_FIELDS:
            value = structured_filters.get(field)
            if value:
                st.session_state[
                    browser_state_key(f"filter_{field}", technical_scope=technical_scope)
                ] = str(value)


def switch_to_data_browser_with_prefill(
    dataset_title: str,
    *,
    keyword: str = "",
    structured_filters: dict[str, str] | None = None,
) -> None:
    apply_browser_prefill(
        build_browser_prefill(
            dataset_title,
            keyword=keyword,
            structured_filters=structured_filters,
        )
    )


def prepare_chat_draft(question: str) -> None:
    queue_navigation("assistant")
    st.session_state["floating_chat_input"] = question
    st.session_state["assistant_chat_input"] = question
    st.session_state["chat_feedback"] = (
        "info",
        "Đã điền sẵn câu hỏi. Bạn có thể gửi ngay trong khu Trợ lý AI hoặc từ avatar nổi.",
    )


def prepare_chat_request(
    question: str,
    *,
    mode: str = "default",
    context_item: dict | None = None,
) -> None:
    prepare_chat_draft(question)
    st.session_state["pending_chat_request"] = build_chat_request(
        question,
        mode=mode,
        context_item=context_item,
    )
    st.session_state["pending_chat_question"] = question.strip()


def show_detail_item(item: dict, *, origin: str) -> None:
    st.session_state["active_detail_item"] = build_detail_state(item, origin=origin)["item"]
    st.session_state["active_detail_origin"] = origin


def clear_detail_item() -> None:
    st.session_state["active_detail_item"] = None
    st.session_state["active_detail_origin"] = None


def open_item_in_explorer(item: dict) -> None:
    apply_browser_prefill(build_browser_prefill_from_item(item))


def queue_item_summary(item: dict, *, navigate: bool = True) -> None:
    question = str(item.get("question_hint") or f"Tóm tắt nhanh mục này: {item.get('title')}")
    if navigate:
        prepare_chat_request(question, mode="summarize_item", context_item=item)
    else:
        st.session_state["pending_chat_request"] = build_chat_request(
            question,
            mode="summarize_item",
            context_item=item,
        )
        st.session_state["pending_chat_question"] = question


def queue_item_question(item: dict, *, navigate: bool = True) -> None:
    question = f"Giải thích nhanh mục này giúp tôi: {item.get('title')}"
    if navigate:
        prepare_chat_request(question, mode="ask_about_item", context_item=item)
    else:
        st.session_state["pending_chat_request"] = build_chat_request(
            question,
            mode="ask_about_item",
            context_item=item,
        )
        st.session_state["pending_chat_question"] = question


def render_page_header(
    *,
    kicker: str,
    title: str,
    description: str,
    badges: list[tuple[str, str]] | None = None,
) -> None:
    header_html = f"""
    <section class="page-shell">
        <div class="page-header">
            <div>
                <div class="section-kicker">{escape(kicker)}</div>
                <h2 class="page-title">{escape(title)}</h2>
                <p class="page-copy">{escape(description)}</p>
            </div>
            <div class="page-actions">
    """
    for label, value in badges or []:
        header_html += build_status_chip(label, value)
    header_html += """
            </div>
        </div>
    </section>
    """
    render_html_block(header_html)


def render_link_cta(
    label: str,
    url: str | None,
    *,
    key: str,
    button_width: str = "stretch",
) -> None:
    if not url:
        st.button(label, key=f"{key}_disabled", width=button_width, disabled=True)
        return

    link_button = getattr(st, "link_button", None)
    if link_button is not None:
        link_button(label, url, width=button_width)
        return
    st.markdown(f"[{escape(label)}]({escape(url)})")


def trigger_item_action(
    action_key: str,
    *,
    item: dict,
    origin: str,
    ai_mode: str,
    close_menu_key: str | None = None,
) -> None:
    if close_menu_key:
        st.session_state[close_menu_key] = False
    if action_key == "detail":
        show_detail_item(item, origin=origin)
        st.rerun()
    if action_key == "ai":
        show_detail_item(item, origin=origin)
        if ai_mode == "ask":
            queue_item_question(item)
        else:
            queue_item_summary(item)
        st.rerun()
    if action_key == "explorer":
        show_detail_item(item, origin=origin)
        open_item_in_explorer(item)
        st.rerun()


def render_item_actions(
    item: dict,
    *,
    key_prefix: str,
    origin: str,
    show_explorer: bool = True,
    show_source: bool = False,
    ai_label: str = "Tóm tắt bằng AI",
    ai_mode: str = "summarize",
    button_width: str = "stretch",
    action_style: str = "inline",
    menu_label: str = "Thao tác ▼",
) -> None:
    actions = [("detail", "Xem chi tiết"), ("ai", ai_label)]
    if show_explorer:
        actions.append(("explorer", "Mở Explorer"))
    if show_source and item.get("url"):
        actions.append(("source", "Mở nguồn"))

    if action_style == "menu":
        menu_state_key = f"{key_prefix}_menu_open"
        is_open = bool(st.session_state.get(menu_state_key, False))
        visible_label = (
            menu_label.replace("▼", "▲")
            if is_open and "▼" in menu_label
            else menu_label
        )
        if st.button(visible_label, key=f"{key_prefix}_menu_toggle", width=button_width):
            st.session_state[menu_state_key] = not is_open
            st.rerun()
        if not st.session_state.get(menu_state_key, False):
            return
        action_columns = st.columns(len(actions), gap="small")
        for column, (action_key, label) in zip(action_columns, actions, strict=False):
            with column:
                if action_key == "source":
                    render_link_cta(
                        label,
                        str(item.get("url") or ""),
                        key=f"{key_prefix}_source",
                        button_width="stretch",
                    )
                    continue
                if st.button(label, key=f"{key_prefix}_{action_key}", width="stretch"):
                    trigger_item_action(
                        action_key,
                        item=item,
                        origin=origin,
                        ai_mode=ai_mode,
                        close_menu_key=menu_state_key,
                    )
        return

    action_columns = st.columns(len(actions), gap="small")
    for column, (action_key, label) in zip(action_columns, actions, strict=False):
        with column:
            if action_key == "detail":
                if st.button(label, key=f"{key_prefix}_detail", width=button_width):
                    trigger_item_action(
                        "detail",
                        item=item,
                        origin=origin,
                        ai_mode=ai_mode,
                    )
            elif action_key == "ai":
                if st.button(label, key=f"{key_prefix}_ai", width=button_width):
                    trigger_item_action(
                        "ai",
                        item=item,
                        origin=origin,
                        ai_mode=ai_mode,
                    )
            elif action_key == "explorer":
                if st.button(label, key=f"{key_prefix}_explorer", width=button_width):
                    trigger_item_action(
                        "explorer",
                        item=item,
                        origin=origin,
                        ai_mode=ai_mode,
                    )
            elif action_key == "source":
                render_link_cta(
                    label,
                    str(item.get("url") or ""),
                    key=f"{key_prefix}_source",
                    button_width=button_width,
                )


def render_detail_panel() -> None:
    detail_item = st.session_state.get("active_detail_item")
    if not isinstance(detail_item, dict) or not detail_item:
        return

    source_label = format_ui_source_label(str(detail_item.get("source") or ""))
    updated_at = format_datetime(str(detail_item.get("updated_at") or ""))
    summary = shorten_preview_text(
        detail_item.get("summary") or "Hiện chưa có phần mô tả chi tiết hơn cho mục này.",
        limit=340,
    )
    metadata = detail_item.get("metadata") or {}
    meta_pairs = [
        (label, value)
        for label, value in (
            ("Nguồn", source_label),
            ("Cập nhật", updated_at),
            ("Danh mục", metadata.get("category")),
            ("Lĩnh vực", metadata.get("field")),
            ("Cơ quan", metadata.get("issuing_agency")),
            ("Địa điểm", metadata.get("location")),
            ("Mặt hàng", metadata.get("item_name")),
            ("Dự báo", metadata.get("forecast_time")),
        )
        if value
    ]
    meta_html = "".join(
        (
            f'<div class="detail-meta-pill"><strong>{escape(label)}:</strong> '
            f"{escape(str(value))}</div>"
        )
        for label, value in meta_pairs
    )
    render_html_block(
        f"""
        <section class="section-shell detail-shell">
            <div class="section-kicker">Chi tiết đang mở</div>
            <h3 class="section-title">{escape(str(detail_item.get("title") or "Mục dữ liệu"))}</h3>
            <p class="detail-summary">{escape(summary)}</p>
            <div class="detail-meta-grid">
                {meta_html}
            </div>
        </section>
        """
    )

    action_columns = st.columns(4, gap="small")
    with action_columns[0]:
        if st.button("Tóm tắt bằng AI", key="detail_panel_ai", width="stretch"):
            queue_item_summary(detail_item)
            st.rerun()
    with action_columns[1]:
        if st.button("Hỏi AI về mục này", key="detail_panel_ask_ai", width="stretch"):
            queue_item_question(detail_item)
            st.rerun()
    with action_columns[2]:
        if st.button("Mở trong Explorer", key="detail_panel_explorer", width="stretch"):
            open_item_in_explorer(detail_item)
            st.rerun()
    with action_columns[3]:
        render_link_cta("Mở nguồn", str(detail_item.get("url") or ""), key="detail_panel_source")

    utility_columns = st.columns([1, 1.2], gap="small")
    with utility_columns[0]:
        if st.button("Đóng chi tiết", key="detail_panel_close", width="stretch"):
            clear_detail_item()
            st.rerun()
    with utility_columns[1]:
        st.caption(
            "Luồng gợi ý: xem preview -> mở chi tiết -> hỏi AI / mở Explorer "
            "-> mở nguồn gốc nếu cần."
        )


def build_record_picker_label(dataset_key: str, record: dict) -> str:
    if dataset_key == "articles":
        return str(record.get("title") or f"Bài viết #{record.get('id')}")
    if dataset_key == "policy_documents":
        return str(record.get("title") or f"Văn bản #{record.get('id')}")
    if dataset_key == "traffic_events":
        return str(record.get("title") or f"Sự kiện #{record.get('id')}")
    if dataset_key == "price_snapshots":
        return str(record.get("item_name") or f"Bản ghi giá #{record.get('id')}")
    if dataset_key == "weather_snapshots":
        return str(record.get("location") or f"Bản ghi thời tiết #{record.get('id')}")
    return f"Bản ghi #{record.get('id')}"


def render_sidebar_navigation(
    health_payload: dict | None,
    dataset_overview: list[dict],
    *,
    data_mode_label: str,
    data_mode_copy: str,
) -> str:
    current_section = st.session_state.get("nav_section", "dashboard")
    current_label = navigation_label_from_key(current_section)
    options = navigation_labels()
    if current_label not in options:
        current_label = options[0]

    db_driver = format_database_driver_label(
        health_payload.get("database_driver") if health_payload else None
    )
    chat_runtime = "OpenAI + fallback" if settings.chat_use_openai else "Agent nội bộ"
    retrieval_runtime = "Bật" if settings.experimental_retrieval_enabled else "Tắt"

    with st.sidebar:
        render_html_block(
            """
            <div class="sidebar-shell">
                <div class="section-kicker">Điều hướng</div>
                <div class="sidebar-title">Trung tâm điều phối thông tin hằng ngày</div>
                <p class="sidebar-copy">
                    Chọn khu làm việc theo nhu cầu: xem nhanh, hỏi AI,
                    tra cứu dữ liệu hoặc kiểm tra hệ thống.
                </p>
            </div>
            """
        )
        selected_label = st.radio(
            "Khu làm việc",
            options=options,
            index=options.index(current_label),
            key="nav_section_widget",
            label_visibility="collapsed",
        )
        st.session_state["nav_section"] = navigation_key_from_label(selected_label)
        current_item = next(
            (
                item
                for item in NAVIGATION_ITEMS
                if item.key == st.session_state["nav_section"]
            ),
            NAVIGATION_ITEMS[0],
        )
        render_html_block(
            f"""
            <div class="sidebar-shell">
                <div class="section-kicker">{escape(current_item.icon)} · Workspace</div>
                <div class="sidebar-title">{escape(current_item.label)}</div>
                <p class="sidebar-copy">{escape(current_item.description)}</p>
            </div>
            """
        )

        render_html_block(
            f"""
            <div class="sidebar-shell">
                <div class="section-kicker">Demo indicator</div>
                <div class="sidebar-title">Runtime hiện tại</div>
                <p class="sidebar-copy">{escape(data_mode_copy)}</p>
            </div>
            """
        )
        st.caption("Trạng thái nhanh")
        st.markdown(
            "\n".join(
                [
                    f"- `Database`: {db_driver}",
                    f"- `Chat`: {chat_runtime}",
                    f"- `Retrieval`: {retrieval_runtime}",
                    f"- `Data`: {data_mode_label}",
                ]
            )
        )

        st.write("")
        render_html_block(
            """
            <div class="sidebar-shell">
                <div class="section-kicker">Quick actions</div>
                <div class="sidebar-title">Tìm nhanh hoặc hỏi nhanh</div>
                <p class="sidebar-copy">
                    Bạn có thể nhập một cụm ngắn để mở Explorer
                    hoặc đẩy thẳng thành câu hỏi cho AI.
                </p>
            </div>
            """
        )
        quick_query = st.text_input(
            "Quick action",
            key="quick_action_query",
            placeholder="Ví dụ: giáo dục, giá vàng, Hải Phòng...",
        )
        quick_left, quick_right = st.columns(2, gap="small")
        with quick_left:
            if st.button("Tìm trong Explorer", key="sidebar_quick_explorer", width="stretch"):
                switch_to_data_browser("Tin tức", keyword=quick_query.strip())
                st.rerun()
        with quick_right:
            if st.button("Hỏi AI", key="sidebar_quick_ai", width="stretch"):
                prepare_chat_draft(quick_query.strip() or "Tin hot hôm nay là gì?")
                st.rerun()

        counts = dataset_count_map(dataset_overview)
        st.caption("Quy mô dữ liệu")
        st.markdown(
            "\n".join(
                [
                    f"- `Tin tức`: {format_record_count(counts.get('articles', 0))}",
                    f"- `Giá`: {format_record_count(counts.get('price_snapshots', 0))}",
                    f"- `Thời tiết`: {format_record_count(counts.get('weather_snapshots', 0))}",
                    f"- `Chính sách`: {format_record_count(counts.get('policy_documents', 0))}",
                    f"- `Giao thông`: {format_record_count(counts.get('traffic_events', 0))}",
                ]
            )
        )

    return st.session_state["nav_section"]


def render_quick_start() -> None:
    render_html_block(
        """
            <section class="quickstart-shell">
                <div class="section-kicker">Bắt đầu nhanh</div>
                <h3 class="section-title">
                Ba lối vào ngắn nhất để người xem không bị lạc trong sản phẩm demo
                </h3>
                <p class="section-copy">
                Chọn xem feed nổi bật, đi thẳng sang Explorer,
                hoặc mở sẵn một câu hỏi trong workspace Trợ lý AI.
                </p>
            </section>
        """
    )
    columns = st.columns(len(QUICK_START_ACTIONS), gap="large")
    for index, action in enumerate(QUICK_START_ACTIONS):
        with columns[index]:
            render_html_block(
                f"""
                <div class="mini-card">
                    <div class="mini-kicker">Luồng thao tác</div>
                    <div class="mini-title">{escape(action.title)}</div>
                    <div class="mini-copy">{escape(action.description)}</div>
                </div>
                """
            )
            if st.button(action.title, key=f"quick_start_{index}", width="stretch"):
                if action.dataset_title:
                    switch_to_data_browser(action.dataset_title)
                if action.suggested_question:
                    prepare_chat_draft(action.suggested_question)
                st.rerun()


def render_section_actions(
    *,
    key_prefix: str,
    dataset_title: str,
    suggested_question: str,
) -> None:
    left_action, right_action = st.columns(2, gap="small")
    with left_action:
        if st.button(
            f"Xem thêm trong {dataset_title}",
            key=f"{key_prefix}_browser_action",
            width="stretch",
        ):
            switch_to_data_browser(dataset_title)
            st.rerun()
    with right_action:
        if st.button(
            "Chuẩn bị câu hỏi AI",
            key=f"{key_prefix}_chat_action",
            width="stretch",
        ):
            prepare_chat_draft(suggested_question)
            st.rerun()


def render_overview_board(
    health_payload: dict | None,
    health_error: str | None,
    news_payload: dict | None,
    price_payload: dict | None,
    weather_payloads: list[tuple[str, dict | None, str | None]],
) -> None:
    st.markdown("### Bảng điều phối")
    if health_error:
        st.error(f"Không đọc được /health: {health_error}")
        return

    if not health_payload:
        st.info("Chưa có dữ liệu health.")
        return

    news_items = (news_payload or {}).get("items", [])
    top_sources = Counter(
        format_ui_source_label(item.get("source", "unknown"))
        for item in news_items
    )
    dominant_source, dominant_count = ("Chưa có dữ liệu", 0)
    if top_sources:
        dominant_source, dominant_count = top_sources.most_common(1)[0]

    weather_ready_count = sum(1 for _, payload, _ in weather_payloads if payload)
    signal_cards = [
        (
            "Nguồn nổi bật trong feed",
            dominant_source,
            f"{dominant_count} bản tin trong cụm hiển thị hiện tại.",
        ),
        (
            "Nhịp dữ liệu",
            f"{len(news_items)} tin / {len((price_payload or {}).get('items', []))} giá",
            f"{weather_ready_count} điểm thời tiết đang có dữ liệu.",
        ),
        (
            "Lộ trình demo",
            "Tin nổi bật → giá live → thời tiết → avatar chat",
            "Nếu cần đối chiếu nguồn hoặc soi dữ liệu sâu hơn, chuyển sang workspace Explorer.",
        ),
    ]

    signal_html = """
    <div class="section-shell">
        <div class="section-kicker">Điều phối</div>
        <h3 class="section-title">Tín hiệu nổi bật trên dashboard</h3>
        <p class="section-copy">
            Khối này tập trung vào dữ liệu đang thấy trên màn hình và thứ tự demo hợp lý.
        </p>
        <div class="signal-grid">
    """
    for label, value, copy in signal_cards:
        signal_html += f"""
            <div class="signal-card">
                <div class="signal-label">{escape(label)}</div>
                <div class="signal-value">{escape(value)}</div>
                <p class="signal-copy">{escape(copy)}</p>
            </div>
        """
    signal_html += """
        </div>
        <div class="inline-note">
            Khi OpenAI không sẵn sàng, phần chat vẫn fallback sang agent nội bộ
            nên luồng demo không bị gãy.
        </div>
    </div>
    """
    render_html_block(signal_html)


def render_dashboard_quick_charts(
    dataset_overview: list[dict],
    news_payload: dict | None,
    weather_payloads: list[tuple[str, dict | None, str | None]],
) -> None:
    st.markdown("### Biểu đồ nhanh")
    render_html_block(
        """
        <section class="section-shell">
            <div class="section-kicker">Visual scan</div>
            <h3 class="section-title">
                Ba biểu đồ nhỏ để nhìn nhanh dữ liệu thay vì đọc nhiều chữ
            </h3>
            <p class="section-copy">
                Các biểu đồ này chỉ dùng dữ liệu đang hiển thị trên dashboard,
                phù hợp cho demo nhanh.
            </p>
        </section>
        """
    )
    left_col, center_col, right_col = st.columns(3, gap="large")
    with left_col:
        dataset_chart = build_dataset_overview_chart_frame(dataset_overview)
        st.caption("Quy mô theo pipeline")
        if dataset_chart.empty:
            st.info("Chưa có dữ liệu để vẽ biểu đồ.")
        else:
            st.bar_chart(
                dataset_chart.set_index("Nhóm dữ liệu")["Số bản ghi"],
                height=240,
                width="stretch",
            )
    with center_col:
        source_chart = build_news_source_chart_frame((news_payload or {}).get("items", []))
        st.caption("Nguồn trong cụm tin hot")
        if source_chart.empty:
            st.info("Chưa có dữ liệu tin hot để vẽ biểu đồ.")
        else:
            st.bar_chart(
                source_chart.set_index("Nguồn")["Số bài"],
                height=240,
                width="stretch",
            )
    with right_col:
        weather_chart = build_weather_chart_frame(weather_payloads)
        st.caption("Biên độ nhiệt độ theo điểm")
        if weather_chart.empty:
            st.info("Chưa có dữ liệu thời tiết để vẽ biểu đồ.")
        else:
            st.line_chart(
                weather_chart.set_index("Địa điểm")[["Nhiệt độ thấp", "Nhiệt độ cao"]],
                height=240,
                width="stretch",
            )


def render_dashboard_ai_panel() -> None:
    render_html_block(
        """
        <section class="section-shell">
            <div class="section-kicker">Trợ lý AI</div>
            <h3 class="section-title">Đi nhanh sang khu hỏi đáp nếu muốn kể chuyện bằng dữ liệu</h3>
            <p class="section-copy">
                Phần này dành cho demo hội thoại. Bạn có thể mở workspace Trợ lý AI
                hoặc đẩy sẵn một câu hỏi mẫu để bắt đầu ngay.
            </p>
        </section>
        """
    )
    prompts = [
        "Tin hot hôm nay là gì?",
        "Giá vàng SJC hôm nay bao nhiêu?",
        "Có chính sách mới nào về giáo dục không?",
    ]
    for index, prompt in enumerate(prompts):
        if st.button(
            prompt,
            key=f"dashboard_ai_prompt_{index}",
            width="stretch",
        ):
            prepare_chat_draft(prompt)
            st.rerun()
    if st.button("Mở workspace Trợ lý AI", key="dashboard_ai_workspace", width="stretch"):
        queue_navigation("assistant")
        st.rerun()


def render_dashboard_workspace(
    *,
    health_payload: dict | None,
    health_error: str | None,
    news_payload: dict | None,
    news_error: str | None,
    price_payload: dict | None,
    price_error: str | None,
    weather_payloads: list[tuple[str, dict | None, str | None]],
    policy_payload: dict | None,
    policy_error: str | None,
    traffic_payload: dict | None,
    traffic_error: str | None,
    dataset_overview: list[dict],
    dataset_overview_error: str | None,
) -> None:
    data_mode_label, _ = summarize_sidebar_runtime(
        dataset_overview,
        news_payload,
        price_payload,
        policy_payload,
        traffic_payload,
    )
    render_page_header(
        kicker="Dashboard",
        title="Tổng quan nhanh về dữ liệu và tín hiệu nổi bật trong ngày",
        description=(
            "Khu này ưu tiên cho giảng viên, hội đồng hoặc người xem lần đầu: "
            "thấy ngay hệ thống làm gì, dữ liệu nào đang nổi bật "
            "và cách đi tiếp sang AI hoặc Explorer."
        ),
        badges=[
            ("Dữ liệu", data_mode_label),
            ("API", format_api_base_label(API_BASE_URL)),
            ("Database", format_database_driver_label(
                health_payload.get("database_driver") if health_payload else None
            )),
        ],
    )
    render_detail_panel()

    intro_col, ai_col = st.columns([1.18, 0.82], gap="large")
    with intro_col:
        render_quick_start()
    with ai_col:
        render_dashboard_ai_panel()

    st.write("")
    render_data_volume_board(dataset_overview, dataset_overview_error)

    st.write("")
    render_dashboard_quick_charts(
        dataset_overview,
        news_payload,
        weather_payloads,
    )

    st.write("")
    dashboard_tabs = st.tabs(
        ["Tin tức & điều phối", "Giá & thời tiết", "Chính sách & giao thông"]
    )

    with dashboard_tabs[0]:
        top_left, top_right = st.columns([1.28, 0.92], gap="large")
        with top_left:
            render_news_board(news_payload, news_error)
            render_section_actions(
                key_prefix="news",
                dataset_title="Tin tức",
                suggested_question="Tin hot hôm nay là gì?",
            )
        with top_right:
            render_overview_board(
                health_payload,
                health_error,
                news_payload,
                price_payload,
                weather_payloads,
            )

    with dashboard_tabs[1]:
        market_col, weather_col = st.columns([1.0, 1.0], gap="large")
        with market_col:
            render_price_cards(price_payload, price_error)
            render_section_actions(
                key_prefix="price",
                dataset_title="Giá cả",
                suggested_question="Giá vàng SJC hôm nay bao nhiêu?",
            )
        with weather_col:
            render_weather_cards(weather_payloads)
            render_section_actions(
                key_prefix="weather",
                dataset_title="Thời tiết",
                suggested_question="Thời tiết Hải Phòng hôm nay thế nào?",
            )

    with dashboard_tabs[2]:
        policy_col, traffic_col = st.columns([1.0, 1.0], gap="large")
        with policy_col:
            render_policy_cards(policy_payload, policy_error)
            render_section_actions(
                key_prefix="policy",
                dataset_title="Chính sách",
                suggested_question="Có chính sách mới nào về giáo dục không?",
            )
        with traffic_col:
            render_traffic_cards(traffic_payload, traffic_error)
            render_section_actions(
                key_prefix="traffic",
                dataset_title="Giao thông",
                suggested_question="Có tuyến đường nào đang bị cấm không?",
            )

    st.write("")
    render_chat_hint()


def sort_price_items(price_payload: dict | None) -> list[dict]:
    items = (price_payload or {}).get("items", [])
    priority = {name: index for index, name in enumerate(PRICE_HIGHLIGHT_ORDER)}
    return sorted(
        items,
        key=lambda item: (
            priority.get(item.get("item_name", ""), len(priority)),
            item.get("display_name", item.get("item_name", "")),
        ),
    )


def render_price_cards(price_payload: dict | None, error_message: str | None) -> None:
    st.markdown("### Bảng giá nhanh")
    if error_message:
        st.error(f"Không tải được bảng giá: {error_message}")
        return

    items = sort_price_items(price_payload)
    if not items:
        st.info("Hiện chưa có dữ liệu giá.")
        return

    price_columns = st.columns(2)
    for index, item in enumerate(items[:4]):
        with price_columns[index % 2]:
            price_item = build_content_item("price", item)
            display_name = escape(str(price_item.get("title") or item.get("item_name")))
            source = escape(format_ui_source_label(str(price_item.get("source") or "price")))
            display_unit = escape(
                str((price_item.get("metadata") or {}).get("unit") or "Không có đơn vị")
            )
            effective_at = escape(format_datetime(str(price_item.get("updated_at") or "")))
            value = price_item.get("summary") or "Chưa có giá"
            card_html = f"""
            <div class="mini-card">
                <div class="mini-kicker">{source}</div>
                <div class="mini-title">{display_name}</div>
                <div class="mini-value">{escape(str(value).split(' · ')[0])}</div>
                <div class="mini-copy">
                    {display_unit}<br/>
                    Cập nhật: {effective_at}
                </div>
            </div>
            """
            render_html_block(card_html)
            render_item_actions(
                price_item,
                key_prefix=f"price_card_{index}",
                origin="dashboard",
                show_explorer=False,
                show_source=False,
                ai_label="Hỏi AI",
                ai_mode="ask",
                action_style="menu",
            )


def render_weather_cards(weather_payloads: list[tuple[str, dict | None, str | None]]) -> None:
    st.markdown("### Thời tiết theo điểm")
    chunk_size = 3
    for start_index in range(0, len(weather_payloads), chunk_size):
        row_payloads = weather_payloads[start_index : start_index + chunk_size]
        weather_columns = st.columns(len(row_payloads))
        for column, (location, payload, error_message) in zip(
            weather_columns,
            row_payloads,
            strict=False,
        ):
            with column:
                if error_message:
                    render_html_block(
                        f"""
                        <div class="mini-card">
                            <div class="mini-kicker">{escape(location)}</div>
                            <div class="mini-title">Không tải được dữ liệu</div>
                            <div class="mini-copy">{escape(error_message)}</div>
                        </div>
                        """
                    )
                    continue

                if not payload:
                    render_html_block(
                        f"""
                        <div class="mini-card">
                            <div class="mini-kicker">{escape(location)}</div>
                            <div class="mini-title">Chưa có dữ liệu</div>
                        </div>
                        """
                    )
                    continue

                weather_item = build_content_item("weather", payload)
                warning_text = (
                    (weather_item.get("metadata") or {}).get("warning_text")
                    or "Không có cảnh báo nổi bật"
                )
                source = escape(format_ui_source_label(str(weather_item.get("source") or location)))
                weather_text = escape(payload.get("weather_text") or "Chưa có mô tả")
                min_temp = escape(str(payload.get("min_temp", "?")))
                max_temp = escape(str(payload.get("max_temp", "?")))
                card_html = f"""
                <div class="mini-card">
                    <div class="mini-kicker">{source}</div>
                    <div class="mini-title">{escape(location)}</div>
                    <div class="mini-value">{min_temp} - {max_temp}°C</div>
                    <div class="mini-copy">
                        {weather_text}<br/>
                        {escape(warning_text)}
                    </div>
                </div>
                """
                render_html_block(card_html)
                render_item_actions(
                    weather_item,
                    key_prefix=f"weather_card_{location}",
                    origin="dashboard",
                    show_explorer=False,
                    show_source=False,
                    ai_label="Hỏi AI",
                    ai_mode="ask",
                    action_style="menu",
                )


def render_policy_cards(policy_payload: dict | None, error_message: str | None) -> None:
    st.markdown("### Chính sách mới")
    if error_message:
        st.error(f"Không tải được dữ liệu chính sách: {error_message}")
        return

    items = (policy_payload or {}).get("items", [])
    if not items:
        st.info("Hiện chưa có dữ liệu chính sách.")
        return

    for item in items[:4]:
        policy_item = build_content_item("policy", item)
        title = escape(str(policy_item.get("title") or "Chưa có tiêu đề"))
        summary = escape(shorten_preview_text(policy_item.get("summary"), limit=150))
        agency_value = (
            (policy_item.get("metadata") or {}).get("issuing_agency")
            or "Chưa rõ cơ quan"
        )
        agency = escape(str(agency_value))
        source = escape(format_ui_source_label(str(policy_item.get("source") or "policy")))
        meta = f"{agency} | {format_datetime(str(policy_item.get('updated_at') or ''))}"
        policy_html = f"""
        <article class="feature-card">
            <div class="mini-kicker">{source}</div>
            <div class="feature-title">
                {title}
            </div>
            <p class="feature-summary">{summary}</p>
            <div class="meta-line">{escape(meta)}</div>
        </article>
        """
        render_html_block(policy_html)
        render_item_actions(
            policy_item,
            key_prefix=f"policy_card_{item.get('id')}",
            origin="dashboard",
            show_explorer=False,
            show_source=False,
            action_style="menu",
        )


def render_traffic_cards(traffic_payload: dict | None, error_message: str | None) -> None:
    st.markdown("### Giao thông cần chú ý")
    if error_message:
        st.error(f"Không tải được dữ liệu giao thông: {error_message}")
        return

    items = (traffic_payload or {}).get("items", [])
    if not items:
        st.info("Hiện chưa có dữ liệu giao thông.")
        return

    for item in items[:4]:
        traffic_item = build_content_item("traffic", item)
        title = escape(str(traffic_item.get("title") or "Chưa có tiêu đề"))
        description = escape(shorten_preview_text(traffic_item.get("summary"), limit=150))
        location_value = (traffic_item.get("metadata") or {}).get("location") or "Chưa rõ địa điểm"
        location = escape(str(location_value))
        source = escape(format_ui_source_label(str(traffic_item.get("source") or "traffic")))
        meta = f"{location} | {format_datetime(str(traffic_item.get('updated_at') or ''))}"
        traffic_html = f"""
        <article class="feature-card">
            <div class="mini-kicker">{source}</div>
            <div class="feature-title">
                {title}
            </div>
            <p class="feature-summary">{description}</p>
            <div class="meta-line">{escape(meta)}</div>
        </article>
        """
        render_html_block(traffic_html)
        render_item_actions(
            traffic_item,
            key_prefix=f"traffic_card_{item.get('id')}",
            origin="dashboard",
            show_explorer=False,
            show_source=False,
            action_style="menu",
        )


def ensure_chat_state() -> None:
    st.session_state.setdefault("chat_messages", build_default_chat_messages())
    st.session_state.setdefault("chat_feedback", None)
    st.session_state.setdefault("pending_chat_question", None)


def queue_chat_question(
    question: str,
    *,
    mode: str = "default",
    context_item: dict | None = None,
) -> None:
    clean_question = question.strip()
    if not clean_question:
        st.session_state["chat_feedback"] = ("warning", "Bạn cần nhập câu hỏi trước khi gửi.")
        return

    st.session_state["chat_feedback"] = None
    st.session_state["pending_chat_question"] = clean_question
    st.session_state["pending_chat_request"] = build_chat_request(
        clean_question,
        mode=mode,
        context_item=context_item,
    )


def process_pending_chat_question() -> None:
    pending_question = st.session_state.get("pending_chat_question")
    if not pending_question:
        return

    ensure_pending_user_visible(st.session_state["chat_messages"], pending_question)
    request_payload = st.session_state.get("pending_chat_request") or {"question": pending_question}

    try:
        answer_payload = post_json("/chat/query", request_payload)
        answer = answer_payload.get("answer", "Chưa có câu trả lời.")
        meta = build_chat_meta(answer_payload)
        intent = answer_payload.get("intent", "unknown")
        follow_ups = get_follow_up_suggestions(
            intent,
            current_question=pending_question,
        )
        response_items = answer_payload.get("items") or []
    except Exception as exc:
        answer = f"Không gọi được chat API: {exc}"
        meta = "Kiểm tra lại API local hoặc quota OpenAI nếu đang bật path OpenAI."
        intent = "unknown"
        follow_ups = get_follow_up_suggestions(
            "unknown",
            current_question=pending_question,
        )
        response_items = []

    append_chat_message(
        st.session_state["chat_messages"],
        "assistant",
        answer,
        meta,
        intent=intent,
        follow_ups=follow_ups,
        items=response_items,
    )
    st.session_state["pending_chat_question"] = None
    st.session_state["pending_chat_request"] = None


def render_chat_intro() -> None:
    render_html_block(
        """
        <div class="section-shell">
            <div class="section-kicker">Hỏi đáp nhanh</div>
            <div class="mini-title">
                Hỏi tự nhiên, hệ thống sẽ tự chọn đúng intent và nguồn dữ liệu
            </div>
            <div class="mini-copy">
                Bạn có thể hỏi theo ngôn ngữ thường ngày như hỏi tin hot, giá vàng,
                thời tiết, chính sách hoặc giao thông. Nếu OpenAI không sẵn sàng,
                agent nội bộ vẫn giữ được luồng trả lời.
            </div>
        </div>
        """
    )


def render_chat_suggestion_groups(*, key_prefix: str = "chat") -> None:
    tabs = st.tabs([group.label for group in CHAT_SUGGESTION_GROUPS])
    for tab, group in zip(tabs, CHAT_SUGGESTION_GROUPS, strict=False):
        with tab:
            st.caption(f"Gợi ý nhanh cho nhóm {group.label.lower()}")
            for prompt_index, prompt in enumerate(group.prompts):
                if st.button(
                    prompt,
                    key=f"{key_prefix}_prompt_{group.label}_{prompt_index}",
                    width="stretch",
                ):
                    queue_chat_question(prompt)
                    st.rerun()


def render_recent_chat_questions(*, key_prefix: str = "chat") -> None:
    recent_questions = extract_recent_user_questions(
        st.session_state["chat_messages"],
        limit=3,
    )
    if not recent_questions:
        return

    st.caption("Câu hỏi gần đây")
    for index, question in enumerate(recent_questions):
        if st.button(
            question,
            key=f"{key_prefix}_recent_question_{index}",
            width="stretch",
        ):
            queue_chat_question(question)
            st.rerun()


def render_follow_up_buttons(
    message: dict,
    *,
    message_index: int,
    key_prefix: str = "chat",
) -> None:
    follow_ups = message.get("follow_ups") or []
    if not follow_ups:
        return

    st.caption("Bạn có thể hỏi tiếp")
    for prompt_index, prompt in enumerate(follow_ups):
        if st.button(
            prompt,
            key=f"{key_prefix}_followup_{message_index}_{prompt_index}",
            width="stretch",
        ):
            queue_chat_question(prompt)
            st.rerun()


def render_chat_result_items(
    message: dict,
    *,
    message_index: int,
    key_prefix: str = "chat",
) -> None:
    items = message.get("items") or []
    if not items:
        return

    st.caption("Mục liên quan")
    for item_index, item in enumerate(items[:3]):
        source_label = format_ui_source_label(str(item.get("source") or ""))
        title = escape(str(item.get("title") or "Mục dữ liệu"))
        summary = escape(shorten_preview_text(item.get("summary"), limit=130))
        updated_at = escape(format_datetime(str(item.get("updated_at") or "")))
        render_html_block(
            f"""
            <div class="chat-result-card">
                <div class="mini-kicker">{escape(source_label)}</div>
                <p class="chat-result-title">{title}</p>
                <p class="chat-result-summary">{summary}</p>
                <div class="meta-line">{updated_at}</div>
            </div>
            """
        )
        render_item_actions(
            item,
            key_prefix=f"{key_prefix}_item_{message_index}_{item_index}",
            origin="assistant",
            show_explorer=False,
            show_source=bool(item.get("url")),
            ai_label="Tóm tắt lại",
            action_style="menu",
            menu_label="Thao tác ▼",
            button_width="content",
        )


def render_chat_messages(*, key_prefix: str = "chat") -> None:
    visible_messages = st.session_state["chat_messages"][-CHAT_HISTORY_LIMIT:]
    latest_assistant_index = max(
        (
            index
            for index, message in enumerate(visible_messages)
            if message["role"] == "assistant"
        ),
        default=-1,
    )

    for index, message in enumerate(visible_messages):
        with st.chat_message(message["role"]):
            role_label = "Bạn" if message["role"] == "user" else "Trợ lý"
            render_html_block(
                f"""
                <div class="chat-role-label {escape(message['role'])}">
                    {escape(role_label)}
                </div>
                """
            )
            st.markdown(message["content"])
            footer_parts = []
            if message.get("timestamp"):
                footer_parts.append(str(message["timestamp"]))
            if message.get("meta"):
                footer_parts.append(str(message["meta"]))
            if footer_parts:
                st.caption(" • ".join(footer_parts))
            if message["role"] == "assistant":
                render_chat_result_items(
                    message,
                    message_index=index,
                    key_prefix=key_prefix,
                )
            if (
                message["role"] == "assistant"
                and index == latest_assistant_index
            ):
                render_follow_up_buttons(
                    message,
                    message_index=index,
                    key_prefix=key_prefix,
                )


def render_pending_chat_response(*, key_prefix: str = "chat") -> None:
    pending_question = st.session_state.get("pending_chat_question")
    if not pending_question:
        return

    ensure_pending_user_visible(st.session_state["chat_messages"], pending_question)
    render_chat_messages(key_prefix=key_prefix)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm thông tin phù hợp trong dữ liệu hiện có..."):
            process_pending_chat_question()
            latest_message = st.session_state["chat_messages"][-1]
        st.markdown(latest_message["content"])
        if latest_message.get("meta"):
            st.caption(latest_message["meta"])

    st.rerun()


def render_chat_form(
    *,
    form_key: str,
    input_key: str,
    submit_label: str,
) -> None:
    with st.form(form_key, clear_on_submit=True):
        question = st.text_area(
            "Nhập câu hỏi",
            height=88,
            key=input_key,
            label_visibility="collapsed",
            placeholder=(
                "Ví dụ: Có cảnh báo thời tiết nào không, "
                "hoặc giá vàng SJC hôm nay bao nhiêu?"
            ),
        )
        submitted = st.form_submit_button(submit_label)

    feedback = st.session_state.get("chat_feedback")
    if feedback:
        feedback_type, feedback_message = feedback
        getattr(st, feedback_type)(feedback_message)

    if submitted:
        queue_chat_question(question)
        st.rerun()


def render_chat_assistant() -> None:
    ensure_chat_state()
    chat_popover = getattr(st, "popover", None)
    if chat_popover is None:
        st.markdown("### Trợ lý AI")
        st.info(
            "Streamlit hiện tại chưa hỗ trợ popover. "
            "Bạn có thể dùng hộp chat mặc định bên dưới."
        )
        return

    with chat_popover("Mở trợ lý AI", help="Mở trợ lý AI"):
        st.markdown("#### Trợ lý AI nhanh")
        st.caption(
            "Popover này dùng cho thao tác nhanh. Muốn hội thoại đầy đủ hơn, "
            "mở khu `Trợ lý AI` ở sidebar."
        )
        for index, prompt in enumerate(flatten_chat_suggestions()[:4]):
            if st.button(
                prompt,
                key=f"floating_chat_prompt_{index}",
                width="stretch",
            ):
                queue_chat_question(prompt)
                st.rerun()
        render_recent_chat_questions(key_prefix="popover")
        st.write("")
        if st.session_state.get("pending_chat_question"):
            render_pending_chat_response(key_prefix="popover")
        else:
            render_chat_messages(key_prefix="popover")

        utility_columns = st.columns([1.1, 1], gap="small")
        with utility_columns[0]:
            if st.button("Xóa hội thoại", key="clear_chat_history", width="stretch"):
                reset_chat_messages(st.session_state["chat_messages"])
                st.session_state["pending_chat_question"] = None
                st.session_state["pending_chat_request"] = None
                st.session_state["chat_feedback"] = (
                    "success",
                    "Đã đặt lại hội thoại về trạng thái mặc định.",
                )
                st.rerun()
        with utility_columns[1]:
            if st.button("Mở workspace AI", key="popover_to_ai_workspace", width="stretch"):
                queue_navigation("assistant")
                st.rerun()

        render_chat_form(
            form_key="popover_chat_form",
            input_key="floating_chat_input",
            submit_label="Gửi nhanh",
        )


def render_chat_hint() -> None:
    st.markdown("### Trợ lý AI nổi")
    render_html_block(
        """
        <div class="card-surface">
            <div class="section-kicker">Chat</div>
            <div class="mini-title">Avatar chat luôn sẵn ở góc phải màn hình.</div>
            <div class="mini-copy">
                Avatar này có bubble nhắc sẵn ở bên ngoài. Bấm vào để hỏi trực tiếp
                về tin hot, giá vàng, thời tiết, chính sách hoặc giao thông mà không
                làm rối phần dashboard chính.
            </div>
        </div>
        """
    )


def render_ai_workspace(health_payload: dict | None) -> None:
    render_page_header(
        kicker="Trợ lý AI",
        title="Workspace hỏi đáp trung tâm cho dữ liệu hằng ngày",
        description=(
            "Khu này biến AI thành trung tâm trải nghiệm. Bạn có thể hỏi tự nhiên, "
            "xem lịch sử hội thoại rõ ràng và nhận gợi ý tiếp theo theo từng intent."
        ),
        badges=[
            ("Chat", "OpenAI + fallback" if settings.chat_use_openai else "Agent nội bộ"),
            ("Retrieval", "Bật" if settings.experimental_retrieval_enabled else "Tắt"),
            ("Database", format_database_driver_label(
                health_payload.get("database_driver") if health_payload else None
            )),
        ],
    )
    render_detail_panel()
    ensure_chat_state()
    chat_col, support_col = st.columns([1.35, 0.65], gap="large")

    with chat_col:
        render_html_block(
            """
            <section class="section-shell">
                <div class="section-kicker">Conversation</div>
                <h3 class="section-title">Hỏi trực tiếp bằng tiếng Việt trên dữ liệu đã ingest</h3>
                <p class="section-copy">
                    Lịch sử chat ở đây dùng chung với avatar nổi.
                    Vì vậy bạn có thể bắt đầu từ dashboard
                    rồi tiếp tục hội thoại ở workspace này mà không mất ngữ cảnh.
                </p>
            </section>
            """
        )
        if st.session_state.get("pending_chat_question"):
            render_pending_chat_response(key_prefix="assistant")
        else:
            render_chat_messages(key_prefix="assistant")

        utility_columns = st.columns([1.05, 1], gap="small")
        with utility_columns[0]:
            if st.button("Xóa hội thoại", key="assistant_clear_chat", width="stretch"):
                reset_chat_messages(st.session_state["chat_messages"])
                st.session_state["pending_chat_question"] = None
                st.session_state["pending_chat_request"] = None
                st.session_state["chat_feedback"] = (
                    "success",
                    "Đã đặt lại hội thoại về trạng thái mặc định.",
                )
                st.rerun()
        with utility_columns[1]:
            if st.button("Mở Explorer", key="assistant_to_explorer", width="stretch"):
                latest_item = get_latest_clickable_item(st.session_state["chat_messages"])
                if latest_item:
                    open_item_in_explorer(latest_item)
                else:
                    switch_to_data_browser("Tin tức")
                st.rerun()
        render_chat_form(
            form_key="assistant_chat_form",
            input_key="assistant_chat_input",
            submit_label="Gửi vào trợ lý",
        )

    with support_col:
        render_chat_intro()
        st.write("")
        render_chat_suggestion_groups(key_prefix="assistant")
        st.write("")
        render_recent_chat_questions(key_prefix="assistant")
        render_html_block(
            """
            <section class="section-shell">
                <div class="section-kicker">Bạn có thể hỏi gì</div>
                <h3 class="section-title">Các nhóm câu hỏi đang được hỗ trợ tốt nhất</h3>
                <p class="section-copy">
                    Tin hot, giá vàng, tỷ giá, thời tiết theo địa điểm, văn bản chính sách
                    và giao thông đều đã có intent riêng trong agent hiện tại.
                </p>
            </section>
            """
        )


def render_data_browser(*, technical_scope: bool = False) -> None:
    scope_label = "Bảng kỹ thuật" if technical_scope else "Dữ liệu nghiệp vụ"
    dataset_title_key = browser_state_key("dataset_title", technical_scope=technical_scope)
    keyword_key = browser_state_key("keyword", technical_scope=technical_scope)
    row_limit_key = browser_state_key("row_limit", technical_scope=technical_scope)
    sort_label_key = browser_state_key("sort_label", technical_scope=technical_scope)
    st.markdown("### Data Explorer")
    render_html_block(
        """
        <section class="section-shell">
            <div class="section-kicker">Tra cứu sâu hơn</div>
            <h3 class="section-title">Explorer cho phép lọc dữ liệu mà không cần viết SQL</h3>
            <p class="section-copy">
                Chọn đúng nhóm dữ liệu, sau đó lọc theo nguồn, địa điểm hoặc item.
                Khu này phục vụ cả nhu cầu demo dữ liệu nghiệp vụ lẫn debug kỹ thuật nhẹ.
            </p>
        </section>
        """
    )
    st.caption(f"Phạm vi hiện tại: {scope_label}")

    dataset_options = list_dataset_definitions(
        include_technical=technical_scope,
        technical_only=technical_scope,
    )
    dataset_map = {dataset.title: dataset for dataset in dataset_options}
    if st.session_state.get(dataset_title_key) not in dataset_map:
        st.session_state[dataset_title_key] = next(iter(dataset_map))

    control_left, control_center, control_right = st.columns([1.2, 1.1, 0.7], gap="large")
    with control_left:
        selected_title = st.selectbox(
            "Chọn nhóm dữ liệu",
            options=list(dataset_map.keys()),
            key=dataset_title_key,
        )
    with control_center:
        keyword = st.text_input(
            "Lọc nhanh theo từ khóa",
            placeholder="Ví dụ: Hà Nội, giáo dục, SJC, VnExpress...",
            key=keyword_key,
        )
    with control_right:
        row_limit = st.slider(
            "Số dòng",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            key=row_limit_key,
        )

    selected_dataset = dataset_map[selected_title]
    base_payload = load_dataset_preview(
        selected_dataset.key,
        limit=row_limit,
        include_technical=technical_scope,
    )
    filter_options = {
        item["field"]: item
        for item in base_payload.get("filter_options", [])
    }
    sort_label_map = {
        "Mới nhất trước": "latest",
        "Cũ nhất trước": "oldest",
    }
    if st.session_state.get(sort_label_key) not in sort_label_map:
        st.session_state[sort_label_key] = "Mới nhất trước"
    selected_sort_label = st.selectbox(
        "Sắp xếp",
        options=list(sort_label_map.keys()),
        key=sort_label_key,
    )
    sort_mode = sort_label_map[selected_sort_label]

    filter_columns = st.columns(4, gap="small")
    for column, field in zip(
        filter_columns,
        BROWSER_FILTER_FIELDS,
        strict=False,
    ):
        option_bundle = filter_options.get(field)
        options = option_bundle["options"] if option_bundle else ["Tất cả"]
        key = browser_state_key(f"filter_{field}", technical_scope=technical_scope)
        if st.session_state.get(key) not in options:
            st.session_state[key] = "Tất cả"
        with column:
            st.selectbox(
                option_bundle["label"] if option_bundle else field,
                options=options,
                key=key,
                disabled=option_bundle is None,
            )

    structured_filters = {
        field: st.session_state.get(
            browser_state_key(f"filter_{field}", technical_scope=technical_scope),
            "Tất cả",
        )
        for field in filter_options
    }
    payload = load_dataset_preview(
        selected_dataset.key,
        limit=row_limit,
        keyword=keyword,
        structured_filters=structured_filters,
        sort_mode=sort_mode,
        include_technical=technical_scope,
    )

    info_html = f"""
    <div class="section-shell">
        <div class="section-kicker">Khám phá dữ liệu</div>
        <div class="mini-title">{escape(payload['title'])}</div>
        <div class="mini-copy">{escape(payload['description'])}</div>
        <div class="chip-row">
            {build_status_chip("Tổng số dòng", str(payload['total_rows']))}
            {build_status_chip("Khớp bộ lọc", str(payload['matched_rows']))}
            {build_status_chip("Đang hiển thị", str(len(payload['records'])))}
        </div>
    </div>
    """
    render_html_block(info_html)

    records = payload["records"]
    if not records:
        st.info("Không có bản ghi nào khớp bộ lọc hiện tại.")
        return

    dataframe = pd.DataFrame(records)
    display_columns = [column for column in payload["columns"] if column in dataframe.columns]
    if display_columns:
        dataframe = dataframe[display_columns]

    st.dataframe(dataframe, width="stretch", height=420)
    detail_item = None
    if selected_dataset.key in {
        "articles",
        "price_snapshots",
        "weather_snapshots",
        "policy_documents",
        "traffic_events",
    }:
        detail_choice_key = browser_state_key("detail_record", technical_scope=technical_scope)
        picker_options = {
            build_record_picker_label(selected_dataset.key, record): record
            for record in records[: min(len(records), 20)]
        }
        if st.session_state.get(detail_choice_key) not in {"", *picker_options.keys()}:
            st.session_state[detail_choice_key] = ""
        selected_record_label = st.selectbox(
            "Chọn một bản ghi trong preview để xem kỹ hơn",
            options=["", *picker_options.keys()],
            key=detail_choice_key,
        )
        if selected_record_label:
            detail_item = build_content_item_from_dataset_record(
                selected_dataset.key,
                picker_options[selected_record_label],
            )

    if detail_item:
        detail_source = escape(format_ui_source_label(str(detail_item.get("source") or "")))
        detail_title = escape(str(detail_item.get("title") or "Bản ghi chi tiết"))
        detail_summary = escape(shorten_preview_text(detail_item.get("summary"), limit=210))
        detail_updated = escape(format_datetime(str(detail_item.get("updated_at") or "")))
        render_html_block(
            f"""
            <div class="feature-card">
                <div class="mini-kicker">{detail_source}</div>
                <div class="feature-title">{detail_title}</div>
                <p class="feature-summary">{detail_summary}</p>
                <div class="meta-line">{detail_updated}</div>
            </div>
            """
        )
        render_item_actions(
            detail_item,
            key_prefix=f"explorer_detail_{selected_dataset.key}",
            origin="explorer",
            show_explorer=False,
            show_source=bool(detail_item.get("url")),
            action_style="menu",
        )

    st.download_button(
        label="Tải CSV preview",
        data=dataframe.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_dataset.key}_preview.csv",
        mime="text/csv",
    )


def render_explorer_workspace(dataset_overview: list[dict]) -> None:
    counts = dataset_count_map(dataset_overview)
    render_page_header(
        kicker="Explorer",
        title="Tra cứu dữ liệu chi tiết theo nhóm nghiệp vụ hoặc bảng kỹ thuật",
        description=(
            "Khu Explorer dành cho người cần đối chiếu nguồn, lọc dữ liệu cụ thể, "
            "xem bản ghi gần nhất hoặc xuất CSV preview để dùng tiếp."
        ),
        badges=[
            ("Tin tức", format_record_count(counts.get("articles", 0))),
            ("Giá", format_record_count(counts.get("price_snapshots", 0))),
            ("Traffic", format_record_count(counts.get("traffic_events", 0))),
        ],
    )
    render_detail_panel()
    explorer_tabs = st.tabs(["Dữ liệu nghiệp vụ", "Bảng kỹ thuật"])
    with explorer_tabs[0]:
        render_data_browser(technical_scope=False)
    with explorer_tabs[1]:
        render_data_browser(technical_scope=True)


def render_system_operator_panel() -> None:
    render_html_block(
        """
        <section class="section-shell">
            <div class="section-kicker">Runbook nhanh</div>
            <h3 class="section-title">Các lệnh thao tác local thường dùng</h3>
            <p class="section-copy">
                Đây là nhóm lệnh thao tác an toàn cho demo local khi cần làm mới dữ liệu
                hoặc kiểm tra scheduler mà không phải tra README.
            </p>
        </section>
        """
    )
    st.code(".venv/bin/python scripts/refresh_live_data.py", language="bash")
    st.code(".venv/bin/python scripts/run_scheduler.py --run-once", language="bash")
    st.code(".venv/bin/python scripts/run_cleanup.py", language="bash")


def render_system_workspace(
    *,
    health_payload: dict | None,
    health_error: str | None,
    dataset_overview: list[dict],
    dataset_overview_error: str | None,
) -> None:
    render_page_header(
        kicker="Hệ thống",
        title="Runtime status, scheduler health và góc nhìn vận hành",
        description=(
            "Phần này tách riêng hoàn toàn khỏi dashboard chính để người kỹ thuật kiểm tra "
            "database runtime, trạng thái source, scheduler và dữ liệu nền "
            "mà không làm rối phần demo."
        ),
        badges=[
            ("Database", format_database_driver_label(
                health_payload.get("database_driver") if health_payload else None
            )),
            ("Chat", "OpenAI + fallback" if settings.chat_use_openai else "Agent nội bộ"),
            ("Retrieval", "Bật" if settings.experimental_retrieval_enabled else "Tắt"),
        ],
    )
    top_left, top_right = st.columns([0.9, 1.1], gap="large")
    with top_left:
        render_system_status(health_payload, health_error)
    with top_right:
        render_source_health()

    st.write("")
    bottom_left, bottom_right = st.columns([1.0, 0.9], gap="large")
    with bottom_left:
        render_data_volume_board(dataset_overview, dataset_overview_error)
    with bottom_right:
        render_system_operator_panel()


st.set_page_config(
    page_title="Tin tức + AI hỏi đáp",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_styles()
ensure_ui_state()
apply_pending_navigation_request()

selected_nav_label = st.session_state.get("nav_section_widget")
if isinstance(selected_nav_label, str) and selected_nav_label in navigation_labels():
    active_section_hint = navigation_key_from_label(selected_nav_label)
else:
    active_section_hint = st.session_state.get("nav_section", "dashboard")

health_payload, health_error = fetch_payload("/health")
news_payload = None
news_error = None
price_payload = None
price_error = None
policy_payload = None
policy_error = None
traffic_payload = None
traffic_error = None
weather_payloads = build_empty_weather_payloads()

if should_load_dashboard_payloads(active_section_hint):
    news_payload, news_error = fetch_payload("/news/hot", params={"limit": 10})
    price_payload, price_error = fetch_payload("/prices/latest")
    policy_payload, policy_error = fetch_payload("/policies/search", params={"limit": 4})
    traffic_payload, traffic_error = fetch_payload("/traffic/latest", params={"limit": 4})
    weather_payloads = fetch_weather_payloads()

try:
    dataset_overview = load_core_dataset_overview()
    dataset_overview_error = None
except Exception as exc:
    dataset_overview = []
    dataset_overview_error = str(exc)

data_mode_label, data_mode_copy = summarize_sidebar_runtime(
    dataset_overview,
    news_payload,
    price_payload,
    policy_payload,
    traffic_payload,
)
active_section = render_sidebar_navigation(
    health_payload,
    dataset_overview,
    data_mode_label=data_mode_label,
    data_mode_copy=data_mode_copy,
)

if active_section == "dashboard":
    render_hero(health_payload, dataset_overview)
    st.write("")
    render_dashboard_workspace(
        health_payload=health_payload,
        health_error=health_error,
        news_payload=news_payload,
        news_error=news_error,
        price_payload=price_payload,
        price_error=price_error,
        weather_payloads=weather_payloads,
        policy_payload=policy_payload,
        policy_error=policy_error,
        traffic_payload=traffic_payload,
        traffic_error=traffic_error,
        dataset_overview=dataset_overview,
        dataset_overview_error=dataset_overview_error,
    )
elif active_section == "assistant":
    render_ai_workspace(health_payload)
elif active_section == "explorer":
    render_explorer_workspace(dataset_overview)
else:
    render_system_workspace(
        health_payload=health_payload,
        health_error=health_error,
        dataset_overview=dataset_overview,
        dataset_overview_error=dataset_overview_error,
    )

render_chat_assistant()
