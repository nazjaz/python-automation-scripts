"""Analyze survey responses."""

from collections import Counter
from typing import Dict, List, Optional

from src.database import DatabaseManager


class SurveyAnalyzer:
    """Analyze survey responses."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize survey analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def analyze_survey(self, survey_id: int) -> Dict[str, any]:
        """Analyze survey responses.

        Args:
            survey_id: Survey ID.

        Returns:
            Dictionary with analysis results.
        """
        responses = self.db_manager.get_survey_responses(survey_id)
        questions = self.db_manager.get_survey_questions(survey_id)

        if not responses:
            return {
                "survey_id": survey_id,
                "total_responses": 0,
                "question_analyses": [],
            }

        question_analyses = []
        for question in questions:
            analysis = self._analyze_question(question, responses)
            question_analyses.append(analysis)

        return {
            "survey_id": survey_id,
            "total_responses": len(responses),
            "question_analyses": question_analyses,
        }

    def _analyze_question(self, question, responses: List) -> Dict[str, any]:
        """Analyze a single question.

        Args:
            question: Question object.
            responses: List of response objects.

        Returns:
            Dictionary with question analysis.
        """
        answers = []
        for response in responses:
            for answer in response.answers:
                if answer.question_id == question.id:
                    answers.append(answer)

        if question.question_type == "rating":
            return self._analyze_rating_question(question, answers)
        elif question.question_type == "multiple_choice":
            return self._analyze_multiple_choice_question(question, answers)
        else:
            return self._analyze_text_question(question, answers)

    def _analyze_rating_question(self, question, answers: List) -> Dict[str, any]:
        """Analyze rating question.

        Args:
            question: Question object.
            answers: List of answer objects.

        Returns:
            Dictionary with rating analysis.
        """
        values = [a.answer_value for a in answers if a.answer_value is not None]

        if not values:
            return {
                "question_id": question.id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "total_answers": len(answers),
                "average": 0.0,
                "min": 0.0,
                "max": 0.0,
            }

        return {
            "question_id": question.id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "total_answers": len(answers),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "median": sorted(values)[len(values) // 2] if values else 0.0,
        }

    def _analyze_multiple_choice_question(
        self, question, answers: List
    ) -> Dict[str, any]:
        """Analyze multiple choice question.

        Args:
            question: Question object.
            answers: List of answer objects.

        Returns:
            Dictionary with multiple choice analysis.
        """
        choices = [a.answer_choice for a in answers if a.answer_choice]
        choice_counts = Counter(choices)

        return {
            "question_id": question.id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "total_answers": len(answers),
            "choice_distribution": dict(choice_counts),
            "most_common": choice_counts.most_common(1)[0][0] if choice_counts else None,
        }

    def _analyze_text_question(self, question, answers: List) -> Dict[str, any]:
        """Analyze text question.

        Args:
            question: Question object.
            answers: List of answer objects.

        Returns:
            Dictionary with text analysis.
        """
        texts = [a.answer_text for a in answers if a.answer_text]
        word_counts = []
        for text in texts:
            if text:
                word_counts.append(len(text.split()))

        return {
            "question_id": question.id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "total_answers": len(answers),
            "average_word_count": (
                sum(word_counts) / len(word_counts) if word_counts else 0.0
            ),
            "sample_responses": texts[:5] if texts else [],
        }

    def get_response_statistics(self, survey_id: int) -> Dict[str, any]:
        """Get response statistics.

        Args:
            survey_id: Survey ID.

        Returns:
            Dictionary with response statistics.
        """
        responses = self.db_manager.get_survey_responses(survey_id)

        satisfaction_scores = [
            r.satisfaction_score for r in responses if r.satisfaction_score is not None
        ]

        return {
            "total_responses": len(responses),
            "responses_with_satisfaction": len(satisfaction_scores),
            "average_satisfaction": (
                sum(satisfaction_scores) / len(satisfaction_scores)
                if satisfaction_scores
                else 0.0
            ),
            "min_satisfaction": min(satisfaction_scores) if satisfaction_scores else 0.0,
            "max_satisfaction": max(satisfaction_scores) if satisfaction_scores else 0.0,
        }
