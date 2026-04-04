from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import PriceSnapshot


class PriceRepository:
    def create_snapshot(self, db: Session, **payload) -> PriceSnapshot:
        snapshot = PriceSnapshot(**payload)
        db.add(snapshot)
        db.flush()
        return snapshot

    def get_latest(
        self,
        db: Session,
        item_name: str | None = None,
        limit: int | None = None,
    ) -> list[PriceSnapshot]:
        stmt = select(PriceSnapshot)
        if item_name:
            stmt = stmt.where(PriceSnapshot.item_name == item_name)
        stmt = stmt.order_by(desc(PriceSnapshot.effective_at), desc(PriceSnapshot.id))
        rows = list(db.scalars(stmt.limit(limit or (30 if item_name is None else 10))))
        if item_name:
            return rows

        seen: set[str] = set()
        latest_rows: list[PriceSnapshot] = []
        for row in rows:
            if row.item_name in seen:
                continue
            latest_rows.append(row)
            seen.add(row.item_name)
        return latest_rows

    def get_previous(
        self,
        db: Session,
        item_name: str,
        current_effective_at: datetime | None,
    ) -> PriceSnapshot | None:
        stmt = select(PriceSnapshot).where(PriceSnapshot.item_name == item_name)
        if current_effective_at is not None:
            stmt = stmt.where(PriceSnapshot.effective_at < current_effective_at)
        stmt = stmt.order_by(desc(PriceSnapshot.effective_at), desc(PriceSnapshot.id))
        return db.scalar(stmt)

    def get_previous_candidates(
        self,
        db: Session,
        item_name: str,
        current_effective_at: datetime | None,
        limit: int = 10,
    ) -> list[PriceSnapshot]:
        stmt = select(PriceSnapshot).where(PriceSnapshot.item_name == item_name)
        if current_effective_at is not None:
            stmt = stmt.where(PriceSnapshot.effective_at < current_effective_at)
        stmt = stmt.order_by(desc(PriceSnapshot.effective_at), desc(PriceSnapshot.id))
        return list(db.scalars(stmt.limit(limit)))
