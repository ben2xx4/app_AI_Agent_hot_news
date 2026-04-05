from __future__ import annotations

from app.core.text import fold_text

TRAFFIC_POSITIVE_KEYWORDS = [
    "giao thong",
    "tai nan",
    "va cham",
    "un tac",
    "ket xe",
    "thong xe",
    "cam duong",
    "phan luong",
    "nut giao",
    "han che luu thong",
    "xe buyt",
    "xe bus",
    "metro",
    "tau dien",
    "duong sat",
    "cao toc",
    "quoc lo",
    "tinh lo",
    "duong noi",
    "lam duong",
    "mo rong duong",
    "cau duong",
    "ham chui",
    "ben xe",
    "san bay",
    "nha ga",
    "hang khong",
    "ve may bay",
    "oto",
    "o to",
    "xe tai",
    "xe khach",
    "container",
    "taxi",
    "csgt",
    "nong do con",
    "dang kiem",
]

TRAFFIC_HEADLINE_PRIORITY_KEYWORDS = [
    "tai nan",
    "va cham",
    "un tac",
    "ket xe",
    "cam duong",
    "cam xe",
    "phan luong",
    "thong xe",
    "dong duong",
    "phong toa",
    "ngap",
    "su co",
]

TRAFFIC_CONTEXT_KEYWORDS = [
    "nut giao",
    "cao toc",
    "quoc lo",
    "tinh lo",
    "ham chui",
    "cau duong",
    "container",
    "xe tai",
    "xe buyt",
    "metro",
    "san bay",
]

TRAFFIC_NEGATIVE_KEYWORDS = [
    "an toan thuc pham",
    "tuyen sinh",
    "giao duc",
    "hoc duong",
    "cap cuu",
    "kham suc khoe",
    "dien anh",
    "world cup",
    "bong da",
    "xac thuc sim",
    "sim chinh chu",
    "doi moi cong nghe",
    "thu tuc hanh chinh",
    "xang dau",
    "gia xang",
    "gia dau",
    "dieu hanh gia",
]

TRAFFIC_LOW_PRIORITY_KEYWORDS = [
    "du thao",
    "nghi dinh",
    "quy dinh",
    "thong tu",
    "thu tuc",
    "dang kiem",
    "tem kiem dinh",
    "bo dan tem",
    "chu truong",
    "de xuat",
    "thanh lap",
]

TRAFFIC_NEGATED_PHRASES = [
    "khong lien quan den giao thong",
    "khong phai giao thong",
]

TRAFFIC_FOCUS_KEYWORDS = {
    "blocked_road": [
        "cam duong",
        "cam xe",
        "bi cam",
        "phan luong",
        "han che luu thong",
        "dong duong",
    ],
    "congestion": [
        "un tac",
        "ket xe",
        "dong xe",
        "di chuyen cham",
    ],
    "accident": [
        "tai nan",
        "va cham",
        "truot nga",
        "lat xe",
    ],
}

TRAFFIC_FOCUS_EVENT_TYPES = {
    "blocked_road": {"phan_luong", "cam_duong_tam_thoi"},
    "congestion": {"un_tac"},
    "accident": {"tai_nan"},
}


def is_relevant_traffic_content(*parts: str | None) -> bool:
    title = parts[0] if len(parts) > 0 else None
    summary = parts[1] if len(parts) > 1 else None
    description = parts[2] if len(parts) > 2 else None

    title_summary = fold_text(" ".join(part for part in [title, summary] if part))
    description_text = fold_text(description)
    haystack = fold_text(" ".join(part for part in parts if part))
    if not haystack:
        return False
    if any(phrase in haystack for phrase in TRAFFIC_NEGATED_PHRASES):
        return False

    headline_hits = [
        keyword for keyword in TRAFFIC_POSITIVE_KEYWORDS if keyword in title_summary
    ]
    description_hits = [
        keyword for keyword in TRAFFIC_POSITIVE_KEYWORDS if keyword in description_text
    ]
    combined_hits = sorted(set(headline_hits + description_hits))
    if not combined_hits:
        return False

    negative_hits = [keyword for keyword in TRAFFIC_NEGATIVE_KEYWORDS if keyword in haystack]
    if negative_hits and len(headline_hits) < 2:
        return False

    if not headline_hits:
        return False

    return True


def traffic_relevance_score(
    event_type: str | None,
    *parts: str | None,
) -> float:
    title = parts[0] if len(parts) > 0 else None
    summary = parts[1] if len(parts) > 1 else None
    description = parts[2] if len(parts) > 2 else None

    if not is_relevant_traffic_content(title, summary, description):
        return 0.0

    title_text = fold_text(title)
    summary_text = fold_text(summary)
    description_text = fold_text(description)
    headline_text = " ".join(part for part in [title_text, summary_text] if part).strip()
    haystack = " ".join(part for part in [headline_text, description_text] if part).strip()

    score = 0.0
    headline_priority_hits = [
        keyword for keyword in TRAFFIC_HEADLINE_PRIORITY_KEYWORDS if keyword in headline_text
    ]
    context_hits = [keyword for keyword in TRAFFIC_CONTEXT_KEYWORDS if keyword in headline_text]
    description_priority_hits = [
        keyword for keyword in TRAFFIC_HEADLINE_PRIORITY_KEYWORDS if keyword in description_text
    ]
    low_priority_hits = [
        keyword for keyword in TRAFFIC_LOW_PRIORITY_KEYWORDS if keyword in haystack
    ]

    score += float(len(set(headline_priority_hits)) * 3)
    score += float(len(set(context_hits)) * 1.2)
    score += float(len(set(description_priority_hits)) * 0.8)

    event_type_bonus = {
        "phan_luong": 2.5,
        "cam_duong_tam_thoi": 2.5,
        "un_tac": 2.2,
        "tai_nan": 2.4,
        "cap_nhat_giao_thong": 0.6,
    }
    score += event_type_bonus.get(event_type or "", 0.0)

    if low_priority_hits:
        score -= float(len(set(low_priority_hits)) * 2.2)
        if not headline_priority_hits:
            score -= 1.5

    if any(keyword in title_text for keyword in ["tam", "sap", "khan cap"]):
        score += 0.6

    return round(score, 3)


def matches_traffic_focus(
    focus: str | None,
    event_type: str | None,
    *parts: str | None,
) -> bool:
    if not focus:
        return True
    title_text = fold_text(parts[0] if len(parts) > 0 else None)
    body_text = fold_text(" ".join(part for part in parts[1:] if part))
    haystack = " ".join(part for part in [title_text, body_text] if part).strip()
    if not haystack and not event_type:
        return False
    title_keyword_match = any(
        keyword in title_text for keyword in TRAFFIC_FOCUS_KEYWORDS.get(focus, [])
    )
    if title_keyword_match:
        return True
    if focus == "blocked_road":
        return False
    return False
