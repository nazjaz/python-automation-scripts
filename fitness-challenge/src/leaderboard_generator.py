"""Generate leaderboards for fitness challenges."""

from typing import Dict, List, Optional

from src.database import DatabaseManager


class LeaderboardGenerator:
    """Generate leaderboards for challenges."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize leaderboard generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def generate_leaderboard(
        self, challenge_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """Generate leaderboard for challenge.

        Args:
            challenge_id: Optional challenge ID. If None, generates global leaderboard.
            limit: Maximum number of entries to return.

        Returns:
            List of leaderboard entry dictionaries.
        """
        if challenge_id:
            return self._generate_challenge_leaderboard(challenge_id, limit)
        else:
            return self._generate_global_leaderboard(limit)

    def _generate_challenge_leaderboard(
        self, challenge_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """Generate leaderboard for specific challenge.

        Args:
            challenge_id: Challenge ID.
            limit: Maximum number of entries.

        Returns:
            List of leaderboard entries.
        """
        from src.database import Challenge, Participant

        session = self.db_manager.get_session()
        try:
            challenge = session.query(Challenge).filter(Challenge.id == challenge_id).first()
            if not challenge:
                return []

            progress_entries = self.db_manager.get_progress_entries(challenge_id=challenge_id)

            participant_scores = {}
            for entry in progress_entries:
                participant_id = entry.participant_id
                if participant_id not in participant_scores:
                    participant_scores[participant_id] = 0.0
                participant_scores[participant_id] += entry.value

            sorted_participants = sorted(
                participant_scores.items(), key=lambda x: x[1], reverse=True
            )

            leaderboard = []
            for rank, (participant_id, score) in enumerate(sorted_participants, start=1):
                if limit and rank > limit:
                    break

                participant = session.query(Participant).filter(
                    Participant.id == participant_id
                ).first()

                self.db_manager.update_leaderboard(
                    challenge_id=challenge_id,
                    participant_id=participant_id,
                    rank=rank,
                    score=score,
                )

                leaderboard.append({
                    "rank": rank,
                    "participant_id": participant_id,
                    "participant_name": participant.name if participant else "Unknown",
                    "score": score,
                    "challenge_id": challenge_id,
                    "challenge_name": challenge.challenge_name,
                })

            return leaderboard
        finally:
            session.close()

    def _generate_global_leaderboard(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """Generate global leaderboard across all challenges.

        Args:
            limit: Maximum number of entries.

        Returns:
            List of leaderboard entries.
        """
        from src.database import Participant

        session = self.db_manager.get_session()
        try:
            participants = self.db_manager.get_all_participants()

            participant_scores = {}
            for participant in participants:
                progress_entries = self.db_manager.get_progress_entries(
                    participant_id=participant.id, days=30
                )
                total_score = sum(pe.value for pe in progress_entries)
                participant_scores[participant.id] = {
                    "name": participant.name,
                    "score": total_score,
                }

            sorted_participants = sorted(
                participant_scores.items(),
                key=lambda x: x[1]["score"],
                reverse=True,
            )

            leaderboard = []
            for rank, (participant_id, data) in enumerate(sorted_participants, start=1):
                if limit and rank > limit:
                    break

                self.db_manager.update_leaderboard(
                    challenge_id=None,
                    participant_id=participant_id,
                    rank=rank,
                    score=data["score"],
                )

                leaderboard.append({
                    "rank": rank,
                    "participant_id": participant_id,
                    "participant_name": data["name"],
                    "score": data["score"],
                })

            return leaderboard
        finally:
            session.close()

    def get_participant_rank(
        self, participant_id: int, challenge_id: Optional[int] = None
    ) -> Optional[Dict[str, any]]:
        """Get participant rank.

        Args:
            participant_id: Participant ID.
            challenge_id: Optional challenge ID.

        Returns:
            Dictionary with rank information or None.
        """
        leaderboard = self.db_manager.get_leaderboard(challenge_id=challenge_id)

        for entry in leaderboard:
            if entry.participant_id == participant_id:
                return {
                    "rank": entry.rank,
                    "score": entry.score,
                    "challenge_id": entry.challenge_id,
                }

        return None

    def update_leaderboard(self, challenge_id: Optional[int] = None) -> int:
        """Update leaderboard for challenge.

        Args:
            challenge_id: Optional challenge ID. If None, updates global leaderboard.

        Returns:
            Number of entries updated.
        """
        leaderboard = self.generate_leaderboard(challenge_id=challenge_id)
        return len(leaderboard)
