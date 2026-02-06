"""Identify trends in survey responses."""

from collections import Counter
from typing import Dict, List, Optional

from src.database import DatabaseManager


class TrendIdentifier:
    """Identify trends in survey responses."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize trend identifier.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.min_occurrences = config.get("min_occurrences", 3)
        self.confidence_threshold = config.get("confidence_threshold", 0.6)

    def identify_trends(self, survey_id: int) -> List[Dict[str, any]]:
        """Identify trends in survey responses.

        Args:
            survey_id: Survey ID.

        Returns:
            List of trend dictionaries.
        """
        responses = self.db_manager.get_survey_responses(survey_id)
        questions = self.db_manager.get_survey_questions(survey_id)

        if not responses:
            return []

        trends = []

        for question in questions:
            question_trends = self._identify_question_trends(question, responses)
            trends.extend(question_trends)

        overall_trends = self._identify_overall_trends(survey_id, responses)
        trends.extend(overall_trends)

        for trend in trends:
            self.db_manager.add_trend(
                survey_id=survey_id,
                trend_name=trend["trend_name"],
                trend_type=trend["trend_type"],
                description=trend["description"],
                confidence_score=trend["confidence_score"],
            )

        return trends

    def _identify_question_trends(self, question, responses: List) -> List[Dict[str, any]]:
        """Identify trends for a specific question.

        Args:
            question: Question object.
            responses: List of response objects.

        Returns:
            List of trend dictionaries.
        """
        trends = []
        answers = []
        for response in responses:
            for answer in response.answers:
                if answer.question_id == question.id:
                    answers.append(answer)

        if question.question_type == "rating":
            rating_trend = self._identify_rating_trend(question, answers)
            if rating_trend:
                trends.append(rating_trend)
        elif question.question_type == "multiple_choice":
            choice_trend = self._identify_choice_trend(question, answers)
            if choice_trend:
                trends.append(choice_trend)

        return trends

    def _identify_rating_trend(self, question, answers: List) -> Optional[Dict[str, any]]:
        """Identify trend in rating question.

        Args:
            question: Question object.
            answers: List of answer objects.

        Returns:
            Trend dictionary or None.
        """
        values = [a.answer_value for a in answers if a.answer_value is not None]
        if not values or len(values) < self.min_occurrences:
            return None

        average = sum(values) / len(values)

        if average >= 4.0:
            trend_type = "positive"
            description = f"High ratings for '{question.question_text}' (average: {average:.2f})"
        elif average <= 2.0:
            trend_type = "negative"
            description = f"Low ratings for '{question.question_text}' (average: {average:.2f})"
        else:
            trend_type = "neutral"
            description = f"Moderate ratings for '{question.question_text}' (average: {average:.2f})"

        confidence = min(len(values) / 10.0, 1.0)

        return {
            "trend_name": f"Rating Trend: {question.question_text[:50]}",
            "trend_type": trend_type,
            "description": description,
            "confidence_score": confidence,
        }

    def _identify_choice_trend(self, question, answers: List) -> Optional[Dict[str, any]]:
        """Identify trend in multiple choice question.

        Args:
            question: Question object.
            answers: List of answer objects.

        Returns:
            Trend dictionary or None.
        """
        choices = [a.answer_choice for a in answers if a.answer_choice]
        if not choices or len(choices) < self.min_occurrences:
            return None

        choice_counts = Counter(choices)
        most_common = choice_counts.most_common(1)[0]
        most_common_choice, count = most_common

        percentage = count / len(choices)

        if percentage >= 0.5:
            trend_type = "dominant"
            description = (
                f"'{most_common_choice}' is the dominant choice "
                f"({percentage:.1%}) for '{question.question_text}'"
            )
        else:
            trend_type = "distributed"
            description = (
                f"Choices are distributed for '{question.question_text}' "
                f"(most common: {most_common_choice} at {percentage:.1%})"
            )

        confidence = min(len(choices) / 10.0, 1.0)

        return {
            "trend_name": f"Choice Trend: {question.question_text[:50]}",
            "trend_type": trend_type,
            "description": description,
            "confidence_score": confidence,
        }

    def _identify_overall_trends(
        self, survey_id: int, responses: List
    ) -> List[Dict[str, any]]:
        """Identify overall trends across survey.

        Args:
            survey_id: Survey ID.
            responses: List of response objects.

        Returns:
            List of trend dictionaries.
        """
        trends = []

        satisfaction_scores = [
            r.satisfaction_score for r in responses if r.satisfaction_score is not None
        ]

        if satisfaction_scores and len(satisfaction_scores) >= self.min_occurrences:
            avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)

            if avg_satisfaction >= 4.0:
                trend_type = "positive"
                description = f"High overall satisfaction (average: {avg_satisfaction:.2f})"
            elif avg_satisfaction <= 2.0:
                trend_type = "negative"
                description = f"Low overall satisfaction (average: {avg_satisfaction:.2f})"
            else:
                trend_type = "neutral"
                description = f"Moderate overall satisfaction (average: {avg_satisfaction:.2f})"

            confidence = min(len(satisfaction_scores) / 20.0, 1.0)

            trends.append({
                "trend_name": "Overall Satisfaction Trend",
                "trend_type": trend_type,
                "description": description,
                "confidence_score": confidence,
            })

        response_count = len(responses)
        if response_count >= 50:
            trends.append({
                "trend_name": "High Response Rate",
                "trend_type": "positive",
                "description": f"Survey received {response_count} responses",
                "confidence_score": 1.0,
            })

        return trends
