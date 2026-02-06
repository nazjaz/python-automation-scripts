"""Theme extraction from customer reviews."""

import re
from collections import Counter
from typing import Dict, List, Set

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)


class ThemeExtractor:
    """Extract key themes from customer reviews."""

    def __init__(self, config: Dict):
        """Initialize theme extractor.

        Args:
            config: Configuration dictionary with theme extraction settings.
        """
        self.config = config
        self.stop_words = set(stopwords.words("english"))
        self.theme_categories = config.get("theme_categories", {})
        self.min_theme_length = config.get("min_theme_length", 2)
        self.max_themes_per_review = config.get("max_themes_per_review", 5)

    def extract_themes(self, review_text: str) -> List[Dict[str, any]]:
        """Extract key themes from review text.

        Args:
            review_text: Review text to analyze.

        Returns:
            List of theme dictionaries with text, relevance_score, and category.
        """
        if not review_text or len(review_text.strip()) < 10:
            return []

        sentences = sent_tokenize(review_text)
        word_frequencies = self._calculate_word_frequencies(review_text)
        sentence_scores = self._score_sentences(sentences, word_frequencies)

        top_sentences = sorted(
            sentence_scores.items(), key=lambda x: x[1], reverse=True
        )[: self.max_themes_per_review]

        themes = []
        for sentence, score in top_sentences:
            if len(sentence.split()) >= self.min_theme_length:
                category = self._categorize_theme(sentence)
                themes.append(
                    {
                        "theme_text": sentence.strip(),
                        "relevance_score": score,
                        "category": category,
                    }
                )

        return themes

    def _calculate_word_frequencies(self, text: str) -> Dict[str, float]:
        """Calculate word frequencies in text.

        Args:
            text: Text to analyze.

        Returns:
            Dictionary mapping words to their frequency scores.
        """
        words = word_tokenize(text.lower())
        filtered_words = [
            word for word in words if word.isalnum() and word not in self.stop_words
        ]

        word_counts = Counter(filtered_words)
        max_count = max(word_counts.values()) if word_counts else 1

        word_frequencies = {
            word: count / max_count for word, count in word_counts.items()
        }

        return word_frequencies

    def _score_sentences(
        self, sentences: List[str], word_frequencies: Dict[str, float]
    ) -> Dict[str, float]:
        """Score sentences based on word frequencies.

        Args:
            sentences: List of sentences.
            word_frequencies: Word frequency dictionary.

        Returns:
            Dictionary mapping sentences to their scores.
        """
        sentence_scores = {}
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            filtered_words = [
                word
                for word in words
                if word.isalnum() and word not in self.stop_words
            ]

            if not filtered_words:
                continue

            score = sum(word_frequencies.get(word, 0) for word in filtered_words)
            score = score / len(filtered_words) if filtered_words else 0

            sentence_scores[sentence] = score

        return sentence_scores

    def _categorize_theme(self, theme_text: str) -> str:
        """Categorize theme based on keywords.

        Args:
            theme_text: Theme text to categorize.

        Returns:
            Theme category name.
        """
        theme_lower = theme_text.lower()

        for category, keywords in self.theme_categories.items():
            for keyword in keywords:
                if keyword.lower() in theme_lower:
                    return category

        return "general"

    def extract_key_phrases(self, review_text: str, top_n: int = 5) -> List[str]:
        """Extract key phrases from review text.

        Args:
            review_text: Review text to analyze.
            top_n: Number of key phrases to return.

        Returns:
            List of key phrases.
        """
        if not review_text:
            return []

        words = word_tokenize(review_text.lower())
        filtered_words = [
            word for word in words if word.isalnum() and word not in self.stop_words
        ]

        bigrams = [
            f"{filtered_words[i]} {filtered_words[i + 1]}"
            for i in range(len(filtered_words) - 1)
        ]

        phrase_counts = Counter(bigrams)
        top_phrases = [phrase for phrase, _ in phrase_counts.most_common(top_n)]

        return top_phrases
