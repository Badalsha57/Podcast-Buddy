import unittest

from podcast_buddy.summarizer import extractive_summarize, summarize_text


class SummarizerTests(unittest.TestCase):
    def test_extractive_summary_limits_words(self) -> None:
        text = (
            "AI policy is moving quickly. Startups are shipping new tools. "
            "Regulators are studying safety labels. Users want clearer disclosures."
        )

        summary = extractive_summarize(text, max_words=12)

        self.assertLessEqual(len(summary.split()), 13)
        self.assertTrue(summary)

    def test_explicit_extractive_strategy_uses_no_paid_model(self) -> None:
        result = summarize_text(
            "AI policy is moving quickly. Regulators are studying safety labels.",
            strategy="extractive",
            max_words=20,
        )

        self.assertEqual(result.engine, "extractive-local")
        self.assertIsNone(result.model)
        self.assertFalse(result.fallback_used)


if __name__ == "__main__":
    unittest.main()
