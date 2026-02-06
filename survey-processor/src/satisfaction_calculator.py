"""Calculate satisfaction scores from survey responses."""

from typing import Dict, List, Optional

from src.database import DatabaseManager


class SatisfactionCalculator:
    """Calculate satisfaction scores."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize satisfaction calculator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.rating_questions_weight = config.get("rating_questions_weight", 0.7)
        self.choice_questions_weight = config.get("choice_questions_weight", 0.3)

    def calculate_satisfaction_scores(self, survey_id: int) -> Dict[str, any]:
        """Calculate satisfaction scores for all responses.

        Args:
            survey_id: Survey ID.

        Returns:
            Dictionary with calculation results.
        """
        responses = self.db_manager.get_survey_responses(survey_id)
        questions = self.db_manager.get_survey_questions(survey_id)

        rating_questions = [
            q for q in questions if q.question_type == "rating"
        ]

        calculated_count = 0
        for response in responses:
            satisfaction_score = self._calculate_response_satisfaction(
                response, rating_questions
            )
            if satisfaction_score is not None:
                self.db_manager.update_response_satisfaction(
                    response.id, satisfaction_score
                )
                calculated_count += 1

        return {
            "success": True,
            "calculated_count": calculated_count,
            "total_responses": len(responses),
        }

    def _calculate_response_satisfaction(
        self, response, rating_questions: List
    ) -> Optional[float]:
        """Calculate satisfaction score for a single response.

        Args:
            response: Response object.
            rating_questions: List of rating question objects.

        Returns:
            Satisfaction score (0.0 to 5.0) or None.
        """
        if not rating_questions:
            return None

        rating_values = []
        for question in rating_questions:
            for answer in response.answers:
                if answer.question_id == question.id and answer.answer_value is not None:
                    rating_values.append(answer.answer_value)
                    break

        if not rating_values:
            return None

        average_rating = sum(rating_values) / len(rating_values)
        return average_rating

    def calculate_average_satisfaction(self, survey_id: int) -> float:
        """Calculate average satisfaction score for survey.

        Args:
            survey_id: Survey ID.

        Returns:
            Average satisfaction score.
        """
        responses = self.db_manager.get_survey_responses(survey_id)

        satisfaction_scores = [
            r.satisfaction_score
            for r in responses
            if r.satisfaction_score is not None
        ]

        if not satisfaction_scores:
            return 0.0

        return sum(satisfaction_scores) / len(satisfaction_scores)

    def get_satisfaction_distribution(self, survey_id: int) -> Dict[str, int]:
        """Get satisfaction score distribution.

        Args:
            survey_id: Survey ID.

        Returns:
            Dictionary with satisfaction distribution.
        """
        responses = self.db_manager.get_survey_responses(survey_id)

        distribution = {
            "very_satisfied": 0,
            "satisfied": 0,
            "neutral": 0,
            "dissatisfied": 0,
            "very_dissatisfied": 0,
        }

        for response in responses:
            if response.satisfaction_score is not None:
                score = response.satisfaction_score
                if score >= 4.5:
                    distribution["very_satisfied"] += 1
                elif score >= 3.5:
                    distribution["satisfied"] += 1
                elif score >= 2.5:
                    distribution["neutral"] += 1
                elif score >= 1.5:
                    distribution["dissatisfied"] += 1
                else:
                    distribution["very_dissatisfied"] += 1

        return distribution

    def get_satisfaction_statistics(self, survey_id: int) -> Dict[str, any]:
        """Get comprehensive satisfaction statistics.

        Args:
            survey_id: Survey ID.

        Returns:
            Dictionary with satisfaction statistics.
        """
        responses = self.db_manager.get_survey_responses(survey_id)

        satisfaction_scores = [
            r.satisfaction_score
            for r in responses
            if r.satisfaction_score is not None
        ]

        if not satisfaction_scores:
            return {
                "average": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
                "total_responses": len(responses),
                "responses_with_score": 0,
            }

        sorted_scores = sorted(satisfaction_scores)
        median = sorted_scores[len(sorted_scores) // 2]

        return {
            "average": sum(satisfaction_scores) / len(satisfaction_scores),
            "median": median,
            "min": min(satisfaction_scores),
            "max": max(satisfaction_scores),
            "total_responses": len(responses),
            "responses_with_score": len(satisfaction_scores),
            "distribution": self.get_satisfaction_distribution(survey_id),
        }
