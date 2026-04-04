from __future__ import annotations

from app.db.session import session_scope
from app.pipelines.common.base import BasePipeline
from app.pipelines.common.records import PriceRecord, SourceDefinition
from app.pipelines.price.parser import parse_price_payload
from app.repositories.price_repository import PriceRepository


class PricePipeline(BasePipeline[PriceRecord]):
    pipeline_name = "price"

    def __init__(self, *, demo_only: bool = False, source_names: set[str] | None = None) -> None:
        super().__init__(demo_only=demo_only, source_names=source_names)
        self.price_repo = PriceRepository()

    def parse(self, source: SourceDefinition, payload: str) -> list[PriceRecord]:
        return parse_price_payload(source, payload)

    def store(self, source_id: int | None, records: list[PriceRecord]) -> int:
        inserted = 0
        with session_scope() as db:
            for record in records:
                self.price_repo.create_snapshot(
                    db,
                    source_id=source_id,
                    item_type=record.item_type,
                    item_name=record.item_name,
                    region=record.region,
                    buy_price=record.buy_price,
                    sell_price=record.sell_price,
                    unit=record.unit,
                    effective_at=record.effective_at,
                )
                inserted += 1
        return inserted
