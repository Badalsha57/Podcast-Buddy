from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


class NewsFetchError(RuntimeError):
    """Raised when the news provider returns an unusable response."""


@dataclass(frozen=True)
class NewsItem:
    title: str
    source: str = ""
    link: str = ""
    published_at: str = ""
    snippet: str = ""

    def as_brief_line(self) -> str:
        parts = [self.title.strip()]
        if self.snippet:
            parts.append(self.snippet.strip())
        context = []
        if self.source:
            context.append(f"source: {self.source}")
        if self.published_at:
            context.append(f"date: {self.published_at}")
        if context:
            parts.append(f"({', '.join(context)})")
        return " ".join(part for part in parts if part).strip()


class SerpApiNewsClient:
    ENDPOINT = "https://serpapi.com/search.json"

    def __init__(self, api_key: str, timeout_seconds: int = 30) -> None:
        if not api_key:
            raise ValueError("SerpAPI key is required")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def search(
        self,
        query: str,
        *,
        limit: int = 8,
        gl: str = "us",
        hl: str = "en",
    ) -> list[NewsItem]:
        params = {
            "engine": "google_news",
            "q": query,
            "gl": gl,
            "hl": hl,
            "api_key": self.api_key,
        }
        url = f"{self.ENDPOINT}?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise NewsFetchError(
                    "SerpAPI rejected the API key (401 Unauthorized). "
                    "Check SERPAPI_KEY in .env and make sure it matches your SerpAPI dashboard key."
                ) from exc
            raise NewsFetchError(f"SerpAPI HTTP error {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise NewsFetchError(f"Could not reach SerpAPI: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise NewsFetchError("SerpAPI returned invalid JSON") from exc

        if isinstance(payload, dict) and payload.get("error"):
            raise NewsFetchError(str(payload["error"]))

        return parse_news_results(payload, limit=limit)


def load_news_json(path: Path) -> list[NewsItem]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return parse_news_results(payload)


def parse_news_results(payload: Any, *, limit: int | None = None) -> list[NewsItem]:
    if isinstance(payload, list):
        raw_results = payload
    elif isinstance(payload, dict):
        raw_results = payload.get("news_results", [])
    else:
        raise NewsFetchError("Unsupported news JSON shape")

    items: list[NewsItem] = []
    seen: set[str] = set()

    for result in raw_results:
        for article in _iter_articles(result):
            item = _to_news_item(article)
            if not item or not item.title:
                continue
            identity = item.link or item.title.lower()
            if identity in seen:
                continue
            seen.add(identity)
            items.append(item)
            if limit is not None and len(items) >= limit:
                return items

    return items


def format_news_brief(topic: str, items: Iterable[NewsItem]) -> str:
    lines = [f"News topic: {topic}."]
    for index, item in enumerate(items, start=1):
        line = f"Story {index}: {item.title.strip()}"
        context = []
        if item.source:
            context.append(f"Source: {item.source}")
        if item.published_at:
            context.append(f"Published: {item.published_at}")
        if context:
            line = f"{line} ({', '.join(context)})"
        parts = [f"{line}."]
        if item.snippet:
            parts.append(f"Detail: {item.snippet.strip()}")
        lines.append(" ".join(parts))
    return "\n".join(lines).strip()


def _iter_articles(result: Any) -> Iterable[dict[str, Any]]:
    if not isinstance(result, dict):
        return

    highlight = result.get("highlight")
    if isinstance(highlight, dict):
        yield highlight

    stories = result.get("stories")
    if isinstance(stories, list):
        for story in stories:
            if isinstance(story, dict):
                yield story

    if result.get("title") or result.get("link"):
        yield result


def _to_news_item(article: dict[str, Any]) -> NewsItem | None:
    title = _clean_text(article.get("title"))
    if not title:
        return None

    source = article.get("source", "")
    if isinstance(source, dict):
        source_name = _clean_text(source.get("name"))
    else:
        source_name = _clean_text(source)

    return NewsItem(
        title=title,
        source=source_name,
        link=_clean_text(article.get("link")),
        published_at=_clean_text(article.get("iso_date") or article.get("date")),
        snippet=_clean_text(article.get("snippet") or article.get("description")),
    )


def _clean_text(value: Any) -> str:
    text = str(value or "").strip()
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(text.split())
