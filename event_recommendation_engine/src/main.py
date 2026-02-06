"""Event Recommendation Engine.

Automatically generates personalized event recommendations by analyzing user
interests, location, and past attendance, with calendar integration and
reminder notifications.
"""

import json
import logging
import smtplib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
import yaml
from icalendar import Calendar, Event
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class UserProfile(BaseModel):
    """User profile with interests and preferences."""

    user_id: str = Field(..., description="Unique user identifier")
    interests: List[str] = Field(
        default_factory=list, description="List of user interest categories"
    )
    location: Dict[str, float] = Field(
        ..., description="User location as latitude and longitude"
    )
    max_travel_distance_km: float = Field(
        default=50.0, description="Maximum travel distance in kilometers"
    )
    preferred_event_types: List[str] = Field(
        default_factory=list, description="Preferred event types"
    )
    email: Optional[str] = Field(
        default=None, description="Email address for notifications"
    )

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate location has latitude and longitude."""
        if "latitude" not in v or "longitude" not in v:
            raise ValueError("Location must contain latitude and longitude")
        if not -90 <= v["latitude"] <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if not -180 <= v["longitude"] <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class EventData(BaseModel):
    """Event information model."""

    event_id: str = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(
        default=None, description="Event description"
    )
    category: str = Field(..., description="Event category")
    event_type: str = Field(..., description="Type of event")
    start_time: datetime = Field(..., description="Event start time")
    end_time: Optional[datetime] = Field(
        default=None, description="Event end time"
    )
    location: Dict[str, float] = Field(
        ..., description="Event location as latitude and longitude"
    )
    venue_name: Optional[str] = Field(
        default=None, description="Venue name"
    )
    price: Optional[float] = Field(
        default=None, description="Event price"
    )


class RecommendationConfig(BaseModel):
    """Configuration for recommendation algorithm."""

    interest_weight: float = Field(
        default=0.4, description="Weight for interest matching"
    )
    location_weight: float = Field(
        default=0.3, description="Weight for location proximity"
    )
    past_attendance_weight: float = Field(
        default=0.3, description="Weight for past attendance patterns"
    )
    max_recommendations: int = Field(
        default=10, description="Maximum number of recommendations"
    )
    min_score_threshold: float = Field(
        default=0.3, description="Minimum recommendation score"
    )


class CalendarConfig(BaseModel):
    """Calendar integration configuration."""

    calendar_file: str = Field(
        default="logs/user_calendar.ics",
        description="Path to user calendar file",
    )
    auto_add_recommendations: bool = Field(
        default=False,
        description="Automatically add recommendations to calendar",
    )


class NotificationConfig(BaseModel):
    """Notification configuration."""

    enabled: bool = Field(
        default=True, description="Enable email notifications"
    )
    reminder_hours_before: List[int] = Field(
        default_factory=lambda: [24, 2],
        description="Hours before event to send reminders",
    )
    smtp_server: Optional[str] = Field(
        default=None, description="SMTP server address"
    )
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: Optional[str] = Field(
        default=None, description="SMTP username"
    )
    smtp_password: Optional[str] = Field(
        default=None, description="SMTP password"
    )


class Config(BaseModel):
    """Main configuration model."""

    users: List[UserProfile] = Field(
        ..., description="List of user profiles"
    )
    events_file: str = Field(
        ..., description="Path to events data file (CSV or JSON)"
    )
    past_attendance_file: Optional[str] = Field(
        default=None, description="Path to past attendance data file"
    )
    recommendation: RecommendationConfig = Field(
        default_factory=RecommendationConfig,
        description="Recommendation algorithm settings",
    )
    calendar: CalendarConfig = Field(
        default_factory=CalendarConfig,
        description="Calendar integration settings",
    )
    notification: NotificationConfig = Field(
        default_factory=NotificationConfig,
        description="Notification settings",
    )
    output_file: str = Field(
        default="logs/recommendations.json",
        description="Path to save recommendations",
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"
    smtp_username: Optional[str] = Field(
        default=None, description="SMTP username from environment"
    )
    smtp_password: Optional[str] = Field(
        default=None, description="SMTP password from environment"
    )


@dataclass
class Recommendation:
    """Event recommendation with score."""

    event: EventData
    score: float
    reasons: List[str]


@dataclass
class UserRecommendations:
    """Recommendations for a specific user."""

    user_id: str
    recommendations: List[Recommendation]
    generated_at: datetime


def load_config(config_path: Path) -> Config:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to configuration YAML file

    Returns:
        Validated configuration object

    Raises:
        FileNotFoundError: If config file does not exist
        ValueError: If configuration is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        config = Config(**config_data)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in configuration file: {e}")
        raise ValueError(f"Invalid YAML configuration: {e}") from e
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def load_events(events_file: Path) -> List[EventData]:
    """Load events from CSV or JSON file.

    Args:
        events_file: Path to events data file

    Returns:
        List of EventData objects

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file format is invalid
    """
    if not events_file.exists():
        raise FileNotFoundError(f"Events file not found: {events_file}")

    events = []

    if events_file.suffix.lower() == ".csv":
        try:
            df = pd.read_csv(events_file)
            required_columns = [
                "event_id",
                "title",
                "category",
                "event_type",
                "start_time",
                "latitude",
                "longitude",
            ]
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                raise ValueError(
                    f"Missing required columns: {missing}"
                )

            for _, row in df.iterrows():
                try:
                    start_time = pd.to_datetime(row["start_time"])
                    end_time = (
                        pd.to_datetime(row["end_time"])
                        if "end_time" in df.columns
                        and pd.notna(row["end_time"])
                        else None
                    )

                    event = EventData(
                        event_id=str(row["event_id"]),
                        title=str(row["title"]),
                        description=(
                            str(row["description"])
                            if "description" in df.columns
                            and pd.notna(row["description"])
                            else None
                        ),
                        category=str(row["category"]),
                        event_type=str(row["event_type"]),
                        start_time=start_time,
                        end_time=end_time,
                        location={
                            "latitude": float(row["latitude"]),
                            "longitude": float(row["longitude"]),
                        },
                        venue_name=(
                            str(row["venue_name"])
                            if "venue_name" in df.columns
                            and pd.notna(row["venue_name"])
                            else None
                        ),
                        price=(
                            float(row["price"])
                            if "price" in df.columns and pd.notna(row["price"])
                            else None
                        ),
                    )
                    events.append(event)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse event row: {e}. Skipping."
                    )
                    continue

        except pd.errors.EmptyDataError:
            logger.warning(f"CSV file is empty: {events_file}")
            return []
        except Exception as e:
            logger.error(f"Failed to load CSV file: {e}")
            raise

    elif events_file.suffix.lower() == ".json":
        try:
            with open(events_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("JSON file must contain an array of events")

            for item in data:
                try:
                    item["start_time"] = datetime.fromisoformat(
                        item["start_time"]
                    )
                    if "end_time" in item and item["end_time"]:
                        item["end_time"] = datetime.fromisoformat(
                            item["end_time"]
                        )
                    events.append(EventData(**item))
                except Exception as e:
                    logger.warning(
                        f"Failed to parse event: {e}. Skipping."
                    )
                    continue

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {events_file}: {e}")
            raise ValueError(f"Invalid JSON structure: {e}") from e
        except Exception as e:
            logger.error(f"Failed to load JSON file: {e}")
            raise
    else:
        raise ValueError(
            f"Unsupported file format: {events_file.suffix}. Use CSV or JSON."
        )

    logger.info(f"Loaded {len(events)} events from {events_file}")
    return events


def load_past_attendance(
    attendance_file: Optional[Path],
) -> Dict[str, List[str]]:
    """Load past attendance data.

    Args:
        attendance_file: Path to attendance data file (optional)

    Returns:
        Dictionary mapping user_id to list of attended event categories/types
    """
    if not attendance_file or not attendance_file.exists():
        return {}

    try:
        if attendance_file.suffix.lower() == ".csv":
            df = pd.read_csv(attendance_file)
            if "user_id" not in df.columns:
                logger.warning(
                    "user_id column not found in attendance file"
                )
                return {}

            attendance = {}
            for user_id in df["user_id"].unique():
                user_df = df[df["user_id"] == user_id]
                categories = (
                    user_df["category"].tolist()
                    if "category" in user_df.columns
                    else []
                )
                event_types = (
                    user_df["event_type"].tolist()
                    if "event_type" in user_df.columns
                    else []
                )
                attendance[str(user_id)] = categories + event_types

            logger.info(
                f"Loaded past attendance for {len(attendance)} users"
            )
            return attendance

        elif attendance_file.suffix.lower() == ".json":
            with open(attendance_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {str(k): v for k, v in data.items()}
            return {}

    except Exception as e:
        logger.warning(f"Failed to load attendance data: {e}")
        return {}

    return {}


def calculate_distance_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calculate distance between two coordinates in kilometers.

    Uses Haversine formula for great-circle distance.

    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point

    Returns:
        Distance in kilometers
    """
    from math import asin, cos, radians, sin, sqrt

    R = 6371.0

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad)
        * cos(lat2_rad)
        * sin(delta_lon / 2) ** 2
    )
    c = 2 * asin(sqrt(a))

    return R * c


def calculate_interest_score(
    event: EventData, user_interests: List[str]
) -> float:
    """Calculate interest matching score.

    Args:
        event: Event to score
        user_interests: List of user interests

    Returns:
        Score between 0.0 and 1.0
    """
    if not user_interests:
        return 0.5

    event_text = (
        f"{event.title} {event.description or ''} "
        f"{event.category} {event.event_type}"
    ).lower()

    matches = sum(
        1
        for interest in user_interests
        if interest.lower() in event_text
    )

    return min(1.0, matches / len(user_interests))


def calculate_location_score(
    event: EventData,
    user_location: Dict[str, float],
    max_distance_km: float,
) -> float:
    """Calculate location proximity score.

    Args:
        event: Event to score
        user_location: User location coordinates
        max_distance_km: Maximum acceptable distance

    Returns:
        Score between 0.0 and 1.0 (1.0 = very close, 0.0 = too far)
    """
    distance = calculate_distance_km(
        user_location["latitude"],
        user_location["longitude"],
        event.location["latitude"],
        event.location["longitude"],
    )

    if distance > max_distance_km:
        return 0.0

    return 1.0 - (distance / max_distance_km)


def calculate_past_attendance_score(
    event: EventData, past_attendance: List[str]
) -> float:
    """Calculate score based on past attendance patterns.

    Args:
        event: Event to score
        past_attendance: List of past attended categories/types

    Returns:
        Score between 0.0 and 1.0
    """
    if not past_attendance:
        return 0.5

    event_categories = [event.category.lower(), event.event_type.lower()]
    matches = sum(
        1
        for cat in event_categories
        if any(cat in past.lower() for past in past_attendance)
    )

    return min(1.0, matches / len(event_categories))


def generate_recommendations(
    user: UserProfile,
    events: List[EventData],
    past_attendance: List[str],
    config: RecommendationConfig,
) -> List[Recommendation]:
    """Generate personalized event recommendations for a user.

    Args:
        user: User profile
        events: List of available events
        past_attendance: User's past attendance history
        config: Recommendation configuration

    Returns:
        List of recommendations sorted by score
    """
    recommendations = []
    now = datetime.now()

    for event in events:
        if event.start_time < now:
            continue

        interest_score = calculate_interest_score(event, user.interests)
        location_score = calculate_location_score(
            event, user.location, user.max_travel_distance_km
        )
        attendance_score = calculate_past_attendance_score(
            event, past_attendance
        )

        total_score = (
            interest_score * config.interest_weight
            + location_score * config.location_weight
            + attendance_score * config.past_attendance_weight
        )

        if total_score < config.min_score_threshold:
            continue

        reasons = []
        if interest_score > 0.5:
            reasons.append("Matches your interests")
        if location_score > 0.7:
            reasons.append("Close to your location")
        if attendance_score > 0.5:
            reasons.append("Similar to events you've attended")

        recommendations.append(
            Recommendation(
                event=event, score=total_score, reasons=reasons
            )
        )

    recommendations.sort(key=lambda x: x.score, reverse=True)
    return recommendations[: config.max_recommendations]


def add_to_calendar(
    recommendation: Recommendation, calendar_file: Path
) -> None:
    """Add recommended event to calendar.

    Args:
        recommendation: Event recommendation to add
        calendar_file: Path to calendar ICS file
    """
    calendar_file.parent.mkdir(parents=True, exist_ok=True)

    cal = Calendar()
    if calendar_file.exists():
        try:
            with open(calendar_file, "rb") as f:
                cal = Calendar.from_ical(f.read())
        except Exception as e:
            logger.warning(f"Failed to load existing calendar: {e}")

    event = Event()
    event.add("summary", recommendation.event.title)
    if recommendation.event.description:
        event.add("description", recommendation.event.description)
    event.add("dtstart", recommendation.event.start_time)
    if recommendation.event.end_time:
        event.add("dtend", recommendation.event.end_time)
    else:
        event.add(
            "dtend",
            recommendation.event.start_time + timedelta(hours=2),
        )
    event.add("dtstamp", datetime.now())
    event.add("uid", f"{recommendation.event.event_id}@eventrec")

    if recommendation.event.venue_name:
        event.add("location", recommendation.event.venue_name)

    cal.add_component(event)

    try:
        with open(calendar_file, "wb") as f:
            f.write(cal.to_ical())
        logger.info(
            f"Added event '{recommendation.event.title}' to calendar"
        )
    except Exception as e:
        logger.error(f"Failed to save calendar: {e}")


def send_notification(
    recommendation: Recommendation,
    user_email: str,
    config: NotificationConfig,
) -> None:
    """Send email notification for recommended event.

    Args:
        recommendation: Event recommendation
        user_email: Recipient email address
        config: Notification configuration
    """
    if not config.enabled or not config.smtp_server:
        return

    subject = f"Event Recommendation: {recommendation.event.title}"
    body = f"""
Event Recommendation

Title: {recommendation.event.title}
Category: {recommendation.event.category}
Type: {recommendation.event.event_type}
Start Time: {recommendation.event.start_time.strftime('%Y-%m-%d %H:%M')}

Recommendation Score: {recommendation.score:.2f}

Reasons:
{chr(10).join(f'- {reason}' for reason in recommendation.reasons)}

"""

    if recommendation.event.description:
        body += f"\nDescription:\n{recommendation.event.description}\n"

    if recommendation.event.venue_name:
        body += f"\nVenue: {recommendation.event.venue_name}\n"

    if recommendation.event.price:
        body += f"\nPrice: ${recommendation.event.price:.2f}\n"

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = config.smtp_username
        msg["To"] = user_email

        with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
            server.starttls()
            if config.smtp_username and config.smtp_password:
                server.login(config.smtp_username, config.smtp_password)
            server.send_message(msg)

        logger.info(f"Notification sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


def process_recommendations(config_path: Path) -> Dict[str, UserRecommendations]:
    """Process recommendations for all users.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary mapping user_id to recommendations

    Raises:
        FileNotFoundError: If config or data files are missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    project_root = config_path.parent

    events_file = Path(config.events_file)
    if not events_file.is_absolute():
        events_file = project_root / events_file

    events = load_events(events_file)

    attendance_file = None
    if config.past_attendance_file:
        attendance_file = Path(config.past_attendance_file)
        if not attendance_file.is_absolute():
            attendance_file = project_root / attendance_file

    past_attendance_all = load_past_attendance(attendance_file)

    all_recommendations = {}

    for user in config.users:
        logger.info(f"Generating recommendations for user: {user.user_id}")
        past_attendance = past_attendance_all.get(user.user_id, [])

        recommendations = generate_recommendations(
            user, events, past_attendance, config.recommendation
        )

        user_recs = UserRecommendations(
            user_id=user.user_id,
            recommendations=recommendations,
            generated_at=datetime.now(),
        )

        all_recommendations[user.user_id] = user_recs

        logger.info(
            f"Generated {len(recommendations)} recommendations for {user.user_id}"
        )

        if config.calendar.auto_add_recommendations:
            calendar_file = Path(config.calendar.calendar_file)
            if not calendar_file.is_absolute():
                calendar_file = project_root / calendar_file

            for rec in recommendations:
                add_to_calendar(rec, calendar_file)

        if config.notification.enabled and user.email:
            for rec in recommendations[:3]:
                send_notification(rec, user.email, config.notification)

    output_file = Path(config.output_file)
    if not output_file.is_absolute():
        output_file = project_root / output_file

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_data = {
        user_id: {
            "user_id": recs.user_id,
            "generated_at": recs.generated_at.isoformat(),
            "recommendations": [
                {
                    "event_id": rec.event.event_id,
                    "title": rec.event.title,
                    "score": rec.score,
                    "reasons": rec.reasons,
                    "start_time": rec.event.start_time.isoformat(),
                }
                for rec in recs.recommendations
            ],
        }
        for user_id, recs in all_recommendations.items()
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Recommendations saved to {output_file}")

    return all_recommendations


def main() -> None:
    """Main entry point for the event recommendation engine."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting event recommendation engine")
        recommendations = process_recommendations(config_path)
        total_recs = sum(
            len(recs.recommendations) for recs in recommendations.values()
        )
        logger.info(
            f"Processing complete. Generated {total_recs} total recommendations "
            f"for {len(recommendations)} users."
        )
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
