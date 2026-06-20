from __future__ import annotations
import math
import re
import os
from dataclasses import dataclass
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Root folder se path set karna zaroori hai
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOM_MODEL_PATH = os.path.join(BASE_DIR, "models", "custom_summarizer")

@dataclass(frozen=True)
class SummaryResult:
    text: str
    engine: str
    model: str | None
    fallback_used: bool = False

class SummarizationError(RuntimeError):
    """Raised when a requested summarizer cannot produce a summary."""

STOPWORDS = {"a", "an", "and", "are", "at", "be", "by", "for", "from", "has", "have", "in", "is", "it", "of", "on",
             "or", "that", "the", "this", "to", "with"}

# Global model loading (taaki baar-baar load na ho)
_cached_model = None
_cached_tokenizer = None

def _get_model_components():
    global _cached_model, _cached_tokenizer
    if _cached_model is None:
        _cached_tokenizer = AutoTokenizer.from_pretrained(CUSTOM_MODEL_PATH)
        _cached_model = AutoModelForSeq2SeqLM.from_pretrained(CUSTOM_MODEL_PATH)
        _cached_model.to("cpu")
    return _cached_model, _cached_tokenizer

def summarize_text(text: str, *, strategy: str = "auto", model_name: str = CUSTOM_MODEL_PATH,
                   max_words: int = 160) -> SummaryResult:
    clean_text = _normalize_space(text)
    if not clean_text:
        raise SummarizationError("Cannot summarize empty text")

    if strategy in {"auto", "transformers"}:
        try:
            summary = _summarize_with_transformers(clean_text, max_words=max_words)
            return SummaryResult(text=summary, engine="transformers-local", model=model_name, fallback_used=False)
        except Exception as exc:
            if strategy == "transformers":
                raise SummarizationError(f"Model error: {str(exc)}") from exc

    return SummaryResult(
        text=extractive_summarize(clean_text, max_words=max_words),
        engine="extractive-local",
        model=None,
        fallback_used=strategy == "auto",
    )

def _summarize_with_transformers(text: str, *, max_words: int) -> str:
    model, tokenizer = _get_model_components()
    encoded = tokenizer(text, max_length=512, truncation=True, return_tensors="pt")
    output_ids = model.generate(
        encoded["input_ids"],
        max_length=max_words,
        min_length=20,
        num_beams=4,
        length_penalty=1.0,
        repetition_penalty=2.0,
        early_stopping=True,
    )
    summary = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return _limit_words(_normalize_space(summary), max_words)

# [NOTE: Extractive functions (extractive_summarize, _split_sentences, etc.) remain as per your code]
def extractive_summarize(text: str, *, max_words: int = 160) -> str:
    sentences = _split_sentences(text)
    if not sentences: return _limit_words(text, max_words)
    frequencies = {w: 1 for w in _words(text) if w not in STOPWORDS}
    scored = []
    for i, s in enumerate(sentences):
        words = [w for w in _words(s) if w not in STOPWORDS]
        if words:
            score = sum(frequencies.get(w, 0) for w in words) / math.sqrt(len(words))
            scored.append((i, score, s))
    keep_count = min(max(3, max_words // 35), len(sentences))
    best_indexes = {i for i, _, _ in sorted(scored, key=lambda x: x[1], reverse=True)[:keep_count]}
    chosen = [s for i, s in enumerate(sentences) if i in best_indexes]
    return _limit_words(" ".join(chosen), max_words)

def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())

def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def _limit_words(text: str, max_words: int) -> str:
    words = text.split()
    return " ".join(words[:max_words]).rstrip(".,;:") + "..." if len(words) > max_words else text