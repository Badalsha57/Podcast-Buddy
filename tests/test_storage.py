import tempfile
import unittest
from pathlib import Path

from podcast_buddy.news import NewsItem
from podcast_buddy.storage import save_episode_outputs, slugify


class StorageTests(unittest.TestCase):
    def test_slugify(self) -> None:
        self.assertEqual(slugify("AI Regulation News!"), "ai-regulation-news")

    def test_save_episode_outputs_creates_separate_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = save_episode_outputs(
                topic="AI News",
                conversation_markdown="# Conversation\n",
                summary_markdown="# Summary\n",
                news_items=[NewsItem(title="Headline")],
                output_dir=Path(tmp),
                metadata={"paid_models_used": False},
            )

            self.assertTrue(paths["conversation"].exists())
            self.assertTrue(paths["summary"].exists())
            self.assertTrue(paths["metadata"].exists())
            self.assertNotEqual(paths["conversation"], paths["summary"])


if __name__ == "__main__":
    unittest.main()
