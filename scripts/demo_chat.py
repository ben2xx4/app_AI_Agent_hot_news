from __future__ import annotations

import json

import _bootstrap  # noqa: F401

from app.db.session import ensure_sqlite_schema, session_scope
from app.services.chat_service import ChatService

QUESTIONS = [
    "Tin hot hom nay la gi?",
    "Gia xang hom nay bao nhieu?",
    "Gia vang hom nay tang hay giam?",
    "Ty gia USD hom nay la bao nhieu?",
    "Ha Noi hom nay co mua khong?",
    "TP.HCM hom nay nong khong?",
    "Co chinh sach moi nao ve giao duc khong?",
    "Co thong bao moi nao tu Bo Y te khong?",
    "Co tin giao thong nao dang chu y o TP.HCM khong?",
    "Co nhung chu de nao dang duoc nhieu bao noi toi?",
]


def main() -> None:
    ensure_sqlite_schema()
    with session_scope() as db:
        service = ChatService(db)
        for question in QUESTIONS:
            answer = service.answer_question(question)
            print(json.dumps(answer, ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
