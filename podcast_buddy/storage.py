from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .news import NewsItem


def save_episode_outputs(
    *,
    topic: str,
    conversation_markdown: str,
    summary_markdown: str,
    news_items: Sequence[NewsItem],
    output_dir: Path,
    metadata: dict[str, Any] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Path]:
    generated_at = generated_at or datetime.now(timezone.utc)
    run_dir = output_dir / f"{slugify(topic)}-{generated_at.strftime('%Y%m%d-%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=False)

    conversation_path = run_dir / "conversation.md"
    summary_path = run_dir / "summary.md"
    metadata_path = run_dir / "metadata.json"

    conversation_path.write_text(conversation_markdown, encoding="utf-8")
    summary_path.write_text(summary_markdown, encoding="utf-8")

    payload = {
        "topic": topic,
        "generated_at": generated_at.isoformat(),
        "files": {
            "conversation": str(conversation_path),
            "summary": str(summary_path),
        },
        "news_items": [asdict(item) for item in news_items],
        "metadata": metadata or {},
    }
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return {
        "run_dir": run_dir,
        "conversation": conversation_path,
        "summary": summary_path,
        "metadata": metadata_path,
    }


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "episode"
