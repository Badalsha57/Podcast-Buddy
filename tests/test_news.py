import json
import unittest
from pathlib import Path

from podcast_buddy.news import format_news_brief, parse_news_results


class NewsParsingTests(unittest.TestCase):
    def test_parse_google_news_groups_and_stories(self) -> None:
        payload = json.loads(Path("tests/fixtures/sample_serpapi_news.json").read_text())

        items = parse_news_results(payload, limit=3)

        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].title, "AI startup announces new safety benchmark")
        self.assertEqual(items[1].source, "Policy Wire")
        self.assertEqual(items[2].link, "https://example.com/ai-disclosure-prompts")

    def test_format_news_brief_contains_topic_and_sources(self) -> None:
        payload = json.loads(Path("tests/fixtures/sample_serpapi_news.json").read_text())
        items = parse_news_results(payload, limit=1)

        brief = format_news_brief("AI news", items)

        self.assertIn("News topic: AI news", brief)
        self.assertIn("Source: Tech Daily", brief)


if __name__ == "__main__":
    unittest.main()
