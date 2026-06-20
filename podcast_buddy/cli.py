from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path

from .config import DEFAULT_SUMMARY_MODEL, Settings, load_dotenv
from .episode import create_episode
from .script import DEFAULT_HOST_A, DEFAULT_HOST_B
from .summarizer import SummarizationError

# Tumhare model ka default absolute path
CUSTOM_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/custom_summarizer"))
UNIQUE_MODEL_NAME = "Podcast-Buddy-Brain-v1"

def build_parser(settings: Settings) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="podcast-buddy",
        description="Create a two-host Q&A news podcast script using SerpAPI and your custom AI model.",
    )
    parser.add_argument("topic", help="News topic or search query")
    parser.add_argument("--limit", type=int, default=8, help="Maximum news items to use")
    parser.add_argument("--gl", default=settings.serpapi_gl, help="Google News country code")
    parser.add_argument("--hl", default=settings.serpapi_hl, help="Google News language code")
    parser.add_argument("--serpapi-key", default=settings.serpapi_key, help=argparse.SUPPRESS)
    parser.add_argument("--news-json", type=Path, help="Use a saved SerpAPI JSON response")

    parser.add_argument(
        "--summarizer",
        choices=["auto", "transformers", "extractive"],
        default="auto",
        help="Summarization strategy.",
    )

    parser.add_argument(
        "--summary-model",
        default=CUSTOM_MODEL_PATH,
        help="Path to the Hugging Face seq2seq model",
    )

    parser.add_argument("--max-summary-words", type=int, default=160)
    parser.add_argument("--host-a-name", default=DEFAULT_HOST_A.name)
    parser.add_argument("--host-b-name", default=DEFAULT_HOST_B.name)
    parser.add_argument("--output-dir", type=Path, default=settings.output_dir)
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    settings = Settings.from_env()
    parser = build_parser(settings)
    args = parser.parse_args(argv)

    if args.limit < 1:
        parser.error("--limit must be at least 1")

    if not os.path.exists(args.summary_model):
        print(f"Warning: Custom model path '{args.summary_model}' nahi mila. Fallback ho sakta hai.", file=sys.stderr)

    try:
        episode = create_episode(
            topic=args.topic,
            limit=args.limit,
            gl=args.gl,
            hl=args.hl,
            serpapi_key=args.serpapi_key,
            news_json=args.news_json,
            summarizer=args.summarizer,
            summary_model=args.summary_model,
            max_summary_words=args.max_summary_words,
            host_a_name=args.host_a_name,
            host_b_name=args.host_b_name,
            output_dir=args.output_dir,
        )
    except SummarizationError as exc:
        print(f"Summarization failed: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Podcast Buddy failed: {exc}", file=sys.stderr)
        return 1

    if episode.summary_result.fallback_used:
        print("Note: local Transformers summarizer was unavailable, so extractive-local fallback was used.",
              file=sys.stderr)

    # --- FINAL DISPLAY LOGIC ---
    display_model_name = episode.summary_result.model
    if display_model_name and os.path.normpath(display_model_name) == os.path.normpath(CUSTOM_MODEL_PATH):
        display_model_name = UNIQUE_MODEL_NAME

    print(f"Podcast generated successfully using: {display_model_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())