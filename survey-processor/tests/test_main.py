"""Unit tests for survey processing system."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, Survey, Question, Response, Answer
from src.response_processor import ResponseProcessor
from src.survey_analyzer import SurveyAnalyzer
from src.trend_identifier import TrendIdentifier
from src.satisfaction_calculator import SatisfactionCalculator
from src.summary_generator import SummaryGenerator


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "import": {
            "csv_encoding": "utf-8",
        },
        "analysis": {
            "analysis_enabled": True,
        },
        "trends": {
            "min_occurrences": 3,
            "confidence_threshold": 0.6,
        },
        "satisfaction": {
            "rating_questions_weight": 0.7,
            "choice_questions_weight": 0.3,
        },
        "summary": {
            "summary_template": {},
        },
        "reporting": {
            "generate_html": True,
            "generate_csv": True,
            "output_directory": "reports",
        },
        "logging": {
            "file": "logs/test.log",
            "format": "%(asctime)s - %(levelname)s - %(message)s",
        },
    }


@pytest.fixture
def db_manager():
    """Database manager fixture."""
    return DatabaseManager("sqlite:///:memory:")


def test_survey_analyzer_analyze_survey(db_manager, sample_config):
    """Test analyzing survey."""
    db_manager.create_tables()
    survey = db_manager.add_survey("Test Survey", "Test description")
    question = db_manager.add_question(
        survey.id, "How satisfied are you?", "rating", question_order=1
    )
    
    response = db_manager.add_response(survey.id, "respondent1")
    db_manager.add_answer(response.id, question.id, answer_value=4.5)
    
    analyzer = SurveyAnalyzer(db_manager, sample_config["analysis"])
    analysis = analyzer.analyze_survey(survey.id)
    
    assert analysis["total_responses"] == 1
    assert len(analysis["question_analyses"]) > 0


def test_trend_identifier_identify_trends(db_manager, sample_config):
    """Test identifying trends."""
    db_manager.create_tables()
    survey = db_manager.add_survey("Test Survey")
    question = db_manager.add_question(
        survey.id, "How satisfied are you?", "rating", question_order=1
    )
    
    for i in range(5):
        response = db_manager.add_response(survey.id, f"respondent{i}")
        db_manager.add_answer(response.id, question.id, answer_value=4.5)
    
    identifier = TrendIdentifier(db_manager, sample_config["trends"])
    trends = identifier.identify_trends(survey.id)
    
    assert len(trends) > 0


def test_satisfaction_calculator_calculate_scores(db_manager, sample_config):
    """Test calculating satisfaction scores."""
    db_manager.create_tables()
    survey = db_manager.add_survey("Test Survey")
    question = db_manager.add_question(
        survey.id, "How satisfied are you?", "rating", question_order=1
    )
    
    response = db_manager.add_response(survey.id, "respondent1")
    db_manager.add_answer(response.id, question.id, answer_value=4.5)
    
    calculator = SatisfactionCalculator(db_manager, sample_config["satisfaction"])
    result = calculator.calculate_satisfaction_scores(survey.id)
    
    assert result["calculated_count"] > 0


def test_satisfaction_calculator_get_statistics(db_manager, sample_config):
    """Test getting satisfaction statistics."""
    db_manager.create_tables()
    survey = db_manager.add_survey("Test Survey")
    question = db_manager.add_question(
        survey.id, "How satisfied are you?", "rating", question_order=1
    )
    
    for i in range(3):
        response = db_manager.add_response(survey.id, f"respondent{i}")
        db_manager.add_answer(response.id, question.id, answer_value=4.0 + i * 0.5)
        db_manager.update_response_satisfaction(response.id, 4.0 + i * 0.5)
    
    calculator = SatisfactionCalculator(db_manager, sample_config["satisfaction"])
    stats = calculator.get_satisfaction_statistics(survey.id)
    
    assert stats["average"] > 0
    assert "distribution" in stats


def test_summary_generator_generate_summary(db_manager, sample_config):
    """Test generating executive summary."""
    db_manager.create_tables()
    survey = db_manager.add_survey("Test Survey")
    question = db_manager.add_question(
        survey.id, "How satisfied are you?", "rating", question_order=1
    )
    
    response = db_manager.add_response(survey.id, "respondent1")
    db_manager.add_answer(response.id, question.id, answer_value=4.5)
    db_manager.update_response_satisfaction(response.id, 4.5)
    
    generator = SummaryGenerator(db_manager, sample_config["summary"])
    summary = generator.generate_summary(survey.id)
    
    assert summary is not None
    assert "summary_text" in summary
    assert "satisfaction_score" in summary


def test_database_manager_add_survey(db_manager):
    """Test adding survey."""
    db_manager.create_tables()
    survey = db_manager.add_survey("Test Survey", "Test description")
    
    assert survey.id is not None
    assert survey.survey_name == "Test Survey"


def test_database_manager_add_question(db_manager):
    """Test adding question."""
    db_manager.create_tables()
    survey = db_manager.add_survey("Test Survey")
    question = db_manager.add_question(
        survey.id, "How satisfied are you?", "rating", question_order=1
    )
    
    assert question.id is not None
    assert question.question_text == "How satisfied are you?"


def test_database_manager_add_response(db_manager):
    """Test adding response."""
    db_manager.create_tables()
    survey = db_manager.add_survey("Test Survey")
    response = db_manager.add_response(survey.id, "respondent1", "test@example.com")
    
    assert response.id is not None
    assert response.respondent_id == "respondent1"


def test_database_manager_add_answer(db_manager):
    """Test adding answer."""
    db_manager.create_tables()
    survey = db_manager.add_survey("Test Survey")
    question = db_manager.add_question(
        survey.id, "How satisfied are you?", "rating", question_order=1
    )
    response = db_manager.add_response(survey.id, "respondent1")
    
    answer = db_manager.add_answer(response.id, question.id, answer_value=4.5)
    
    assert answer.id is not None
    assert answer.answer_value == 4.5


def test_trend_identifier_identify_rating_trend(db_manager, sample_config):
    """Test identifying rating trend."""
    db_manager.create_tables()
    survey = db_manager.add_survey("Test Survey")
    question = db_manager.add_question(
        survey.id, "How satisfied are you?", "rating", question_order=1
    )
    
    for i in range(5):
        response = db_manager.add_response(survey.id, f"respondent{i}")
        db_manager.add_answer(response.id, question.id, answer_value=4.5)
    
    identifier = TrendIdentifier(db_manager, sample_config["trends"])
    trend = identifier._identify_rating_trend(question, [])
    
    responses = db_manager.get_survey_responses(survey.id)
    answers = []
    for response in responses:
        for answer in response.answers:
            if answer.question_id == question.id:
                answers.append(answer)
    
    trend = identifier._identify_rating_trend(question, answers)
    
    if trend:
        assert "trend_type" in trend
        assert "confidence_score" in trend
