from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SUMMARY_MODEL = "sshleifer/distilbart-cnn-12-6"


def load_dotenv(path: Path | str = ".env") -> None:
    """Load simple KEY=VALUE pairs without adding a runtime dependency."""
    dotenv_path = Path(path)
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    serpapi_key: str | None
    serpapi_gl: str
    serpapi_hl: str
    summary_model: str
    output_dir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            serpapi_key=os.getenv("SERPAPI_KEY"),
            serpapi_gl=os.getenv("SERPAPI_GL", "us"),
            serpapi_hl=os.getenv("SERPAPI_HL", "en"),
            summary_model=os.getenv("SUMMARY_MODEL", DEFAULT_SUMMARY_MODEL),
            output_dir=Path(os.getenv("OUTPUT_DIR", "outputs")),
        )
