"""Generate personalized fitness challenges."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class ChallengeGenerator:
    """Generate personalized fitness challenges."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize challenge generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.challenge_templates = config.get("challenge_templates", {})
        self.default_duration_days = config.get("default_duration_days", 7)

    def generate_challenge(
        self,
        participant_id: int,
        challenge_type: str,
        duration_days: Optional[int] = None,
        target_value: Optional[float] = None,
    ) -> Dict[str, any]:
        """Generate a personalized challenge.

        Args:
            participant_id: Participant ID.
            challenge_type: Challenge type (steps, distance, calories, workouts, etc.).
            duration_days: Challenge duration in days.
            target_value: Optional target value.

        Returns:
            Dictionary with challenge information.
        """
        participant = self.db_manager.get_participant(participant_id)
        if not participant:
            return {}

        template = self.challenge_templates.get(challenge_type, {})
        challenge_name = template.get("name", f"{challenge_type.replace('_', ' ').title()} Challenge")

        if duration_days is None:
            duration_days = template.get("duration_days", self.default_duration_days)

        if target_value is None:
            target_value = self._calculate_target_value(
                participant, challenge_type, duration_days, template
            )

        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration_days)

        target_unit = template.get("unit", "")

        description = template.get("description", "")
        if not description:
            description = f"Complete {target_value} {target_unit} in {duration_days} days"

        challenge = self.db_manager.create_challenge(
            participant_id=participant_id,
            challenge_name=challenge_name,
            challenge_type=challenge_type,
            start_date=start_date,
            end_date=end_date,
            target_value=target_value,
            target_unit=target_unit,
            description=description,
        )

        return {
            "id": challenge.id,
            "challenge_name": challenge.challenge_name,
            "challenge_type": challenge.challenge_type,
            "target_value": challenge.target_value,
            "target_unit": challenge.target_unit,
            "start_date": challenge.start_date,
            "end_date": challenge.end_date,
            "description": challenge.description,
            "status": challenge.status,
        }

    def _calculate_target_value(
        self,
        participant,
        challenge_type: str,
        duration_days: int,
        template: Dict,
    ) -> float:
        """Calculate target value based on participant profile.

        Args:
            participant: Participant object.
            challenge_type: Challenge type.
            duration_days: Challenge duration.
            template: Challenge template.

        Returns:
            Calculated target value.
        """
        base_value = template.get("base_value", 0)
        fitness_level_multiplier = self._get_fitness_level_multiplier(
            participant.fitness_level
        )

        daily_target = base_value * fitness_level_multiplier
        total_target = daily_target * duration_days

        return total_target

    def _get_fitness_level_multiplier(self, fitness_level: Optional[str]) -> float:
        """Get multiplier based on fitness level.

        Args:
            fitness_level: Fitness level.

        Returns:
            Multiplier value.
        """
        multipliers = {
            "beginner": 0.7,
            "intermediate": 1.0,
            "advanced": 1.5,
        }
        return multipliers.get(fitness_level or "beginner", 1.0)

    def generate_personalized_challenges(
        self, participant_id: int, count: int = 3
    ) -> List[Dict[str, any]]:
        """Generate multiple personalized challenges.

        Args:
            participant_id: Participant ID.
            count: Number of challenges to generate.

        Returns:
            List of challenge dictionaries.
        """
        participant = self.db_manager.get_participant(participant_id)
        if not participant:
            return []

        available_types = list(self.challenge_templates.keys())
        if not available_types:
            available_types = ["steps", "distance", "calories"]

        selected_types = available_types[:count]

        challenges = []
        for challenge_type in selected_types:
            challenge = self.generate_challenge(
                participant_id=participant_id,
                challenge_type=challenge_type,
            )
            if challenge:
                challenges.append(challenge)

        return challenges

    def get_challenge_progress(self, challenge_id: int) -> Dict[str, any]:
        """Get challenge progress information.

        Args:
            challenge_id: Challenge ID.

        Returns:
            Challenge progress dictionary.
        """
        from src.database import Challenge

        session = self.db_manager.get_session()
        try:
            challenge = session.query(Challenge).filter(Challenge.id == challenge_id).first()
            if not challenge:
                return {}

            progress_entries = self.db_manager.get_progress_entries(challenge_id=challenge_id)
            total_progress = sum(pe.value for pe in progress_entries)

            days_remaining = (challenge.end_date - datetime.utcnow()).days
            days_elapsed = (datetime.utcnow() - challenge.start_date).days

            progress_percentage = (
                total_progress / challenge.target_value * 100
                if challenge.target_value and challenge.target_value > 0
                else 0
            )

            return {
                "id": challenge.id,
                "challenge_name": challenge.challenge_name,
                "target_value": challenge.target_value,
                "current_value": total_progress,
                "target_unit": challenge.target_unit,
                "progress_percentage": progress_percentage,
                "days_elapsed": days_elapsed,
                "days_remaining": days_remaining,
                "start_date": challenge.start_date,
                "end_date": challenge.end_date,
                "status": challenge.status,
                "entries_count": len(progress_entries),
            }
        finally:
            session.close()

    def get_participant_challenges(
        self, participant_id: int, status: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """Get all challenges for participant.

        Args:
            participant_id: Participant ID.
            status: Optional status filter (active, completed, cancelled).

        Returns:
            List of challenge dictionaries.
        """
        challenges = self.db_manager.get_active_challenges(participant_id=participant_id)

        if status:
            challenges = [c for c in challenges if c.status == status]

        result = []
        for challenge in challenges:
            progress = self.get_challenge_progress(challenge.id)
            result.append(progress)

        return result
