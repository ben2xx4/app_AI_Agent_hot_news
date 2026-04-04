from __future__ import annotations

from pathlib import Path

import yaml

from app.core.settings import get_settings
from app.pipelines.common.records import SourceDefinition


def load_source_definitions() -> list[SourceDefinition]:
    settings = get_settings()
    config_path = Path(settings.source_config_path)
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    sources: list[SourceDefinition] = []
    for item in payload.get("sources", []):
        extra = {
            key: value
            for key, value in item.items()
            if key
            not in {
                "name",
                "pipeline",
                "source_type",
                "url",
                "category_default",
                "active",
                "fetch_interval_minutes",
                "timeout_seconds",
                "retry_count",
                "trust_level",
                "demo_fixture",
                "parser",
                "headers",
            }
        }
        sources.append(
            SourceDefinition(
                name=item["name"],
                pipeline=item["pipeline"],
                source_type=item["source_type"],
                url=item.get("url"),
                category_default=item.get("category_default"),
                active=item.get("active", True),
                fetch_interval_minutes=int(item.get("fetch_interval_minutes", 60)),
                timeout_seconds=int(item.get("timeout_seconds", 15)),
                retry_count=int(item.get("retry_count", 2)),
                trust_level=int(item.get("trust_level", 3)),
                demo_fixture=item.get("demo_fixture"),
                parser=item.get("parser"),
                headers=item.get("headers", {}) or {},
                extra=extra,
            )
        )
    return sources


def load_sources_for_pipeline(pipeline_name: str) -> list[SourceDefinition]:
    return [
        source
        for source in load_source_definitions()
        if source.pipeline == pipeline_name and source.active
    ]
