from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.pipelines.common.processing import stable_hash


class RawStorage:
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_text(
        self,
        *,
        pipeline_name: str,
        source_name: str,
        content: str,
        extension: str = "txt",
    ) -> tuple[str, str]:
        now = datetime.now(UTC).replace(tzinfo=None)
        content_hash = stable_hash(content)
        folder = (
            self.base_path
            / pipeline_name
            / source_name
            / now.strftime("%Y")
            / now.strftime("%m")
            / now.strftime("%d")
        )
        folder.mkdir(parents=True, exist_ok=True)

        filename = f"{now.strftime('%H%M%S')}_{content_hash[:12]}.{extension}"
        file_path = folder / filename
        file_path.write_text(content, encoding="utf-8")
        return str(file_path), content_hash
