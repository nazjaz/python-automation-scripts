"""Identify error patterns and trends."""

import hashlib
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class PatternIdentifier:
    """Identify patterns in error logs."""

    def __init__(self, config: Dict):
        """Initialize pattern identifier.

        Args:
            config: Configuration dictionary with pattern identification settings.
        """
        self.config = config
        self.min_frequency = config.get("min_frequency", 3)
        self.similarity_threshold = config.get("similarity_threshold", 0.8)

    def identify_patterns(self, errors: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Identify error patterns from error list.

        Args:
            errors: List of error dictionaries.

        Returns:
            List of pattern dictionaries.
        """
        if not errors:
            return []

        error_signatures = {}
        for error in errors:
            signature = self._create_error_signature(error)
            if signature not in error_signatures:
                error_signatures[signature] = []
            error_signatures[signature].append(error)

        patterns = []
        for signature, signature_errors in error_signatures.items():
            if len(signature_errors) >= self.min_frequency:
                pattern = self._create_pattern(signature, signature_errors)
                patterns.append(pattern)

        patterns.sort(key=lambda x: x.get("frequency", 0), reverse=True)

        return patterns

    def _create_error_signature(self, error: Dict[str, any]) -> str:
        """Create error signature for pattern matching.

        Args:
            error: Error dictionary.

        Returns:
            Error signature string.
        """
        error_message = error.get("error_message", "")
        error_type = error.get("error_type", "")

        normalized_message = self._normalize_error_message(error_message)
        signature_parts = [error_type, normalized_message]

        signature = "|".join(s for s in signature_parts if s)

        return hashlib.md5(signature.encode()).hexdigest()

    def _normalize_error_message(self, message: str) -> str:
        """Normalize error message for pattern matching.

        Args:
            message: Error message.

        Returns:
            Normalized message.
        """
        message = message.lower()

        message = re.sub(r"\d+", "N", message)
        message = re.sub(r"0x[0-9a-f]+", "HEX", message)
        message = re.sub(r"['\"][^'\"]*['\"]", "STRING", message)
        message = re.sub(r"\s+", " ", message)

        return message.strip()

    def _create_pattern(self, signature: str, errors: List[Dict[str, any]]) -> Dict[str, any]:
        """Create pattern from error signature and errors.

        Args:
            signature: Error signature.
            errors: List of errors with this signature.

        Returns:
            Pattern dictionary.
        """
        timestamps = [
            error.get("timestamp", datetime.utcnow())
            for error in errors
            if error.get("timestamp")
        ]

        first_seen = min(timestamps) if timestamps else datetime.utcnow()
        last_seen = max(timestamps) if timestamps else datetime.utcnow()

        trend = self._calculate_trend(timestamps)

        sample_error = errors[0]
        error_message = sample_error.get("error_message", "")
        error_type = sample_error.get("error_type", "")

        return {
            "pattern_name": f"{error_type or 'Error'}: {error_message[:100]}",
            "error_signature": signature,
            "pattern_description": f"Pattern identified from {len(errors)} occurrences",
            "frequency": len(errors),
            "first_seen": first_seen,
            "last_seen": last_seen,
            "trend": trend,
            "error_type": error_type,
            "error_message": error_message,
        }

    def _calculate_trend(self, timestamps: List[datetime]) -> str:
        """Calculate error trend.

        Args:
            timestamps: List of error timestamps.

        Returns:
            Trend indicator (increasing, decreasing, stable).
        """
        if len(timestamps) < 2:
            return "stable"

        timestamps.sort()
        mid_point = len(timestamps) // 2

        first_half = timestamps[:mid_point]
        second_half = timestamps[mid_point:]

        first_half_count = len(first_half)
        second_half_count = len(second_half)

        time_span_first = (first_half[-1] - first_half[0]).total_seconds() if len(first_half) > 1 else 1
        time_span_second = (second_half[-1] - second_half[0]).total_seconds() if len(second_half) > 1 else 1

        rate_first = first_half_count / time_span_first if time_span_first > 0 else 0
        rate_second = second_half_count / time_span_second if time_span_second > 0 else 0

        if rate_second > rate_first * 1.2:
            return "increasing"
        elif rate_second < rate_first * 0.8:
            return "decreasing"
        else:
            return "stable"

    def find_similar_errors(
        self, target_error: Dict[str, any], all_errors: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """Find errors similar to target error.

        Args:
            target_error: Target error dictionary.
            all_errors: List of all errors.

        Returns:
            List of similar errors.
        """
        target_signature = self._create_error_signature(target_error)
        similar_errors = []

        for error in all_errors:
            signature = self._create_error_signature(error)
            similarity = self._calculate_similarity(target_signature, signature)

            if similarity >= self.similarity_threshold:
                similar_errors.append(error)

        return similar_errors

    def _calculate_similarity(self, signature1: str, signature2: str) -> float:
        """Calculate similarity between two signatures.

        Args:
            signature1: First signature.
            signature2: Second signature.

        Returns:
            Similarity score (0.0 to 1.0).
        """
        if signature1 == signature2:
            return 1.0

        return 0.0
