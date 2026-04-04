from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import DocumentEmbedding

EmbeddingVector = dict[str, float] | list[float] | None


class EmbeddingRepository:
    def replace_chunks(
        self,
        db: Session,
        *,
        doc_type: str,
        doc_id: int,
        chunks: list[str],
        embedding_model: str | None = None,
        embedding_vectors: list[EmbeddingVector] | None = None,
    ) -> None:
        db.execute(
            delete(DocumentEmbedding).where(
                DocumentEmbedding.doc_type == doc_type,
                DocumentEmbedding.doc_id == doc_id,
            )
        )
        for index, chunk in enumerate(chunks):
            vector = None
            if embedding_vectors and index < len(embedding_vectors):
                vector = embedding_vectors[index]
            db.add(
                DocumentEmbedding(
                    doc_type=doc_type,
                    doc_id=doc_id,
                    chunk_index=index,
                    chunk_text=chunk,
                    embedding_model=embedding_model,
                    embedding_vector_json=vector,
                )
            )
        db.flush()
