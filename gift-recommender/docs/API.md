# Gift Recommender API Documentation

## Overview

The Gift Recommender provides a comprehensive API for managing recipients, preferences, purchase history, and generating personalized gift recommendations based on multiple factors.

## Architecture

The system is built with a modular architecture:

- **Preference Analyzer**: Analyzes recipient preferences and calculates category scores
- **Purchase Analyzer**: Analyzes purchase history to identify patterns and preferences
- **Occasion Handler**: Handles special occasions and applies multipliers
- **Price Filter**: Filters and categorizes items by price range
- **Recommendation Engine**: Core engine that combines all factors to generate recommendations
- **Report Generator**: Creates HTML and CSV reports with recommendations

## Database Schema

### Recipient

Stores recipient information.

- `id`: Primary key
- `name`: Recipient name
- `email`: Email address (unique)
- `age`: Age
- `relationship`: Relationship type
- `created_at`: When record was created
- `updated_at`: When record was last updated

### Preference

Stores recipient preferences by category.

- `id`: Primary key
- `recipient_id`: Foreign key to Recipient
- `category`: Preference category
- `interest`: Interest description
- `priority`: Priority level (1-10)
- `created_at`: When record was created

### PurchaseHistory

Stores historical purchase data.

- `id`: Primary key
- `recipient_id`: Foreign key to Recipient
- `item_name`: Name of purchased item
- `category`: Item category
- `price`: Purchase price
- `purchase_date`: Date of purchase
- `rating`: Rating (1-5)
- `notes`: Optional notes
- `created_at`: When record was created

### GiftItem

Stores gift catalog items.

- `id`: Primary key
- `name`: Item name
- `category`: Item category
- `description`: Item description
- `price`: Item price
- `brand`: Brand name
- `tags`: Comma-separated tags
- `availability`: Availability status
- `created_at`: When record was created
- `updated_at`: When record was last updated

### Recommendation

Stores generated recommendations.

- `id`: Primary key
- `recipient_id`: Foreign key to Recipient
- `gift_item_id`: Foreign key to GiftItem
- `occasion`: Occasion type
- `score`: Recommendation score (0.0 to 1.0)
- `price_range`: Price range category
- `reasoning`: Reasoning text
- `created_at`: When recommendation was created

## Usage Examples

### Adding a Recipient

```python
from src.config import load_config, get_settings
from src.database import DatabaseManager

config = load_config()
settings = get_settings()
db_manager = DatabaseManager(settings.database.url)
db_manager.create_tables()

recipient = db_manager.add_recipient(
    name="John Doe",
    email="john@example.com",
    age=30,
    relationship="friend",
)
```

### Adding Preferences

```python
db_manager.add_preference(
    recipient_id=recipient.id,
    category="electronics",
    interest="gadgets",
    priority=5,
)
```

### Adding Purchase History

```python
from datetime import datetime

db_manager.add_purchase(
    recipient_id=recipient.id,
    item_name="Smart Watch",
    purchase_date=datetime.utcnow(),
    category="electronics",
    price=199.99,
    rating=5,
)
```

### Generating Recommendations

```python
from src.recommendation_engine import RecommendationEngine

engine = RecommendationEngine(db_manager, config)
recommendations = engine.generate_recommendations(
    recipient_id=recipient.id,
    occasion="birthday",
    price_range="medium",
    max_recommendations=10,
)
```

### Generating Reports

```python
from src.report_generator import ReportGenerator

generator = ReportGenerator(db_manager, engine, output_dir="reports")
html_path = generator.generate_html_report(
    recipient_id=recipient.id,
    recommendations=recommendations,
    occasion="birthday",
)
```

## Recommendation Scoring

The recommendation engine uses a weighted scoring system:

1. **Preference Score** (default 40%): Based on recipient's stated preferences
2. **Purchase History Score** (default 30%): Based on purchase frequency by category
3. **Price Score** (default 10%): How well price matches target
4. **Occasion Multiplier** (default 20%): Multiplier based on occasion type

Final score = (preference_score × 0.4 + purchase_score × 0.3 + price_score × 0.1) × occasion_multiplier

## Price Ranges

Default price range categories:

- **budget**: $0 - $0
- **low**: $0 - $25
- **medium**: $25 - $100
- **high**: $100 - $500
- **premium**: $500 - $1000
- **luxury**: $1000+

## Occasion Types

Supported occasion types with multipliers:

- **birthday**: 1.2x multiplier
- **anniversary**: 1.15x multiplier
- **wedding**: 1.3x multiplier
- **graduation**: 1.1x multiplier
- **holiday**: 1.1x multiplier
- **thank_you**: 1.0x multiplier
- **congratulations**: 1.1x multiplier
- **get_well**: 1.05x multiplier

## Extending the System

### Adding New Categories

1. Add category to `gift_catalog.categories` in `config.yaml`
2. Update gift items with new category
3. Add preferences for recipients in new category

### Customizing Scoring Weights

Modify weights in `config.yaml`:

```yaml
recommendations:
  preference_weight: 0.4
  purchase_history_weight: 0.3
  occasion_weight: 0.2
  price_weight: 0.1
```

### Adding New Occasion Types

1. Add occasion type to `occasions.types` in `config.yaml`
2. Add multiplier to `occasions.occasion_multipliers`
3. Update `OccasionHandler.get_occasion_context()` if needed
