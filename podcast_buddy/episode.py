from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import DEFAULT_SUMMARY_MODEL
from .news import NewsItem, SerpApiNewsClient, format_news_brief, load_news_json
from .script import DEFAULT_HOST_A, DEFAULT_HOST_B, Host, build_conversation, render_summary_markdown
from .storage import save_episode_outputs
from .summarizer import SummaryResult, summarize_text

# Unique Identity Configuration
CUSTOM_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/custom_summarizer"))
UNIQUE_MODEL_NAME = "Podcast-Buddy-Brain-v1"


@dataclass(frozen=True)
class EpisodeResult:
    topic: str
    conversation_markdown: str
    summary_markdown: str
    news_items: list[NewsItem]
    summary_result: SummaryResult
    paths: dict[str, Path]


def create_episode(
        *,
        topic: str,
        limit: int = 8,
        gl: str = "us",
        hl: str = "en",
        serpapi_key: str | None = None,
        news_json: Path | None = None,
        summarizer: str = "auto",
        summary_model: str = DEFAULT_SUMMARY_MODEL,
        max_summary_words: int = 160,
        host_a_name: str = DEFAULT_HOST_A.name,
        host_b_name: str = DEFAULT_HOST_B.name,
        output_dir: Path = Path("outputs"),
) -> EpisodeResult:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if not topic.strip():
        raise ValueError("topic is required")

    if news_json:
        news_items = load_news_json(news_json)[:limit]
    else:
        if not serpapi_key:
            raise ValueError("SERPAPI_KEY is required unless news_json is provided")
        client = SerpApiNewsClient(serpapi_key)
        news_items = client.search(topic, limit=limit, gl=gl, hl=hl)

    if not news_items:
        raise ValueError("No news items were found for this topic")

    brief = format_news_brief(topic, news_items)
    summary_result = summarize_text(
        brief,
        strategy=summarizer,
        model_name=summary_model,
        max_words=max_summary_words,
    )

    # --- MODEL NAME OVERRIDE LOGIC ---
    final_model_name = summary_result.model
    if final_model_name and os.path.normpath(final_model_name) == os.path.normpath(CUSTOM_MODEL_PATH):
        final_model_name = UNIQUE_MODEL_NAME

    # Create an updated result object with the unique name
    summary_result_updated = SummaryResult(
        text=summary_result.text,
        engine=summary_result.engine,
        model=final_model_name,
        fallback_used=summary_result.fallback_used
    )

    generated_at = datetime.now(timezone.utc)
    host_a = Host(code="Host A", name=host_a_name, gender="Male", role="questioner")
    host_b = Host(code="Host B", name=host_b_name, gender="Female", role="explainer")

    conversation = build_conversation(
        topic=topic,
        summary=summary_result_updated.text,
        news_items=news_items,
        host_a=host_a,
        host_b=host_b,
        generated_at=generated_at,
    )

    summary_markdown = render_summary_markdown(
        topic=topic,
        summary=summary_result_updated.text,
        news_items=news_items,
        summarizer_engine=summary_result_updated.engine,
        summarizer_model=summary_result_updated.model,
        generated_at=generated_at,
    )

    paths = save_episode_outputs(
        topic=topic,
        conversation_markdown=conversation,
        summary_markdown=summary_markdown,
        news_items=news_items,
        output_dir=output_dir,
        generated_at=generated_at,
        metadata={
            "gl": gl,
            "hl": hl,
            "summarizer": summary_result_updated.engine,
            "model": summary_result_updated.model,
            "fallback_used": summary_result_updated.fallback_used,
            "paid_models_used": False,
        },
    )

    return EpisodeResult(
        topic=topic,
        conversation_markdown=conversation,
        summary_markdown=summary_markdown,
        news_items=list(news_items),
        summary_result=summary_result_updated,
        paths=paths,
    )