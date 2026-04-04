from __future__ import annotations

from app.core.text import fold_text

TRAFFIC_POSITIVE_KEYWORDS = [
    "giao thong",
    "tai nan",
    "va cham",
    "un tac",
    "ket xe",
    "cam duong",
    "phan luong",
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
]

TRAFFIC_NEGATED_PHRASES = [
    "khong lien quan den giao thong",
    "khong phai giao thong",
]


def is_relevant_traffic_content(*parts: str | None) -> bool:
    haystack = fold_text(" ".join(part for part in parts if part))
    if not haystack:
        return False
    if any(phrase in haystack for phrase in TRAFFIC_NEGATED_PHRASES):
        return False

    positive_hits = [
        keyword for keyword in TRAFFIC_POSITIVE_KEYWORDS if keyword in haystack
    ]
    if not positive_hits:
        return False

    negative_hits = [
        keyword for keyword in TRAFFIC_NEGATIVE_KEYWORDS if keyword in haystack
    ]
    if negative_hits and len(positive_hits) < 2:
        return False

    return True
