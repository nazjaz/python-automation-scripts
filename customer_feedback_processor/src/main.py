"""Customer Feedback Processor.

Automatically processes customer feedback from multiple channels, aggregates
insights, identifies common themes, and generates product roadmap recommendations.
"""

import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class FeedbackSourceConfig(BaseModel):
    """Configuration for a feedback data source."""

    name: str = Field(..., description="Source name identifier")
    path: str = Field(..., description="Path to feedback data file")
    format: str = Field(..., description="File format: csv, json, or txt")
    text_column: Optional[str] = Field(
        None, description="Column name containing feedback text (CSV/JSON)"
    )
    metadata_columns: List[str] = Field(
        default_factory=list,
        description="Additional columns to preserve as metadata",
    )

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate file format is supported."""
        if v.lower() not in ["csv", "json", "txt"]:
            raise ValueError("Format must be csv, json, or txt")
        return v.lower()


class ThemeConfig(BaseModel):
    """Configuration for theme identification."""

    min_occurrences: int = Field(
        default=3, description="Minimum occurrences for a theme to be significant"
    )
    min_keyword_length: int = Field(
        default=3, description="Minimum keyword length for extraction"
    )
    stop_words: List[str] = Field(
        default_factory=lambda: [
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "they",
            "them",
            "we",
            "us",
            "you",
            "your",
            "my",
            "our",
        ],
        description="Stop words to exclude from theme analysis",
    )


class RoadmapConfig(BaseModel):
    """Configuration for roadmap generation."""

    high_priority_threshold: float = Field(
        default=0.15,
        description="Minimum frequency for high priority recommendations",
    )
    medium_priority_threshold: float = Field(
        default=0.05,
        description="Minimum frequency for medium priority recommendations",
    )
    max_recommendations: int = Field(
        default=20, description="Maximum number of recommendations to generate"
    )


class Config(BaseModel):
    """Main configuration model."""

    sources: List[FeedbackSourceConfig] = Field(
        ..., description="List of feedback data sources"
    )
    theme: ThemeConfig = Field(
        default_factory=ThemeConfig, description="Theme identification settings"
    )
    roadmap: RoadmapConfig = Field(
        default_factory=RoadmapConfig, description="Roadmap generation settings"
    )
    output_path: str = Field(
        default="logs/feedback_analysis.md",
        description="Path for output report",
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"


@dataclass
class FeedbackItem:
    """Represents a single feedback item."""

    text: str
    source: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Theme:
    """Represents an identified theme."""

    keywords: List[str]
    frequency: int
    percentage: float
    sample_feedback: List[str]


@dataclass
class RoadmapRecommendation:
    """Represents a product roadmap recommendation."""

    theme: str
    priority: str
    frequency: int
    percentage: float
    rationale: str
    sample_feedback: List[str]


@dataclass
class FeedbackAnalysis:
    """Complete feedback analysis results."""

    total_feedback_count: int
    sources_summary: Dict[str, int]
    themes: List[Theme]
    recommendations: List[RoadmapRecommendation]


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


def load_csv_feedback(
    file_path: Path, text_column: str, metadata_columns: List[str], source_name: str
) -> List[FeedbackItem]:
    """Load feedback from CSV file.

    Args:
        file_path: Path to CSV file
        text_column: Name of column containing feedback text
        metadata_columns: Additional columns to preserve as metadata
        source_name: Identifier for the data source

    Returns:
        List of FeedbackItem objects

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If required columns are missing
    """
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    try:
        df = pd.read_csv(file_path)
        if text_column not in df.columns:
            raise ValueError(
                f"Required column '{text_column}' not found in CSV file"
            )

        feedback_items = []
        for _, row in df.iterrows():
            text = str(row[text_column]).strip()
            if not text or text.lower() == "nan":
                continue

            metadata = {}
            for col in metadata_columns:
                if col in df.columns:
                    metadata[col] = str(row[col])

            feedback_items.append(
                FeedbackItem(text=text, source=source_name, metadata=metadata)
            )

        logger.info(f"Loaded {len(feedback_items)} feedback items from CSV: {file_path}")
        return feedback_items
    except pd.errors.EmptyDataError:
        logger.warning(f"CSV file is empty: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load CSV file {file_path}: {e}")
        raise


def load_json_feedback(
    file_path: Path, text_column: str, metadata_columns: List[str], source_name: str
) -> List[FeedbackItem]:
    """Load feedback from JSON file.

    Args:
        file_path: Path to JSON file
        text_column: Key name containing feedback text
        metadata_columns: Additional keys to preserve as metadata
        source_name: Identifier for the data source

    Returns:
        List of FeedbackItem objects

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If JSON structure is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("JSON file must contain an array of objects")

        feedback_items = []
        for item in data:
            if not isinstance(item, dict):
                continue

            if text_column not in item:
                continue

            text = str(item[text_column]).strip()
            if not text or text.lower() == "null":
                continue

            metadata = {}
            for col in metadata_columns:
                if col in item:
                    metadata[col] = str(item[col])

            feedback_items.append(
                FeedbackItem(text=text, source=source_name, metadata=metadata)
            )

        logger.info(f"Loaded {len(feedback_items)} feedback items from JSON: {file_path}")
        return feedback_items
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {e}")
        raise ValueError(f"Invalid JSON structure: {e}") from e
    except Exception as e:
        logger.error(f"Failed to load JSON file {file_path}: {e}")
        raise


def load_txt_feedback(file_path: Path, source_name: str) -> List[FeedbackItem]:
    """Load feedback from plain text file.

    Args:
        file_path: Path to text file
        source_name: Identifier for the data source

    Returns:
        List of FeedbackItem objects

    Raises:
        FileNotFoundError: If file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        feedback_items = []
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                feedback_items.append(
                    FeedbackItem(text=line, source=source_name)
                )

        logger.info(f"Loaded {len(feedback_items)} feedback items from text file: {file_path}")
        return feedback_items
    except Exception as e:
        logger.error(f"Failed to load text file {file_path}: {e}")
        raise


def load_all_feedback(config: Config) -> List[FeedbackItem]:
    """Load feedback from all configured sources.

    Args:
        config: Configuration object with source definitions

    Returns:
        Combined list of all feedback items

    Raises:
        FileNotFoundError: If any source file is missing
        ValueError: If source configuration is invalid
    """
    all_feedback = []

    for source_config in config.sources:
        source_path = Path(source_config.path)
        logger.info(f"Loading feedback from source: {source_config.name}")

        if source_config.format == "csv":
            if not source_config.text_column:
                raise ValueError(
                    f"text_column required for CSV source: {source_config.name}"
                )
            items = load_csv_feedback(
                source_path,
                source_config.text_column,
                source_config.metadata_columns,
                source_config.name,
            )
        elif source_config.format == "json":
            if not source_config.text_column:
                raise ValueError(
                    f"text_column required for JSON source: {source_config.name}"
                )
            items = load_json_feedback(
                source_path,
                source_config.text_column,
                source_config.metadata_columns,
                source_config.name,
            )
        elif source_config.format == "txt":
            items = load_txt_feedback(source_path, source_config.name)
        else:
            raise ValueError(
                f"Unsupported format: {source_config.format} for source: {source_config.name}"
            )

        all_feedback.extend(items)

    logger.info(f"Total feedback items loaded: {len(all_feedback)}")
    return all_feedback


def extract_keywords(text: str, stop_words: Set[str], min_length: int) -> List[str]:
    """Extract keywords from text.

    Args:
        text: Input text to process
        stop_words: Set of stop words to exclude
        min_length: Minimum keyword length

    Returns:
        List of extracted keywords
    """
    text_lower = text.lower()
    words = re.findall(r"\b[a-z]+\b", text_lower)
    keywords = [
        word
        for word in words
        if len(word) >= min_length and word not in stop_words
    ]
    return keywords


def identify_themes(
    feedback_items: List[FeedbackItem], config: ThemeConfig
) -> List[Theme]:
    """Identify common themes from feedback.

    Args:
        feedback_items: List of feedback items to analyze
        config: Theme identification configuration

    Returns:
        List of identified themes sorted by frequency
    """
    if not feedback_items:
        return []

    stop_words_set = set(word.lower() for word in config.stop_words)
    keyword_to_feedback: Dict[str, List[str]] = {}

    for item in feedback_items:
        keywords = extract_keywords(
            item.text, stop_words_set, config.min_keyword_length
        )
        for keyword in keywords:
            if keyword not in keyword_to_feedback:
                keyword_to_feedback[keyword] = []
            keyword_to_feedback[keyword].append(item.text)

    total_count = len(feedback_items)
    themes = []

    for keyword, feedback_samples in keyword_to_feedback.items():
        frequency = len(feedback_samples)
        if frequency >= config.min_occurrences:
            percentage = (frequency / total_count) * 100
            sample_feedback = feedback_samples[:5]
            themes.append(
                Theme(
                    keywords=[keyword],
                    frequency=frequency,
                    percentage=percentage,
                    sample_feedback=sample_feedback,
                )
            )

    themes.sort(key=lambda x: x.frequency, reverse=True)
    logger.info(f"Identified {len(themes)} themes from feedback")
    return themes


def generate_roadmap_recommendations(
    themes: List[Theme], config: RoadmapConfig, total_feedback: int
) -> List[RoadmapRecommendation]:
    """Generate product roadmap recommendations from themes.

    Args:
        themes: List of identified themes
        config: Roadmap generation configuration
        total_feedback: Total number of feedback items

    Returns:
        List of roadmap recommendations sorted by priority and frequency
    """
    recommendations = []

    for theme in themes[: config.max_recommendations]:
        frequency_ratio = theme.frequency / total_feedback if total_feedback > 0 else 0

        if frequency_ratio >= config.high_priority_threshold:
            priority = "High"
        elif frequency_ratio >= config.medium_priority_threshold:
            priority = "Medium"
        else:
            priority = "Low"

        rationale = (
            f"Appears in {theme.frequency} feedback items "
            f"({theme.percentage:.1f}% of total). "
            f"Addressing this theme could improve satisfaction for "
            f"a significant portion of customers."
        )

        recommendations.append(
            RoadmapRecommendation(
                theme=" ".join(theme.keywords),
                priority=priority,
                frequency=theme.frequency,
                percentage=theme.percentage,
                rationale=rationale,
                sample_feedback=theme.sample_feedback,
            )
        )

    recommendations.sort(
        key=lambda x: (
            {"High": 0, "Medium": 1, "Low": 2}[x.priority],
            -x.frequency,
        )
    )

    logger.info(f"Generated {len(recommendations)} roadmap recommendations")
    return recommendations


def write_markdown_report(
    analysis: FeedbackAnalysis, output_path: Path
) -> None:
    """Write analysis results to markdown report.

    Args:
        analysis: Complete feedback analysis results
        output_path: Path to write the markdown report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Customer Feedback Analysis Report\n\n")
        f.write(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Summary\n\n")
        f.write(f"- **Total Feedback Items:** {analysis.total_feedback_count}\n")
        f.write(f"- **Data Sources:** {len(analysis.sources_summary)}\n")
        f.write(f"- **Identified Themes:** {len(analysis.themes)}\n")
        f.write(f"- **Roadmap Recommendations:** {len(analysis.recommendations)}\n\n")

        f.write("## Data Sources Summary\n\n")
        for source, count in sorted(
            analysis.sources_summary.items(), key=lambda x: -x[1]
        ):
            f.write(f"- **{source}:** {count} items\n")
        f.write("\n")

        f.write("## Identified Themes\n\n")
        if analysis.themes:
            f.write("| Theme | Frequency | Percentage |\n")
            f.write("|-------|-----------|------------|\n")
            for theme in analysis.themes[:20]:
                theme_name = " ".join(theme.keywords)
                f.write(
                    f"| {theme_name} | {theme.frequency} | "
                    f"{theme.percentage:.1f}% |\n"
                )
        else:
            f.write("No themes identified.\n")
        f.write("\n")

        f.write("## Product Roadmap Recommendations\n\n")
        if analysis.recommendations:
            for i, rec in enumerate(analysis.recommendations, 1):
                f.write(f"### {i}. {rec.theme} (Priority: {rec.priority})\n\n")
                f.write(f"**Frequency:** {rec.frequency} occurrences ({rec.percentage:.1f}%)\n\n")
                f.write(f"**Rationale:** {rec.rationale}\n\n")
                f.write("**Sample Feedback:**\n\n")
                for sample in rec.sample_feedback[:3]:
                    f.write(f"- {sample[:200]}{'...' if len(sample) > 200 else ''}\n")
                f.write("\n")
        else:
            f.write("No recommendations generated.\n")

    logger.info(f"Analysis report written to: {output_path}")


def process_feedback(config_path: Path) -> FeedbackAnalysis:
    """Process customer feedback and generate analysis.

    Args:
        config_path: Path to configuration file

    Returns:
        Complete feedback analysis results

    Raises:
        FileNotFoundError: If config or source files are missing
        ValueError: If configuration or data is invalid
    """
    config = load_config(config_path)
    feedback_items = load_all_feedback(config)

    if not feedback_items:
        logger.warning("No feedback items loaded. Check source configurations.")
        return FeedbackAnalysis(
            total_feedback_count=0,
            sources_summary={},
            themes=[],
            recommendations=[],
        )

    sources_summary = Counter(item.source for item in feedback_items)
    themes = identify_themes(feedback_items, config.theme)
    recommendations = generate_roadmap_recommendations(
        themes, config.roadmap, len(feedback_items)
    )

    analysis = FeedbackAnalysis(
        total_feedback_count=len(feedback_items),
        sources_summary=dict(sources_summary),
        themes=themes,
        recommendations=recommendations,
    )

    output_path = Path(config.output_path)
    write_markdown_report(analysis, output_path)

    return analysis


def main() -> None:
    """Main entry point for the feedback processor."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting customer feedback processing")
        analysis = process_feedback(config_path)
        logger.info(
            f"Processing complete. Analyzed {analysis.total_feedback_count} "
            f"feedback items and generated {len(analysis.recommendations)} "
            "recommendations."
        )
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
        raise


if __name__ == "__main__":
    main()
