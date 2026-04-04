from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from math import sqrt

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.settings import get_settings
from app.core.text import fold_text
from app.models import Article, PolicyDocument
from app.pipelines.common.processing import split_into_chunks
from app.repositories.embedding_repository import EmbeddingRepository

logger = get_logger(__name__)

ARTICLE_CHUNK_SIZE = 380
POLICY_CHUNK_SIZE = 450
MAX_VECTOR_FEATURES = 80

STOPWORDS = {
    "bi",
    "boi",
    "chu",
    "cac",
    "can",
    "cho",
    "co",
    "cua",
    "da",
    "dang",
    "de",
    "den",
    "duoc",
    "giu",
    "giua",
    "hom",
    "khong",
    "khi",
    "la",
    "lam",
    "lai",
    "len",
    "mot",
    "moi",
    "nao",
    "nay",
    "nhieu",
    "nhung",
    "noi",
    "o",
    "sau",
    "se",
    "tai",
    "the",
    "theo",
    "thi",
    "toi",
    "tren",
    "trong",
    "tu",
    "va",
    "van",
    "ve",
    "voi",
}

SEMANTIC_CONCEPTS = {
    "giao_duc": {
        "dau cap",
        "giao duc",
        "hoc duong",
        "hoc phi",
        "hoc sinh",
        "nha truong",
        "sinh vien",
        "truong hoc",
        "tuyen sinh",
    },
    "y_te": {
        "bac si",
        "benh vien",
        "cap cuu",
        "co so y te",
        "kham chua benh",
        "thuoc",
        "vat tu y te",
        "y te",
    },
    "tai_chinh": {
        "gia vang",
        "lai suat",
        "ngan sach",
        "tai chinh",
        "thue",
        "ty gia",
        "xang dau",
    },
    "giao_thong": {
        "cam duong",
        "giao thong",
        "luu thong",
        "phan luong",
        "un tac",
        "van tai",
        "xe buyt",
    },
    "buyt_dien": {
        "buyt dien",
        "xe buyt dien",
        "xe cong cong dien",
    },
    "thoi_tiet": {
        "gio giat",
        "mua dong",
        "mua lon",
        "nang nong",
        "thoi tiet",
    },
}


def _generate_ngrams(words: list[str], size: int) -> Iterable[str]:
    if len(words) < size:
        return []
    return (" ".join(words[index : index + size]) for index in range(len(words) - size + 1))


def build_sparse_vector(text: str | None) -> dict[str, float]:
    folded = fold_text(text)
    if not folded:
        return {}

    words = [word for word in folded.split() if len(word) > 1 and word not in STOPWORDS]
    if not words:
        return {}

    counter: Counter[str] = Counter()
    for word in words:
        counter[f"tok:{word}"] += 1.0
    for phrase in _generate_ngrams(words, 2):
        counter[f"phrase:{phrase}"] += 1.2
    for phrase in _generate_ngrams(words, 3):
        counter[f"phrase:{phrase}"] += 1.35
    for concept, aliases in SEMANTIC_CONCEPTS.items():
        if any(alias in folded for alias in aliases):
            counter[f"concept:{concept}"] += 2.2

    top_features = counter.most_common(MAX_VECTOR_FEATURES)
    norm = sqrt(sum(weight * weight for _, weight in top_features))
    if norm <= 0:
        return {}
    return {
        feature: round(weight / norm, 6)
        for feature, weight in top_features
    }


def build_chunk_vectors(chunks: list[str]) -> list[dict[str, float] | None]:
    vectors: list[dict[str, float] | None] = []
    for chunk in chunks:
        vector = build_sparse_vector(chunk)
        vectors.append(vector or None)
    return vectors


def build_article_chunks(article: Article) -> list[str]:
    return split_into_chunks(article.content_clean or article.summary, max_chars=ARTICLE_CHUNK_SIZE)


def build_policy_chunks(document: PolicyDocument) -> list[str]:
    return split_into_chunks(
        document.content_clean or document.summary, max_chars=POLICY_CHUNK_SIZE
    )


class RetrievalIndexService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.embedding_repo = EmbeddingRepository()

    @property
    def model_name(self) -> str:
        return self.settings.experimental_retrieval_model

    def build_chunk_vectors(self, chunks: list[str]) -> list[dict[str, float] | None]:
        return build_chunk_vectors(chunks)

    def reindex_articles(self, limit: int | None = None) -> dict[str, int | str]:
        stmt = select(Article).order_by(desc(Article.published_at), desc(Article.id))
        if limit:
            stmt = stmt.limit(limit)
        rows = list(self.db.scalars(stmt))

        total_chunks = 0
        for row in rows:
            chunks = build_article_chunks(row)
            total_chunks += len(chunks)
            self.embedding_repo.replace_chunks(
                self.db,
                doc_type="article",
                doc_id=row.id,
                chunks=chunks,
                embedding_model=self.model_name,
                embedding_vectors=self.build_chunk_vectors(chunks),
            )

        self.db.flush()
        logger.info(
            "Da build experimental retrieval index cho news: %s bai, %s chunk",
            len(rows),
            total_chunks,
        )
        return {"doc_type": "article", "documents": len(rows), "chunks": total_chunks}

    def reindex_policies(self, limit: int | None = None) -> dict[str, int | str]:
        stmt = select(PolicyDocument).order_by(
            desc(PolicyDocument.issued_at),
            desc(PolicyDocument.id),
        )
        if limit:
            stmt = stmt.limit(limit)
        rows = list(self.db.scalars(stmt))

        total_chunks = 0
        for row in rows:
            chunks = build_policy_chunks(row)
            total_chunks += len(chunks)
            self.embedding_repo.replace_chunks(
                self.db,
                doc_type="policy",
                doc_id=row.id,
                chunks=chunks,
                embedding_model=self.model_name,
                embedding_vectors=self.build_chunk_vectors(chunks),
            )

        self.db.flush()
        logger.info(
            "Da build experimental retrieval index cho policy: %s van ban, %s chunk",
            len(rows),
            total_chunks,
        )
        return {"doc_type": "policy", "documents": len(rows), "chunks": total_chunks}
