from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from xml.etree import ElementTree

from bs4 import BeautifulSoup

from app.pipelines.common.processing import normalize_key, parse_datetime
from app.pipelines.common.records import PriceRecord, SourceDefinition


def _to_decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if text in {"-", "N/A"}:
        return None
    return Decimal(text.replace(",", ""))


def _to_vn_decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if text in {"-", "N/A"}:
        return None
    normalized = text.replace(".", "").replace(",", ".")
    return Decimal(normalized)


def _parse_vietcombank_datetime(value: str | None):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is not None:
        return parsed
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S"):
        try:
            from datetime import datetime

            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _parse_vietcombank_fx_xml(source: SourceDefinition, payload: str) -> list[PriceRecord]:
    xml_payload = payload[payload.find("<ExrateList") :] if "<ExrateList" in payload else payload
    root = ElementTree.fromstring(xml_payload)
    effective_at = _parse_vietcombank_datetime(root.findtext("DateTime"))
    allowed_currencies = {str(item).upper() for item in source.extra.get("currencies", [])}
    provider_suffix = normalize_key(str(source.extra.get("provider_suffix", "vietcombank")))

    records: list[PriceRecord] = []
    for row in root.findall("Exrate"):
        currency_code = (row.attrib.get("CurrencyCode") or "").strip().upper()
        if allowed_currencies and currency_code not in allowed_currencies:
            continue

        item_name = normalize_key(f"ty gia {currency_code.lower()} {provider_suffix}")
        records.append(
            PriceRecord(
                item_type=str(source.extra.get("item_type", "ty_gia")),
                item_name=item_name,
                region=str(source.extra.get("region", "Vietcombank")),
                buy_price=_to_decimal(row.attrib.get("Buy")),
                sell_price=_to_decimal(row.attrib.get("Sell")),
                unit=str(source.extra.get("unit", "VND")),
                effective_at=effective_at,
            )
        )
    return records


def _parse_sjc_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%H:%M %d/%m/%Y", "%H:%M:%S %d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return parse_datetime(value)


def _parse_sjc_gold_json(source: SourceDefinition, payload: str) -> list[PriceRecord]:
    data = json.loads(payload)
    rows = data.get("data", [])
    effective_at = _parse_sjc_datetime(data.get("latestDate"))
    allowed_types = source.extra.get("type_map", {}) or {}

    records: list[PriceRecord] = []
    for row in rows:
        type_name = str(row.get("TypeName") or "").strip()
        item_name = allowed_types.get(type_name)
        if not item_name:
            continue
        records.append(
            PriceRecord(
                item_type="gold",
                item_name=str(item_name),
                region=str(row.get("BranchName") or source.extra.get("region") or "SJC"),
                buy_price=_to_decimal(row.get("BuyValue") or row.get("Buy")),
                sell_price=_to_decimal(row.get("SellValue") or row.get("Sell")),
                unit=str(source.extra.get("unit", "VND/luong")),
                effective_at=effective_at,
            )
        )
    return records


def _parse_petrolimex_fuel_json(source: SourceDefinition, payload: str) -> list[PriceRecord]:
    data = json.loads(payload)
    rows = data.get("Objects", [])
    product_map = source.extra.get("product_map", {}) or {}
    price_field = str(source.extra.get("price_field", "Zone1Price"))

    records: list[PriceRecord] = []
    for row in rows:
        title = str(row.get("Title") or "").strip()
        item_name = product_map.get(title)
        if not item_name:
            continue
        records.append(
            PriceRecord(
                item_type=str(source.extra.get("item_type", "fuel")),
                item_name=str(item_name),
                region=str(source.extra.get("region", "Vùng 1")),
                buy_price=None,
                sell_price=_to_decimal(row.get(price_field)),
                unit=str(source.extra.get("unit", "VND/lit")),
                effective_at=parse_datetime(row.get("LastModified")),
            )
        )
    return records


def _extract_section_table(soup: BeautifulSoup, heading_text: str):
    for heading in soup.find_all(["h2", "h3"]):
        if heading_text.casefold() not in heading.get_text(" ", strip=True).casefold():
            continue
        return heading.find_next("table")
    return None


def _extract_effective_date(soup: BeautifulSoup, heading_text: str) -> datetime | None:
    for heading in soup.find_all(["h2", "h3"]):
        if heading_text.casefold() not in heading.get_text(" ", strip=True).casefold():
            continue
        container = heading.parent
        if container is None:
            continue
        text = container.get_text(" ", strip=True)
        marker = "áp dụng cho ngày"
        lowered = text.casefold()
        if marker in lowered:
            suffix = text[lowered.index(marker) + len(marker) :].strip()
            date_text = suffix.split()[0]
            parsed = parse_datetime(date_text)
            if parsed is not None:
                return parsed.replace(hour=12, minute=0, second=0, microsecond=0)
    return None


def _parse_sbv_fx_html(source: SourceDefinition, payload: str) -> list[PriceRecord]:
    soup = BeautifulSoup(payload, "html.parser")
    item_name_map = source.extra.get("item_name_map", {}) or {}
    allowed_currencies = {str(code).upper() for code in source.extra.get("currencies", [])}
    region = str(source.extra.get("region", "Viet Nam"))
    item_type = str(source.extra.get("item_type", "ty_gia"))

    reference_table = _extract_section_table(
        soup,
        "Tỷ giá tham khảo giữa đồng Việt Nam và các loại ngoại tệ tại Cục Quản lý ngoại hối",
    )
    effective_at = _extract_effective_date(
        soup,
        "Tỷ giá tham khảo giữa đồng Việt Nam và các loại ngoại tệ tại Cục Quản lý ngoại hối",
    )

    records: list[PriceRecord] = []
    if reference_table is not None:
        for row in reference_table.select("tbody tr"):
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
            if len(cells) < 5:
                continue
            currency_code = cells[1].upper()
            if allowed_currencies and currency_code not in allowed_currencies:
                continue

            item_name = item_name_map.get(currency_code)
            if not item_name:
                item_name = normalize_key(f"ty gia {currency_code.lower()} sbv")

            records.append(
                PriceRecord(
                    item_type=item_type,
                    item_name=str(item_name),
                    region=region,
                    buy_price=_to_vn_decimal(cells[3]),
                    sell_price=_to_vn_decimal(cells[4]),
                    unit=f"VND/{currency_code}",
                    effective_at=effective_at,
                )
            )

    central_rate_item_name = source.extra.get("central_rate_item_name")
    if central_rate_item_name:
        central_table = _extract_section_table(soup, "Tỷ giá trung tâm")
        central_effective_at = _extract_effective_date(soup, "Tỷ giá trung tâm")
        if central_table is not None:
            row = central_table.select_one("tbody tr")
            if row is not None:
                cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
                if len(cells) >= 2:
                    value_text = cells[1].replace("VND", "").strip()
                    records.append(
                        PriceRecord(
                            item_type=item_type,
                            item_name=str(central_rate_item_name),
                            region=region,
                            buy_price=None,
                            sell_price=_to_vn_decimal(value_text),
                            unit="VND/USD",
                            effective_at=central_effective_at or effective_at,
                        )
                    )

    return records


def parse_price_payload(source: SourceDefinition, payload: str) -> list[PriceRecord]:
    if source.parser == "vietcombank_fx_xml":
        return _parse_vietcombank_fx_xml(source, payload)
    if source.parser == "sjc_gold_json":
        return _parse_sjc_gold_json(source, payload)
    if source.parser == "petrolimex_fuel_json":
        return _parse_petrolimex_fuel_json(source, payload)
    if source.parser == "sbv_fx_html":
        return _parse_sbv_fx_html(source, payload)

    data = json.loads(payload)
    rows = data.get("records", data if isinstance(data, list) else [])
    records: list[PriceRecord] = []

    for row in rows:
        records.append(
            PriceRecord(
                item_type=row["item_type"],
                item_name=row["item_name"],
                region=row.get("region"),
                buy_price=_to_decimal(row.get("buy_price")),
                sell_price=_to_decimal(row.get("sell_price")),
                unit=row.get("unit"),
                effective_at=parse_datetime(row.get("effective_at")),
            )
        )
    return records
