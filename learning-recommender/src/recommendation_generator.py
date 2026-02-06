"""Generate personalized learning recommendations."""

from typing import Dict, List, Optional

from src.database import DatabaseManager


class RecommendationGenerator:
    """Generate personalized learning recommendations."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize recommendation generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.min_confidence = config.get("min_confidence", 0.5)

    def generate_recommendations(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, any]]:
        """Generate personalized learning recommendations.

        Args:
            user_id: User ID.
            limit: Maximum number of recommendations to generate.

        Returns:
            List of recommendation dictionaries.
        """
        from src.behavior_analyzer import BehaviorAnalyzer
        from src.completion_analyzer import CompletionAnalyzer
        from src.difficulty_adapter import DifficultyAdapter
        from src.objective_tracker import ObjectiveTracker

        behavior_analyzer = BehaviorAnalyzer(
            self.db_manager, self.config.get("behavior_analysis", {})
        )
        completion_analyzer = CompletionAnalyzer(
            self.db_manager, self.config.get("completion_analysis", {})
        )
        difficulty_adapter = DifficultyAdapter(
            self.db_manager, self.config.get("difficulty_adaptation", {})
        )
        objective_tracker = ObjectiveTracker(
            self.db_manager, self.config.get("objective_tracking", {})
        )

        behavior_analysis = behavior_analyzer.analyze_user_behavior(user_id)
        learning_style = behavior_analyzer.get_learning_style(user_id)
        completion_stats = completion_analyzer.get_user_completion_statistics(user_id)
        objectives_summary = objective_tracker.get_user_objectives_summary(user_id)

        recommendations = []

        session = self.db_manager.get_session()
        try:
            from src.database import Course

            all_courses = session.query(Course).all()

            for course in all_courses:
                recommendation = self._generate_course_recommendation(
                    user_id=user_id,
                    course=course,
                    behavior_analysis=behavior_analysis,
                    learning_style=learning_style,
                    completion_stats=completion_stats,
                    objectives_summary=objectives_summary,
                    difficulty_adapter=difficulty_adapter,
                )

                if recommendation and recommendation["confidence_score"] >= self.min_confidence:
                    rec = self.db_manager.add_recommendation(
                        user_id=user_id,
                        course_id=course.id,
                        recommendation_type=recommendation["type"],
                        title=recommendation["title"],
                        description=recommendation["description"],
                        confidence_score=recommendation["confidence_score"],
                        difficulty_level=recommendation.get("difficulty_level"),
                        priority=recommendation.get("priority", "medium"),
                    )
                    recommendations.append({
                        "id": rec.id,
                        "course_id": course.course_id,
                        "course_name": course.course_name,
                        "title": rec.title,
                        "description": rec.description,
                        "confidence_score": rec.confidence_score,
                        "difficulty_level": rec.difficulty_level,
                        "priority": rec.priority,
                    })
        finally:
            session.close()

        recommendations.sort(key=lambda x: x["confidence_score"], reverse=True)

        return recommendations[:limit]

    def _generate_course_recommendation(
        self,
        user_id: int,
        course,
        behavior_analysis: Dict,
        learning_style: Dict,
        completion_stats: Dict,
        objectives_summary: Dict,
        difficulty_adapter,
    ) -> Optional[Dict[str, any]]:
        """Generate recommendation for a specific course.

        Args:
            user_id: User ID.
            course: Course object.
            behavior_analysis: Behavior analysis results.
            learning_style: Learning style information.
            completion_stats: Completion statistics.
            objectives_summary: Objectives summary.
            difficulty_adapter: Difficulty adapter instance.

        Returns:
            Recommendation dictionary or None.
        """
        confidence_score = 0.0
        recommendation_type = "general"
        priority = "medium"

        category_preferences = behavior_analysis.get("category_preferences", {})
        if course.category in category_preferences:
            confidence_score += category_preferences[course.category] * 0.3

        difficulty_rec = difficulty_adapter.adapt_difficulty(user_id, course.id)
        recommended_difficulty = difficulty_rec.get("recommended_difficulty", "beginner")

        if course.difficulty_level == recommended_difficulty:
            confidence_score += 0.3
            recommendation_type = "difficulty_match"
        elif course.difficulty_level:
            diff_match = abs(
                ["beginner", "intermediate", "advanced"].index(course.difficulty_level)
                - ["beginner", "intermediate", "advanced"].index(recommended_difficulty)
            )
            if diff_match <= 1:
                confidence_score += 0.2

        objectives = objectives_summary.get("objectives", [])
        for objective in objectives:
            if objective.get("target_skill"):
                if objective["target_skill"].lower() in (course.category or "").lower():
                    confidence_score += 0.2
                    recommendation_type = "objective_aligned"
                    priority = objective.get("priority", "medium")
                    break

        if completion_stats.get("average_completion_rate", 0.0) > 0.7:
            confidence_score += 0.1

        if confidence_score < self.min_confidence:
            return None

        title = f"Recommended: {course.course_name}"
        description = self._generate_description(
            course, learning_style, difficulty_rec, recommendation_type
        )

        return {
            "type": recommendation_type,
            "title": title,
            "description": description,
            "confidence_score": min(confidence_score, 1.0),
            "difficulty_level": recommended_difficulty,
            "priority": priority,
        }

    def _generate_description(
        self,
        course,
        learning_style: Dict,
        difficulty_rec: Dict,
        recommendation_type: str,
    ) -> str:
        """Generate recommendation description.

        Args:
            course: Course object.
            learning_style: Learning style information.
            difficulty_rec: Difficulty recommendation.
            recommendation_type: Recommendation type.

        Returns:
            Description string.
        """
        style = learning_style.get("learning_style", "balanced")
        difficulty = difficulty_rec.get("recommended_difficulty", "beginner")

        description_parts = [
            f"This {course.category or 'course'} is recommended based on your learning profile.",
        ]

        if recommendation_type == "objective_aligned":
            description_parts.append("It aligns with your learning objectives.")
        elif recommendation_type == "difficulty_match":
            description_parts.append(f"The {difficulty} difficulty level matches your current skill level.")

        description_parts.append(f"Your learning style ({style}) suggests this course format will be effective.")

        return " ".join(description_parts)

    def get_recommendations_for_objective(
        self, user_id: int, objective_id: int
    ) -> List[Dict[str, any]]:
        """Get recommendations for a specific learning objective.

        Args:
            user_id: User ID.
            objective_id: Learning objective ID.

        Returns:
            List of recommendation dictionaries.
        """
        from src.objective_tracker import ObjectiveTracker

        tracker = ObjectiveTracker(
            self.db_manager, self.config.get("objective_tracking", {})
        )
        recommended_courses = tracker.get_recommended_courses_for_objective(objective_id)

        recommendations = []
        for course_data in recommended_courses:
            course = self.db_manager.get_course(course_data["course_id"])
            if course:
                rec = self.db_manager.add_recommendation(
                    user_id=user_id,
                    course_id=course.id,
                    recommendation_type="objective_based",
                    title=f"Recommended for Objective: {course.course_name}",
                    description=f"This course aligns with your learning objective: {course_data.get('category', 'skill')}",
                    confidence_score=0.8,
                    difficulty_level=course.difficulty_level,
                    priority="high",
                )
                recommendations.append({
                    "id": rec.id,
                    "course_name": course.course_name,
                    "confidence_score": rec.confidence_score,
                })

        return recommendations
