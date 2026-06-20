from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from .news import NewsItem


@dataclass(frozen=True)
class Host:
    code: str
    name: str
    gender: str
    role: str

    @property
    def label(self) -> str:
        return self.name


DEFAULT_HOST_A = Host(code="Host A", name="Aarav", gender="Male", role="questioner")
DEFAULT_HOST_B = Host(code="Host B", name="Meera", gender="Female", role="explainer")


def build_conversation(
        *,
        topic: str,
        summary: str,
        news_items: Sequence[NewsItem],
        host_a: Host = DEFAULT_HOST_A,
        host_b: Host = DEFAULT_HOST_B,
        max_segments: int = 1000,
        generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now(timezone.utc)
    points = _summary_points(summary)

    # Filter out duplicate news items to prevent repeating the same data
    seen_titles = set()
    unique_items = []
    for item in news_items:
        clean_title = item.title.strip().lower() if item.title else ""
        if clean_title and clean_title not in seen_titles:
            seen_titles.add(clean_title)
            unique_items.append(item)

    # Slice sequence up to the maximum configured segments limit
    selected_items = list(unique_items[:max_segments])

    lines = [
        f"# Podcast Conversation: {topic}",
        "",
        f"Generated: {generated_at.isoformat()}",
        "",
        f"**{host_a.label}:** Welcome back everyone. Today we are breaking down the critical updates surrounding {topic}.",
        f"**{host_b.label}:** That's right. I will be summarizing each development in clear, direct terms.",
        "",
    ]

    for index, item in enumerate(selected_items, start=1):
        headline = item.title[:120].strip() if item.title else "this update"

        # Host A ke dynamic conversational questions
        dynamic_questions = [
            f"Meera, what's the core update regarding '{headline}'?",
            f"Let's focus on this story: '{headline}'. What new details have emerged here?",
            f"What are the major takeaways concerning '{headline}'?",
            f"Next on our list is: '{headline}'. What kind of impact should we look out for?",
            f"What do our listeners need to know about '{headline}' right now?"
        ]

        question = dynamic_questions[(index - 1) % len(dynamic_questions)]

        # Sahi modular index context ke liye safe-check laga diya hai
        point = _clean_point(points[(index - 1) % len(points)] if points else summary)

        # FIX: Ab answer generation purely item-specific context ke mutabik chalega
        answer = _answer_for_item(item=item, point=point, index=index)

        lines.extend(
            [
                f"## Segment {index}",
                "",
                f"**{host_a.label}:** {question}",
                f"**{host_b.label}:** {answer}",
                "",
            ]
        )

    # Wrap up script segment execution
    lines.extend(
        [
            "## Wrap",
            "",
            f"**{host_a.label}:** This was an insightful discussion. Meera, what is our final macro takeaway?",
            f"**{host_b.label}:** To put it all in perspective: {summary}",
        ]
    )

    return "\n".join(lines).strip() + "\n"


def render_summary_markdown(
        *,
        topic: str,
        summary: str,
        news_items: Sequence[NewsItem],
        summarizer_engine: str,
        summarizer_model: str | None,
        generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now(timezone.utc)
    lines = [
        f"# News Summary: {topic}",
        "",
        f"Generated: {generated_at.isoformat()}",
        f"Summarizer: {summarizer_engine}",
    ]
    if summarizer_model:
        lines.append(f"Model: {summarizer_model}")

    lines.extend(["", "## Summary", "", summary, "", "## Sources", ""])
    for index, item in enumerate(news_items, start=1):
        source = f" - {item.source}" if item.source else ""
        date = f" ({item.published_at})" if item.published_at else ""
        link = f" - {item.link}" if item.link else ""
        lines.append(f"{index}. {item.title}{source}{date}{link}")

    return "\n".join(lines).strip() + "\n"


def _summary_points(summary: str) -> list[str]:
    split_pattern = r"(?<=[.!?])\s+|\s*Story\s+\d+:\s*|\s*-\s*"
    points = [
        point.strip()
        for point in re.split(split_pattern, summary)
        if point.strip() and not point.strip().lower().startswith("to put it all")
    ]
    return points or [summary.strip()]


def _clean_point(point: str) -> str:
    point = re.sub(r"\bNews topic:\s*[^.]+\.?", "", point).strip()
    point = re.sub(r"\bStory\s+\d+:\s*", "", point).strip()
    point = re.sub(r"\s*\([^)]*(?:Source|Published):[^)]*\)", "", point).strip()
    return point or "This update adds crucial context to the evolving technical domain."


def _answer_for_item(*, item: NewsItem, point: str, index: int = 1) -> str:
    """Detailed response evaluator formatting clean textual summaries without code leaks."""
    text_source = ""

    if item.snippet and len(item.snippet.strip()) > 20:
        text_source = item.snippet
    elif hasattr(item, 'text') and item.text and len(item.text.strip()) > 20:
        text_source = item.text

    if text_source:
        text = text_source
        text = re.sub(r"(?i)source:.*", "", text)
        text = re.sub(r"(?i)published:.*", "", text)

        if item.title and item.title.lower() in text.lower():
            cleaned_text = re.sub(re.escape(item.title), "", text, flags=re.IGNORECASE).strip()
            if len(cleaned_text.split()) > 3:
                text = cleaned_text

        text = text.strip()

        if point and point.strip() and point.strip().lower() not in text.lower():
            return f"{text}. Looking at the broader perspective, a key aspect to consider is that {point.strip()}"

        return text

    # FIX: Agar snippet/text khali hai, toh random fallbacks use honge taaki repetition na dikhe
    conversational_fallbacks = [
        f"This development marks a significant milestone. It highlights how these new policy frameworks are actively forcing developers and institutions to rethink their compliance strategies.",
        f"The critical thing to note here is the push towards structural auditing. This change means industry players will need to adapt quickly to maintain standard market operations.",
        f"This is generating quite a bit of discussion right now. Essentially, it underscores the tension between pushing for rapid local innovation and implementing macro-level safeguards.",
        f"If you read between the lines, it's all about proactive risk management. This move could very well set a major precedent for upcoming federal and international standards.",
        f"This update really clarifies some underlying technical friction. It shows that setting clear boundaries is becoming a top priority across the board."
    ]

    selected_fallback = conversational_fallbacks[(index - 1) % len(conversational_fallbacks)]
    return f"Regarding the update on '{item.title}'— {selected_fallback} In terms of the bigger picture, {point.strip()}"