"""Generate executive summaries with insights."""

import json
from typing import Dict, List, Optional

from src.database import DatabaseManager


class SummaryGenerator:
    """Generate executive summaries with insights."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize summary generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.summary_template = config.get("summary_template", {})

    def generate_summary(self, survey_id: int) -> Dict[str, any]:
        """Generate executive summary for survey.

        Args:
            survey_id: Survey ID.

        Returns:
            Dictionary with summary information.
        """
        survey = self.db_manager.get_survey(survey_id)
        if not survey:
            return {}

        responses = self.db_manager.get_survey_responses(survey_id)
        trends = self.db_manager.get_survey_trends(survey_id)
        insights = self.db_manager.get_survey_insights(survey_id)

        from src.satisfaction_calculator import SatisfactionCalculator

        calculator = SatisfactionCalculator(self.db_manager, self.config.get("satisfaction", {}))
        satisfaction_stats = calculator.get_satisfaction_statistics(survey_id)

        summary_text = self._generate_summary_text(
            survey, responses, trends, insights, satisfaction_stats
        )

        key_insights = self._extract_key_insights(insights)
        recommendations = self._generate_recommendations(trends, insights, satisfaction_stats)

        summary = self.db_manager.add_summary(
            survey_id=survey_id,
            summary_text=summary_text,
            satisfaction_score=satisfaction_stats.get("average", 0.0),
            response_count=len(responses),
            key_insights=json.dumps(key_insights),
            recommendations=json.dumps(recommendations),
        )

        return {
            "id": summary.id,
            "survey_id": survey_id,
            "summary_text": summary_text,
            "satisfaction_score": summary.satisfaction_score,
            "response_count": summary.response_count,
            "key_insights": key_insights,
            "recommendations": recommendations,
        }

    def _generate_summary_text(
        self,
        survey,
        responses: List,
        trends: List,
        insights: List,
        satisfaction_stats: Dict,
    ) -> str:
        """Generate summary text.

        Args:
            survey: Survey object.
            responses: List of response objects.
            trends: List of trend objects.
            insights: List of insight objects.
            satisfaction_stats: Satisfaction statistics.

        Returns:
            Summary text.
        """
        summary_parts = []

        summary_parts.append(f"Executive Summary: {survey.survey_name}")
        summary_parts.append("=" * 50)
        summary_parts.append("")

        summary_parts.append(f"Survey Overview:")
        summary_parts.append(f"  - Total Responses: {len(responses)}")
        summary_parts.append(
            f"  - Average Satisfaction Score: {satisfaction_stats.get('average', 0.0):.2f}/5.0"
        )
        summary_parts.append("")

        if trends:
            summary_parts.append("Key Trends Identified:")
            for trend in trends[:5]:
                summary_parts.append(f"  - {trend.trend_name}: {trend.description}")
            summary_parts.append("")

        if insights:
            summary_parts.append("Key Insights:")
            for insight in insights[:5]:
                summary_parts.append(f"  - {insight.title}: {insight.description}")
            summary_parts.append("")

        distribution = satisfaction_stats.get("distribution", {})
        if distribution:
            summary_parts.append("Satisfaction Distribution:")
            summary_parts.append(
                f"  - Very Satisfied: {distribution.get('very_satisfied', 0)}"
            )
            summary_parts.append(f"  - Satisfied: {distribution.get('satisfied', 0)}")
            summary_parts.append(f"  - Neutral: {distribution.get('neutral', 0)}")
            summary_parts.append(
                f"  - Dissatisfied: {distribution.get('dissatisfied', 0)}"
            )
            summary_parts.append(
                f"  - Very Dissatisfied: {distribution.get('very_dissatisfied', 0)}"
            )

        return "\n".join(summary_parts)

    def _extract_key_insights(self, insights: List) -> List[Dict[str, str]]:
        """Extract key insights.

        Args:
            insights: List of insight objects.

        Returns:
            List of insight dictionaries.
        """
        key_insights = []
        for insight in insights[:10]:
            key_insights.append({
                "type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "priority": insight.priority,
            })
        return key_insights

    def _generate_recommendations(
        self, trends: List, insights: List, satisfaction_stats: Dict
    ) -> List[str]:
        """Generate recommendations.

        Args:
            trends: List of trend objects.
            insights: List of insight objects.
            satisfaction_stats: Satisfaction statistics.

        Returns:
            List of recommendation strings.
        """
        recommendations = []

        avg_satisfaction = satisfaction_stats.get("average", 0.0)

        if avg_satisfaction < 3.0:
            recommendations.append(
                "URGENT: Overall satisfaction is below acceptable levels. "
                "Immediate action required to address customer concerns."
            )

        negative_trends = [t for t in trends if t.trend_type == "negative"]
        if negative_trends:
            recommendations.append(
                f"Address {len(negative_trends)} negative trend(s) identified in survey responses."
            )

        high_priority_insights = [i for i in insights if i.priority == "high"]
        if high_priority_insights:
            recommendations.append(
                f"Review {len(high_priority_insights)} high-priority insight(s) for immediate action."
            )

        distribution = satisfaction_stats.get("distribution", {})
        dissatisfied_count = (
            distribution.get("dissatisfied", 0)
            + distribution.get("very_dissatisfied", 0)
        )
        if dissatisfied_count > 0:
            recommendations.append(
                f"Follow up with {dissatisfied_count} dissatisfied customer(s) to understand concerns."
            )

        if not recommendations:
            recommendations.append(
                "Continue monitoring satisfaction trends and maintain current service levels."
            )

        return recommendations

    def generate_insights(
        self, survey_id: int, analysis_results: Dict
    ) -> List[Dict[str, any]]:
        """Generate insights from analysis results.

        Args:
            survey_id: Survey ID.
            analysis_results: Analysis results dictionary.

        Returns:
            List of insight dictionaries.
        """
        insights = []
        question_analyses = analysis_results.get("question_analyses", [])

        for analysis in question_analyses:
            if analysis.get("question_type") == "rating":
                avg_rating = analysis.get("average", 0.0)
                if avg_rating >= 4.5:
                    insight = self.db_manager.add_insight(
                        survey_id=survey_id,
                        insight_type="positive",
                        title=f"High Ratings: {analysis.get('question_text', '')[:50]}",
                        description=(
                            f"Question received high average rating of {avg_rating:.2f}/5.0. "
                            f"This indicates strong positive feedback."
                        ),
                        priority="low",
                    )
                    insights.append({
                        "id": insight.id,
                        "type": insight.insight_type,
                        "title": insight.title,
                        "description": insight.description,
                    })
                elif avg_rating <= 2.0:
                    insight = self.db_manager.add_insight(
                        survey_id=survey_id,
                        insight_type="negative",
                        title=f"Low Ratings: {analysis.get('question_text', '')[:50]}",
                        description=(
                            f"Question received low average rating of {avg_rating:.2f}/5.0. "
                            f"This requires immediate attention."
                        ),
                        priority="high",
                    )
                    insights.append({
                        "id": insight.id,
                        "type": insight.insight_type,
                        "title": insight.title,
                        "description": insight.description,
                    })

        return insights
