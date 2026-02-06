# Shopping Recommendation Engine API Documentation

## Overview

This document describes the public API for the shopping recommendation engine system.

## Configuration Models

### PurchaseHistoryConfig

Configuration for purchase history data source.

**Fields:**
- `file_path` (str): Path to purchase history file
- `format` (str): File format (`csv` or `json`)
- `customer_id_column` (str): Column name for customer ID
- `product_id_column` (str): Column name for product ID
- `purchase_date_column` (str): Column name for purchase date
- `quantity_column` (Optional[str]): Column name for quantity
- `category_column` (Optional[str]): Column name for product category
- `price_column` (Optional[str]): Column name for price

### BrowsingBehaviorConfig

Configuration for browsing behavior data source.

**Fields:**
- `file_path` (str): Path to browsing behavior file
- `format` (str): File format (`csv` or `json`)
- `customer_id_column` (str): Column name for customer ID
- `product_id_column` (str): Column name for product ID
- `timestamp_column` (str): Column name for timestamp
- `action_type_column` (Optional[str]): Column name for action type
- `view_duration_column` (Optional[str]): Column name for view duration

### InventoryConfig

Configuration for inventory data source.

**Fields:**
- `file_path` (str): Path to inventory file
- `format` (str): File format (`csv` or `json`)
- `product_id_column` (str): Column name for product ID
- `quantity_column` (str): Column name for available quantity
- `in_stock_column` (Optional[str]): Column name for in-stock status

### SeasonalTrendsConfig

Configuration for seasonal trends.

**Fields:**
- `enable_seasonal_boost` (bool): Enable seasonal trend boosting
- `seasonal_categories` (Dict[str, List[int]]): Mapping of seasons to month numbers
- `seasonal_boost_multiplier` (float): Multiplier for seasonal products

### RecommendationConfig

Configuration for recommendation generation.

**Fields:**
- `max_recommendations` (int): Maximum number of recommendations
- `min_score_threshold` (float): Minimum recommendation score
- `purchase_history_weight` (float): Weight for purchase history
- `browsing_weight` (float): Weight for browsing behavior
- `seasonal_weight` (float): Weight for seasonal trends
- `require_in_stock` (bool): Only recommend in-stock items

## Data Models

### PurchaseRecord

Represents a purchase record.

**Fields:**
- `customer_id` (str): Customer identifier
- `product_id` (str): Product identifier
- `purchase_date` (datetime): Purchase date
- `quantity` (int): Purchase quantity
- `category` (Optional[str]): Product category
- `price` (Optional[float]): Purchase price

### BrowsingRecord

Represents a browsing behavior record.

**Fields:**
- `customer_id` (str): Customer identifier
- `product_id` (str): Product identifier
- `timestamp` (datetime): Browsing timestamp
- `action_type` (Optional[str]): Action type (view, add_to_cart, etc.)
- `view_duration` (Optional[float]): View duration in seconds

### InventoryItem

Represents an inventory item.

**Fields:**
- `product_id` (str): Product identifier
- `quantity` (int): Available quantity
- `in_stock` (bool): In-stock status

### Recommendation

Personalized shopping recommendation.

**Fields:**
- `product_id` (str): Product identifier
- `customer_id` (str): Customer identifier
- `score` (float): Recommendation score
- `priority` (RecommendationPriority): Priority level
- `reasons` (List[str]): List of recommendation reasons
- `category` (Optional[str]): Product category
- `in_stock` (bool): In-stock status
- `available_quantity` (int): Available quantity

### RecommendationAnalysis

Complete recommendation analysis results.

**Fields:**
- `customer_id` (str): Customer identifier
- `recommendations` (List[Recommendation]): Generated recommendations
- `purchase_history_summary` (Dict[str, int]): Purchase history summary
- `browsing_summary` (Dict[str, int]): Browsing behavior summary
- `seasonal_products` (List[str]): List of seasonal product IDs
- `generated_at` (datetime): Generation timestamp

## Enumerations

### RecommendationPriority

Priority level for recommendations.

**Values:**
- `HIGH`: High priority recommendation
- `MEDIUM`: Medium priority recommendation
- `LOW`: Low priority recommendation

## Functions

### load_config(config_path: Path) -> Config

Load and validate configuration from YAML file.

**Parameters:**
- `config_path` (Path): Path to configuration YAML file

**Returns:**
- `Config`: Validated configuration object

**Raises:**
- `FileNotFoundError`: If config file does not exist
- `ValueError`: If configuration is invalid

### load_purchase_history(config: PurchaseHistoryConfig, project_root: Path) -> List[PurchaseRecord]

Load purchase history data from file.

**Parameters:**
- `config` (PurchaseHistoryConfig): Purchase history configuration
- `project_root` (Path): Project root directory

**Returns:**
- `List[PurchaseRecord]`: List of purchase records

**Raises:**
- `FileNotFoundError`: If data file does not exist
- `ValueError`: If data format is invalid

### analyze_purchase_history(purchases: List[PurchaseRecord], customer_id: str) -> Dict[str, float]

Analyze purchase history for a customer.

**Parameters:**
- `purchases` (List[PurchaseRecord]): List of purchase records
- `customer_id` (str): Customer identifier

**Returns:**
- `Dict[str, float]`: Dictionary mapping product_id to purchase score

### analyze_browsing_behavior(browsing_records: List[BrowsingRecord], customer_id: str) -> Dict[str, float]

Analyze browsing behavior for a customer.

**Parameters:**
- `browsing_records` (List[BrowsingRecord]): List of browsing records
- `customer_id` (str): Customer identifier

**Returns:**
- `Dict[str, float]`: Dictionary mapping product_id to browsing score

### identify_seasonal_products(purchases: List[PurchaseRecord], seasonal_config: SeasonalTrendsConfig) -> Set[str]

Identify products with seasonal trends.

**Parameters:**
- `purchases` (List[PurchaseRecord]): List of purchase records
- `seasonal_config` (SeasonalTrendsConfig): Seasonal trends configuration

**Returns:**
- `Set[str]`: Set of product IDs with seasonal patterns

### generate_recommendations(...) -> List[Recommendation]

Generate personalized recommendations for a customer.

**Parameters:**
- `customer_id` (str): Customer identifier
- `purchase_scores` (Dict[str, float]): Purchase history scores
- `browsing_scores` (Dict[str, float]): Browsing behavior scores
- `seasonal_products` (Set[str]): Set of seasonal product IDs
- `inventory` (Dict[str, InventoryItem]): Dictionary of inventory items
- `purchases` (List[PurchaseRecord]): List of purchase records
- `config` (RecommendationConfig): Recommendation configuration
- `seasonal_config` (SeasonalTrendsConfig): Seasonal trends configuration

**Returns:**
- `List[Recommendation]`: List of recommendations sorted by score

### process_recommendations(config_path: Path, customer_id: str) -> RecommendationAnalysis

Process data and generate recommendations for a customer.

**Parameters:**
- `config_path` (Path): Path to configuration file
- `customer_id` (str): Customer identifier

**Returns:**
- `RecommendationAnalysis`: Complete recommendation analysis

**Raises:**
- `FileNotFoundError`: If config or data files are missing
- `ValueError`: If configuration is invalid

## Example Usage

```python
from pathlib import Path
from shopping_recommendation_engine.src.main import process_recommendations

config_path = Path("config.yaml")
customer_id = "cust_001"

analysis = process_recommendations(config_path, customer_id)

print(f"Generated {len(analysis.recommendations)} recommendations")
for rec in analysis.recommendations:
    print(f"- {rec.product_id}: {rec.score:.2f} ({rec.priority.value})")
    print(f"  Reasons: {', '.join(rec.reasons)}")
    print(f"  In Stock: {rec.in_stock}, Available: {rec.available_quantity}")
```
