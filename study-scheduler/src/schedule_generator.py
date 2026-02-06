"""Generates personalized study schedules."""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, Course, Exam, StudySession, LearningPreference

logger = logging.getLogger(__name__)


class ScheduleGenerator:
    """Generates personalized study schedules based on exam dates and preferences."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize schedule generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.scheduling_config = config.get("scheduling", {})
        self.session_duration = self.scheduling_config.get("study_session_duration_minutes", 90)
        self.break_duration = self.scheduling_config.get("break_duration_minutes", 15)

    def generate_schedule(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        course_ids: Optional[List[int]] = None,
    ) -> List[StudySession]:
        """Generate study schedule for courses and exams.

        Args:
            start_date: Optional start date (defaults to today).
            end_date: Optional end date (defaults to last exam date).
            course_ids: Optional list of course IDs to include.

        Returns:
            List of generated StudySession objects.
        """
        if start_date is None:
            start_date = date.today()

        exams = self.db_manager.get_exams(upcoming_only=True)
        if not exams:
            logger.warning("No upcoming exams found for schedule generation")
            return []

        if end_date is None:
            last_exam_date = max(exam.exam_date for exam in exams)
            buffer_days = self.scheduling_config.get("days_before_exam_buffer", 2)
            end_date = last_exam_date - timedelta(days=buffer_days)

        if course_ids:
            exams = [e for e in exams if e.course_id in course_ids]

        preference = self.db_manager.get_learning_preference()
        if not preference:
            preference = self._get_default_preference()

        courses = self.db_manager.get_courses()
        if course_ids:
            courses = [c for c in courses if c.id in course_ids]

        schedule = []

        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            daily_sessions = self._generate_daily_sessions(
                current_date,
                courses,
                exams,
                preference,
            )

            schedule.extend(daily_sessions)
            current_date += timedelta(days=1)

        for session in schedule:
            self.db_manager.add_study_session(
                course_id=session["course_id"],
                session_date=session["session_date"],
                start_time=session.get("start_time"),
                end_time=session.get("end_time"),
                duration_minutes=session.get("duration_minutes"),
                topics_covered=session.get("topics_covered"),
                completion_status="scheduled",
            )

        logger.info(
            f"Generated study schedule: {len(schedule)} sessions",
            extra={"session_count": len(schedule), "start_date": str(start_date), "end_date": str(end_date)},
        )

        return schedule

    def _generate_daily_sessions(
        self,
        session_date: date,
        courses: List[Course],
        exams: List[Exam],
        preference: LearningPreference,
    ) -> List[Dict]:
        """Generate study sessions for a specific date.

        Args:
            session_date: Date for sessions.
            courses: List of courses.
            exams: List of exams.
            preference: Learning preferences.

        Returns:
            List of session dictionaries.
        """
        sessions = []

        daily_hours = preference.daily_study_hours
        preferred_times = self._parse_preferred_times(preference.preferred_study_times)

        exams_soon = [
            e for e in exams
            if (e.exam_date - session_date).days <= 14 and (e.exam_date - session_date).days >= 0
        ]

        courses_to_study = self._prioritize_courses(courses, exams_soon, session_date)

        hours_allocated = 0.0
        time_slot_index = 0

        for course in courses_to_study:
            if hours_allocated >= daily_hours:
                break

            exam = next((e for e in exams_soon if e.course_id == course.id), None)

            hours_needed = self._calculate_hours_needed(course, exam, session_date)

            if hours_needed <= 0:
                continue

            session_hours = min(hours_needed, daily_hours - hours_allocated)
            session_hours = min(session_hours, self.session_duration / 60.0)

            if time_slot_index < len(preferred_times):
                start_time = preferred_times[time_slot_index]
            else:
                start_time = "09:00"

            end_time = self._calculate_end_time(start_time, session_hours)

            topics = self._generate_topics(course, exam)

            sessions.append(
                {
                    "course_id": course.id,
                    "session_date": session_date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_minutes": int(session_hours * 60),
                    "topics_covered": topics,
                }
            )

            hours_allocated += session_hours
            time_slot_index += 1

        return sessions

    def _prioritize_courses(
        self,
        courses: List[Course],
        exams_soon: List[Exam],
        current_date: date,
    ) -> List[Course]:
        """Prioritize courses based on exam dates and priority.

        Args:
            courses: List of courses.
            exams_soon: List of upcoming exams.
            current_date: Current date.

        Returns:
            List of courses ordered by priority.
        """
        course_priorities = []

        for course in courses:
            exam = next((e for e in exams_soon if e.course_id == course.id), None)

            priority_score = 0.0

            if exam:
                days_until_exam = (exam.exam_date - current_date).days
                if days_until_exam <= 7:
                    priority_score += 100.0
                elif days_until_exam <= 14:
                    priority_score += 50.0
                elif days_until_exam <= 30:
                    priority_score += 25.0

                if exam.weight_percentage:
                    priority_score += exam.weight_percentage

            priority_map = {"critical": 50.0, "high": 30.0, "medium": 15.0, "low": 5.0}
            priority_score += priority_map.get(course.priority, 15.0)

            difficulty_map = {"hard": 20.0, "medium": 10.0, "easy": 5.0}
            priority_score += difficulty_map.get(course.difficulty, 10.0)

            completion_ratio = (
                course.hours_completed / course.total_hours_required
                if course.total_hours_required > 0
                else 0.0
            )
            priority_score += (1.0 - completion_ratio) * 30.0

            course_priorities.append((priority_score, course))

        course_priorities.sort(key=lambda x: x[0], reverse=True)

        return [course for _, course in course_priorities]

    def _calculate_hours_needed(
        self,
        course: Course,
        exam: Optional[Exam],
        current_date: date,
    ) -> float:
        """Calculate hours needed for course on given date.

        Args:
            course: Course object.
            exam: Optional exam object.
            current_date: Current date.

        Returns:
            Hours needed.
        """
        if exam:
            days_until_exam = (exam.exam_date - current_date).days
            if days_until_exam <= 0:
                return 0.0

            if exam.preparation_hours_required:
                remaining_hours = exam.preparation_hours_required
                hours_per_day = remaining_hours / max(days_until_exam, 1)
                return min(hours_per_day, 4.0)

        remaining_hours = course.total_hours_required - course.hours_completed
        if remaining_hours <= 0:
            return 0.0

        all_exams = self.db_manager.get_exams(course_id=course.id, upcoming_only=True)
        if all_exams:
            next_exam = min(all_exams, key=lambda e: e.exam_date)
            days_until_exam = (next_exam.exam_date - current_date).days
            if days_until_exam > 0:
                hours_per_day = remaining_hours / max(days_until_exam, 1)
                return min(hours_per_day, 4.0)

        return min(remaining_hours / 30.0, 2.0)

    def _generate_topics(
        self, course: Course, exam: Optional[Exam]
    ) -> str:
        """Generate topics to cover in session.

        Args:
            course: Course object.
            exam: Optional exam object.

        Returns:
            Comma-separated topics string.
        """
        if exam:
            return f"Exam preparation for {exam.name}"

        topics = [
            f"Review {course.name} materials",
            "Practice problems",
            "Concept review",
        ]

        return ", ".join(topics)

    def _parse_preferred_times(self, times_str: Optional[str]) -> List[str]:
        """Parse preferred study times string.

        Args:
            times_str: Comma-separated times string.

        Returns:
            List of time strings.
        """
        if not times_str:
            return self.scheduling_config.get("preferred_study_times", ["09:00", "14:00", "19:00"])

        return [t.strip() for t in times_str.split(",")]

    def _calculate_end_time(self, start_time: str, hours: float) -> str:
        """Calculate end time from start time and duration.

        Args:
            start_time: Start time string (HH:MM).
            hours: Duration in hours.

        Returns:
            End time string (HH:MM).
        """
        try:
            start_hour, start_minute = map(int, start_time.split(":"))
            start_datetime = datetime(2000, 1, 1, start_hour, start_minute)

            end_datetime = start_datetime + timedelta(hours=hours)

            return f"{end_datetime.hour:02d}:{end_datetime.minute:02d}"
        except Exception:
            return start_time

    def _get_default_preference(self) -> LearningPreference:
        """Get default learning preferences.

        Returns:
            LearningPreference object with defaults.
        """
        return self.db_manager.update_learning_preference(
            study_style="reading_writing",
            daily_study_hours=self.scheduling_config.get("default_study_hours_per_day", 4.0),
            break_frequency_minutes=self.session_duration,
            review_frequency_days=7,
        )
