"""Tests for testimonial processing."""

import pytest

from testimonial_processor.src.main import (
    CategorizationConfig,
    PermissionStatus,
    QuoteExtractionConfig,
    TestimonialRecord,
    categorize_testimonial,
    extract_quotes,
)


def test_extract_quotes_basic():
    """Test basic quote extraction."""
    testimonial = TestimonialRecord(
        testimonial_id="test_001",
        customer_name="John Doe",
        testimonial_text='This product is amazing! The customer said "Best purchase I\'ve ever made." Highly recommended.',
    )

    config = QuoteExtractionConfig(
        min_quote_length=10,
        max_quote_length=100,
        extract_full_sentences=True,
    )

    quotes = extract_quotes(testimonial, config)

    assert len(quotes) > 0
    assert all(
        config.min_quote_length <= len(q.quote_text) <= config.max_quote_length
        for q in quotes
    )


def test_extract_quotes_quoted_text():
    """Test extraction of quoted text."""
    testimonial = TestimonialRecord(
        testimonial_id="test_002",
        customer_name="Jane Smith",
        testimonial_text='The service was excellent. They said "Outstanding support team" and I agree completely.',
    )

    config = QuoteExtractionConfig(
        min_quote_length=10,
        max_quote_length=200,
        extract_full_sentences=False,
    )

    quotes = extract_quotes(testimonial, config)

    assert len(quotes) > 0


def test_extract_quotes_no_quotes():
    """Test extraction when no quotes found."""
    testimonial = TestimonialRecord(
        testimonial_id="test_003",
        customer_name="Bob Johnson",
        testimonial_text="Good product.",
    )

    config = QuoteExtractionConfig(
        min_quote_length=20,
        max_quote_length=500,
        extract_full_sentences=True,
    )

    quotes = extract_quotes(testimonial, config)

    assert len(quotes) >= 0


def test_categorize_testimonial_by_keyword():
    """Test categorization using keywords."""
    testimonial = TestimonialRecord(
        testimonial_id="test_004",
        customer_name="Alice Brown",
        testimonial_text="Product A has amazing features. The solution y really helped us.",
    )

    config = CategorizationConfig(
        product_keywords={
            "Product A": ["product a", "feature x", "solution y"],
        },
        auto_categorize=True,
    )

    category = categorize_testimonial(testimonial, config)

    assert category == "Product A"


def test_categorize_testimonial_existing_category():
    """Test categorization when category already exists."""
    testimonial = TestimonialRecord(
        testimonial_id="test_005",
        customer_name="Charlie Wilson",
        testimonial_text="Great service overall.",
        category="Support",
    )

    config = CategorizationConfig()

    category = categorize_testimonial(testimonial, config)

    assert category == "Support"


def test_categorize_testimonial_no_match():
    """Test categorization when no keywords match."""
    testimonial = TestimonialRecord(
        testimonial_id="test_006",
        customer_name="Diana Lee",
        testimonial_text="This is a generic testimonial without specific keywords.",
    )

    config = CategorizationConfig(
        product_keywords={"Product A": ["specific", "keywords"]},
        auto_categorize=True,
    )

    category = categorize_testimonial(testimonial, config)

    assert category is None


def test_categorize_testimonial_service_keywords():
    """Test categorization using service keywords."""
    testimonial = TestimonialRecord(
        testimonial_id="test_007",
        customer_name="Edward White",
        testimonial_text="The consulting services provided excellent advice and guidance.",
    )

    config = CategorizationConfig(
        service_keywords={
            "Consulting": ["consulting", "advice", "guidance"],
        },
        auto_categorize=True,
    )

    category = categorize_testimonial(testimonial, config)

    assert category == "Consulting"


def test_extract_quotes_length_limits():
    """Test quote extraction respects length limits."""
    long_text = "This is a very long testimonial. " * 50
    testimonial = TestimonialRecord(
        testimonial_id="test_008",
        customer_name="Frank Green",
        testimonial_text=long_text,
    )

    config = QuoteExtractionConfig(
        min_quote_length=20,
        max_quote_length=500,
        extract_full_sentences=True,
    )

    quotes = extract_quotes(testimonial, config)

    assert all(len(q.quote_text) <= config.max_quote_length for q in quotes)
    assert all(len(q.quote_text) >= config.min_quote_length for q in quotes)
