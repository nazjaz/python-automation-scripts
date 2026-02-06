"""Process survey responses and extract data."""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

from src.database import DatabaseManager


class ResponseProcessor:
    """Process survey responses from various sources."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize response processor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def import_responses_from_csv(
        self, survey_id: int, file_path: Path
    ) -> Dict[str, any]:
        """Import responses from CSV file.

        Args:
            survey_id: Survey ID.
            file_path: Path to CSV file.

        Returns:
            Dictionary with import results.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        imported_count = 0
        questions = self.db_manager.get_survey_questions(survey_id)

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    respondent_id = row.get("respondent_id", f"respondent_{imported_count}")
                    respondent_email = row.get("respondent_email")

                    response = self.db_manager.add_response(
                        survey_id=survey_id,
                        respondent_id=respondent_id,
                        respondent_email=respondent_email,
                    )

                    for question in questions:
                        answer_value = row.get(f"question_{question.id}")
                        if answer_value:
                            self._add_answer_for_question(
                                response.id, question, answer_value
                            )

                    imported_count += 1
                except Exception:
                    continue

        return {
            "success": True,
            "imported_count": imported_count,
            "file_path": str(file_path),
        }

    def _add_answer_for_question(
        self, response_id: int, question, answer_value: str
    ) -> None:
        """Add answer for a question.

        Args:
            response_id: Response ID.
            question: Question object.
            answer_value: Answer value from CSV.
        """
        if question.question_type == "rating":
            try:
                numeric_value = float(answer_value)
                self.db_manager.add_answer(
                    response_id=response_id,
                    question_id=question.id,
                    answer_value=numeric_value,
                )
            except ValueError:
                self.db_manager.add_answer(
                    response_id=response_id,
                    question_id=question.id,
                    answer_text=answer_value,
                )
        elif question.question_type == "multiple_choice":
            self.db_manager.add_answer(
                response_id=response_id,
                question_id=question.id,
                answer_choice=answer_value,
            )
        else:
            self.db_manager.add_answer(
                response_id=response_id,
                question_id=question.id,
                answer_text=answer_value,
            )

    def import_responses_from_json(
        self, survey_id: int, file_path: Path
    ) -> Dict[str, any]:
        """Import responses from JSON file.

        Args:
            survey_id: Survey ID.
            file_path: Path to JSON file.

        Returns:
            Dictionary with import results.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        imported_count = 0
        questions = self.db_manager.get_survey_questions(survey_id)

        if isinstance(data, list):
            responses_data = data
        elif isinstance(data, dict) and "responses" in data:
            responses_data = data["responses"]
        else:
            responses_data = [data]

        for response_data in responses_data:
            try:
                respondent_id = response_data.get("respondent_id", f"respondent_{imported_count}")
                respondent_email = response_data.get("respondent_email")

                response = self.db_manager.add_response(
                    survey_id=survey_id,
                    respondent_id=respondent_id,
                    respondent_email=respondent_email,
                )

                answers_data = response_data.get("answers", {})
                for question in questions:
                    answer_value = answers_data.get(f"question_{question.id}") or answers_data.get(
                        str(question.id)
                    )
                    if answer_value:
                        self._add_answer_for_question(
                            response.id, question, str(answer_value)
                        )

                imported_count += 1
            except Exception:
                continue

        return {
            "success": True,
            "imported_count": imported_count,
            "file_path": str(file_path),
        }

    def get_response_data(self, response_id: int) -> Dict[str, any]:
        """Get complete response data.

        Args:
            response_id: Response ID.

        Returns:
            Dictionary with response data.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Response

            response = session.query(Response).filter(Response.id == response_id).first()
            if not response:
                return {}

            answers_data = []
            for answer in response.answers:
                answers_data.append({
                    "question_id": answer.question_id,
                    "answer_text": answer.answer_text,
                    "answer_value": answer.answer_value,
                    "answer_choice": answer.answer_choice,
                })

            return {
                "id": response.id,
                "survey_id": response.survey_id,
                "respondent_id": response.respondent_id,
                "respondent_email": response.respondent_email,
                "submitted_at": response.submitted_at,
                "satisfaction_score": response.satisfaction_score,
                "answers": answers_data,
            }
        finally:
            session.close()

    def get_all_responses_data(
        self, survey_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """Get all responses data for a survey.

        Args:
            survey_id: Survey ID.
            limit: Maximum number of responses to return.

        Returns:
            List of response data dictionaries.
        """
        responses = self.db_manager.get_survey_responses(survey_id, limit=limit)
        return [self.get_response_data(response.id) for response in responses]
