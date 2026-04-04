from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.text import (
    display_price_name,
    display_price_unit,
    display_trend,
    format_price_amount,
    format_price_with_unit,
)
from app.repositories.price_repository import PriceRepository
from app.services.helpers import load_source_metadata_map


class PriceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PriceRepository()

    @staticmethod
    def _is_demo_only_source(
        source_metadata: dict[int, dict[str, object]],
        source_id: int | None,
    ) -> bool:
        if source_id is None:
            return False
        return bool(source_metadata.get(source_id, {}).get("is_demo_only", False))

    def _pick_preferred_row(
        self,
        rows: list[object],
        source_metadata: dict[int, dict[str, object]],
        *,
        prefer_live: bool | None = None,
    ):
        if not rows:
            return None
        if prefer_live is True:
            live_rows = [
                row
                for row in rows
                if not self._is_demo_only_source(source_metadata, row.source_id)
            ]
            return live_rows[0] if live_rows else None
        if prefer_live is False:
            demo_rows = [
                row for row in rows if self._is_demo_only_source(source_metadata, row.source_id)
            ]
            return demo_rows[0] if demo_rows else None

        live_rows = [
            row for row in rows if not self._is_demo_only_source(source_metadata, row.source_id)
        ]
        preferred_rows = live_rows or rows
        return preferred_rows[0] if preferred_rows else None

    def _pick_preferred_latest_rows(
        self,
        rows: list[object],
        source_metadata: dict[int, dict[str, object]],
    ) -> list[object]:
        grouped_rows: dict[str, list[object]] = {}
        for row in rows:
            grouped_rows.setdefault(row.item_name, []).append(row)

        preferred_rows = [
            preferred_row
            for item_rows in grouped_rows.values()
            if (preferred_row := self._pick_preferred_row(item_rows, source_metadata)) is not None
        ]
        return sorted(
            preferred_rows,
            key=lambda row: (row.effective_at or datetime.min, row.id),
            reverse=True,
        )

    def get_latest_price(self, item_name: str | None = None) -> dict:
        rows = self.repo.get_latest(self.db, item_name=item_name, limit=60 if item_name else 20)
        source_metadata = load_source_metadata_map(self.db, [row.source_id for row in rows])
        preferred_rows = self._pick_preferred_latest_rows(rows, source_metadata)
        if item_name:
            preferred_rows = preferred_rows[:1]
        items = [
            {
                "id": row.id,
                "item_type": row.item_type,
                "item_name": row.item_name,
                "display_name": display_price_name(row.item_name),
                "region": row.region,
                "buy_price": row.buy_price,
                "sell_price": row.sell_price,
                "unit": row.unit,
                "display_buy_price": format_price_amount(row.buy_price),
                "display_sell_price": format_price_amount(row.sell_price),
                "display_unit": display_price_unit(row.unit),
                "display_value": format_price_with_unit(
                    row.sell_price or row.buy_price,
                    row.unit,
                ),
                "effective_at": row.effective_at,
                "source": source_metadata.get(row.source_id or -1, {}).get(
                    "source_name",
                    "unknown",
                ),
            }
            for row in preferred_rows
        ]
        updated_at = max(
            (row["effective_at"] for row in items if row["effective_at"]), default=None
        )
        return {"items": items, "updated_at": updated_at}

    def compare_price(self, item_name: str) -> dict:
        latest_rows = self.repo.get_latest(self.db, item_name=item_name, limit=20)
        source_metadata = load_source_metadata_map(self.db, [row.source_id for row in latest_rows])
        current = self._pick_preferred_row(latest_rows, source_metadata)
        if not current:
            return {
                "item_name": item_name,
                "current": None,
                "previous": None,
                "delta": None,
                "trend": "no_data",
            }

        previous_candidates = self.repo.get_previous_candidates(
            self.db, item_name=item_name, current_effective_at=current.effective_at
        )
        previous_source_metadata = load_source_metadata_map(
            self.db,
            [row.source_id for row in previous_candidates],
        )
        previous = self._pick_preferred_row(
            previous_candidates,
            previous_source_metadata,
            prefer_live=not self._is_demo_only_source(source_metadata, current.source_id),
        )
        current_value = current.sell_price or current.buy_price or Decimal("0")
        previous_value = (
            (previous.sell_price or previous.buy_price or Decimal("0")) if previous else None
        )
        delta = (current_value - previous_value) if previous_value is not None else None
        trend = "khong_doi"
        if delta is not None:
            if delta > 0:
                trend = "tang"
            elif delta < 0:
                trend = "giam"

        return {
            "item_name": item_name,
            "display_name": display_price_name(item_name),
            "current": {
                "buy_price": current.buy_price,
                "sell_price": current.sell_price,
                "unit": current.unit,
                "display_buy_price": format_price_amount(current.buy_price),
                "display_sell_price": format_price_amount(current.sell_price),
                "display_unit": display_price_unit(current.unit),
                "display_value": format_price_with_unit(
                    current.sell_price or current.buy_price,
                    current.unit,
                ),
                "effective_at": current.effective_at,
                "source": source_metadata.get(current.source_id or -1, {}).get(
                    "source_name",
                    "unknown",
                ),
            },
            "previous": (
                {
                    "buy_price": previous.buy_price,
                    "sell_price": previous.sell_price,
                    "unit": previous.unit,
                    "display_buy_price": format_price_amount(previous.buy_price),
                    "display_sell_price": format_price_amount(previous.sell_price),
                    "display_unit": display_price_unit(previous.unit),
                    "display_value": format_price_with_unit(
                        previous.sell_price or previous.buy_price,
                        previous.unit,
                    ),
                    "effective_at": previous.effective_at,
                    "source": previous_source_metadata.get(previous.source_id or -1, {}).get(
                        "source_name",
                        "unknown",
                    ),
                }
                if previous
                else None
            ),
            "delta": delta,
            "display_delta": format_price_with_unit(
                abs(delta) if delta is not None else None,
                current.unit,
            ),
            "trend": display_trend(trend),
            "updated_at": current.effective_at,
        }
