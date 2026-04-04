from __future__ import annotations

from datetime import datetime
from html import escape

import httpx
import streamlit as st

from app.core.settings import get_settings
from app.ui.chat_state import (
    append_chat_message,
    build_chat_meta,
    ensure_pending_user_visible,
)

settings = get_settings()
API_BASE_URL = settings.api_base_url
PRICE_HIGHLIGHT_ORDER = [
    "gia-vang-sjc",
    "gia-vang-nhan-9999",
    "ty-gia-usd-ban-ra",
    "gia-xang-ron95-iii",
]
WEATHER_LOCATIONS = ["Hà Nội", "TP.HCM", "Đà Nẵng"]
CHAT_SUGGESTIONS = [
    "Tin hot hôm nay là gì?",
    "Giá vàng SJC hôm nay bao nhiêu?",
    "Có cảnh báo thời tiết nào không?",
    "Có chính sách mới nào về giáo dục không?",
]
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


def format_datetime(value: str | None) -> str:
    if not value:
        return "Chưa có thời điểm"
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).strftime("%H:%M %d/%m/%Y")
    except ValueError:
        return value


def render_styles() -> None:
    styles = """
        <style>
        :root {
            --bg: #f5ecde;
            --ink: #1e1d1a;
            --muted: #655d52;
            --paper: rgba(255, 250, 242, 0.82);
            --line: rgba(102, 84, 62, 0.18);
            --accent: #c65a1e;
            --accent-soft: #f3d7bf;
            --support: #1e6a73;
            --support-soft: #d9edf0;
            --shadow: 0 20px 60px rgba(73, 48, 24, 0.12);
            --radius-lg: 28px;
            --radius-md: 20px;
            --chat-avatar: url("__CHAT_AVATAR_DATA__");
        }

        html, body, [class*="css"] {
            font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(243, 215, 191, 0.8), transparent 32%),
                radial-gradient(circle at top right, rgba(217, 237, 240, 0.9), transparent 28%),
                linear-gradient(180deg, #fbf6ef 0%, #f5ecde 100%);
            color: var(--ink);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stAppViewContainer"] > .main {
            padding-top: 1.4rem;
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
        }

        .feature-summary {
            margin: 0 0 0.8rem;
            color: var(--muted);
            font-size: 0.95rem;
            line-height: 1.6;
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
        }

        .mini-kicker {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--support);
            font-weight: 800;
        }

        .mini-title {
            margin-top: 0.55rem;
            font-size: 1rem;
            font-weight: 800;
            line-height: 1.35;
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

        @media (max-width: 900px) {
            .hero-shell {
                padding: 1.4rem 1.2rem;
            }

            .stat-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 760px) {
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
    st.markdown(
        styles.replace("__CHAT_AVATAR_DATA__", CHAT_AVATAR_DATA),
        unsafe_allow_html=True,
    )


def build_status_chip(label: str, value: str) -> str:
    return f"<span class='status-chip'>{escape(label)} <strong>{escape(value)}</strong></span>"


def render_hero(health_payload: dict | None) -> None:
    db_driver = (
        health_payload.get("database_driver", "unknown")
        if health_payload
        else "không kết nối"
    )
    retrieval_label = "bật" if settings.experimental_retrieval_enabled else "tắt"
    chat_label = "OpenAI + fallback" if settings.chat_use_openai else "agent nội bộ"
    hero_html = f"""
    <section class="hero-shell">
        <span class="hero-eyebrow">Dashboard local cho 5 pipeline</span>
        <h1 class="hero-title">
            Tin tức, dữ liệu cấu trúc và AI hỏi đáp trong một giao diện gọn hơn.
        </h1>
        <p class="hero-copy">
            Trang này lấy dữ liệu trực tiếp từ API local, giữ nguyên flow ingestion
            và chat hiện tại. Bạn có thể xem nhanh tin hot, bảng giá, thời tiết
            và mở trợ lý AI từ nút tròn ở góc phải.
        </p>
        <div class="chip-row">
            {build_status_chip("Database", db_driver)}
            {build_status_chip("Retrieval experimental", retrieval_label)}
            {build_status_chip("Chế độ chat", chat_label)}
            {build_status_chip("API", API_BASE_URL)}
        </div>
    </section>
    """
    st.markdown(hero_html, unsafe_allow_html=True)


def render_news_cards(news_payload: dict | None, error_message: str | None) -> None:
    st.markdown("### Tin đáng chú ý")
    if error_message:
        st.error(f"Không tải được tin hot: {error_message}")
        return

    items = (news_payload or {}).get("items", [])
    if not items:
        st.info("Hiện chưa có dữ liệu tin hot.")
        return

    for item in items[:5]:
        summary = item.get("summary") or "Chưa có tóm tắt ngắn."
        canonical_url = escape(item["canonical_url"])
        title = escape(item["title"])
        source = escape(item.get("source", "unknown"))
        published_at = escape(format_datetime(item.get("published_at")))
        card_html = f"""
        <article class="feature-card">
            <div class="feature-title">
                <a href="{canonical_url}" target="_blank">{title}</a>
            </div>
            <p class="feature-summary">{escape(summary)}</p>
            <div class="meta-line">{source} | {published_at}</div>
        </article>
        """
        st.markdown(card_html, unsafe_allow_html=True)


def render_status_panel(health_payload: dict | None, health_error: str | None) -> None:
    st.markdown("### Trạng thái hệ thống")
    if health_error:
        st.error(f"Không đọc được /health: {health_error}")
        return

    if not health_payload:
        st.info("Chưa có dữ liệu health.")
        return

    openai_status = "Bật" if settings.chat_use_openai else "Tắt"
    retrieval_status = "Bật" if settings.experimental_retrieval_enabled else "Tắt"
    database_driver = escape(health_payload.get("database_driver", "unknown"))
    stat_html = f"""
    <div class="card-surface">
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">Runtime DB</div>
                <div class="stat-value">{database_driver}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">API health</div>
                <div class="stat-value">{escape(health_payload.get("status", "unknown"))}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">OpenAI path</div>
                <div class="stat-value">{openai_status}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Retrieval</div>
                <div class="stat-value">{retrieval_status}</div>
            </div>
        </div>
        <div class="inline-note">
            API đang đọc dữ liệu trực tiếp từ backend local. Khi OpenAI không
            sẵn sàng, câu trả lời vẫn fallback về agent nội bộ.
        </div>
    </div>
    """
    st.markdown(stat_html, unsafe_allow_html=True)


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
    st.markdown("### Giá mới nhất")
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
            display_name = escape(item.get("display_name") or item["item_name"])
            source = escape(item.get("source", "price"))
            display_unit = escape(item.get("display_unit") or item.get("unit") or "Không có đơn vị")
            effective_at = escape(format_datetime(item.get("effective_at")))
            value = (
                item.get("display_value")
                or item.get("display_sell_price")
                or item.get("sell_price")
                or item.get("display_buy_price")
                or item.get("buy_price")
                or "Chưa có giá"
            )
            card_html = f"""
            <div class="mini-card">
                <div class="mini-kicker">{source}</div>
                <div class="mini-title">{display_name}</div>
                <div class="mini-value">{escape(str(value))}</div>
                <div class="mini-copy">
                    {display_unit}<br/>
                    Cập nhật: {effective_at}
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)


def render_weather_cards(weather_payloads: list[tuple[str, dict | None, str | None]]) -> None:
    st.markdown("### Thời tiết nhanh")
    weather_columns = st.columns(len(weather_payloads))
    for column, (location, payload, error_message) in zip(
        weather_columns,
        weather_payloads,
        strict=False,
    ):
        with column:
            if error_message:
                st.markdown(
                    f"""
                    <div class="mini-card">
                        <div class="mini-kicker">{escape(location)}</div>
                        <div class="mini-title">Không tải được dữ liệu</div>
                        <div class="mini-copy">{escape(error_message)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                continue

            if not payload:
                st.markdown(
                    f"""
                    <div class="mini-card">
                        <div class="mini-kicker">{escape(location)}</div>
                        <div class="mini-title">Chưa có dữ liệu</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                continue

            warning_text = payload.get("warning_text") or "Không có cảnh báo nổi bật"
            source = escape(payload.get("source", location))
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
            st.markdown(card_html, unsafe_allow_html=True)


def ensure_chat_state() -> None:
    st.session_state.setdefault(
        "chat_messages",
        [
            {
                "role": "assistant",
                "content": (
                    "Xin chào. Tôi có thể trả lời về tin hot, giá vàng, tỷ giá, thời tiết, "
                    "chính sách và giao thông."
                ),
                "meta": "Chat local qua API /chat/query",
            }
        ],
    )
    st.session_state.setdefault("chat_feedback", None)
    st.session_state.setdefault("pending_chat_question", None)


def queue_chat_question(question: str) -> None:
    clean_question = question.strip()
    if not clean_question:
        st.session_state["chat_feedback"] = ("warning", "Bạn cần nhập câu hỏi trước khi gửi.")
        return

    st.session_state["chat_feedback"] = None
    st.session_state["pending_chat_question"] = clean_question


def process_pending_chat_question() -> None:
    pending_question = st.session_state.get("pending_chat_question")
    if not pending_question:
        return

    ensure_pending_user_visible(st.session_state["chat_messages"], pending_question)

    try:
        answer_payload = post_json("/chat/query", {"question": pending_question})
        answer = answer_payload.get("answer", "Chưa có câu trả lời.")
        meta = build_chat_meta(answer_payload)
    except Exception as exc:
        answer = f"Không gọi được chat API: {exc}"
        meta = "Kiểm tra lại API local hoặc quota OpenAI nếu đang bật path OpenAI."

    append_chat_message(
        st.session_state["chat_messages"],
        "assistant",
        answer,
        meta,
    )
    st.session_state["pending_chat_question"] = None


def render_chat_messages() -> None:
    for message in st.session_state["chat_messages"][-CHAT_HISTORY_LIMIT:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("meta"):
                st.caption(message["meta"])


def render_pending_chat_response() -> None:
    pending_question = st.session_state.get("pending_chat_question")
    if not pending_question:
        return

    ensure_pending_user_visible(st.session_state["chat_messages"], pending_question)
    render_chat_messages()

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm thông tin phù hợp trong dữ liệu hiện có..."):
            process_pending_chat_question()
            latest_message = st.session_state["chat_messages"][-1]
        st.markdown(latest_message["content"])
        if latest_message.get("meta"):
            st.caption(latest_message["meta"])

    st.rerun()


def render_chat_form() -> None:
    with st.form("floating_chat_form", clear_on_submit=True):
        question = st.text_area(
            "Nhập câu hỏi",
            height=96,
            label_visibility="collapsed",
            placeholder="Ví dụ: Có cảnh báo thời tiết nào không?",
        )
        submitted = st.form_submit_button("Gửi")

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
        st.markdown("#### Trợ lý AI")
        st.caption("Nút tròn này luôn nổi ở góc phải. Bấm vào để hỏi trực tiếp từ API local.")
        st.markdown(
            "<ul class='prompt-list'>"
            + "".join(f"<li>{escape(prompt)}</li>" for prompt in CHAT_SUGGESTIONS)
            + "</ul>",
            unsafe_allow_html=True,
        )
        if st.session_state.get("pending_chat_question"):
            render_pending_chat_response()
        else:
            render_chat_messages()

        render_chat_form()


def render_chat_hint() -> None:
    st.markdown("### Hỏi đáp bằng tiếng Việt")
    st.markdown(
        """
        <div class="card-surface">
            <div class="mini-title">Avatar chat tròn luôn nổi ở góc phải.</div>
            <div class="mini-copy">
                Avatar này có bubble nhắc sẵn ở bên ngoài.
                Bấm vào avatar để mở hộp chat, xem lịch sử hội thoại gần nhất
                và gửi câu hỏi mới mà không làm rối phần dashboard chính.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Tin tức + AI hỏi đáp",
    layout="wide",
    initial_sidebar_state="collapsed",
)

render_styles()

health_payload, health_error = fetch_payload("/health")
news_payload, news_error = fetch_payload("/news/hot", params={"limit": 5})
price_payload, price_error = fetch_payload("/prices/latest")
weather_payloads = [
    (location, *fetch_payload("/weather/latest", params={"location": location}))
    for location in WEATHER_LOCATIONS
]

render_hero(health_payload)

st.write("")
main_left, main_right = st.columns([1.35, 0.95], gap="large")

with main_left:
    render_news_cards(news_payload, news_error)

with main_right:
    render_status_panel(health_payload, health_error)
    st.write("")
    render_price_cards(price_payload, price_error)

st.write("")
render_weather_cards(weather_payloads)

st.write("")
render_chat_hint()
render_chat_assistant()
