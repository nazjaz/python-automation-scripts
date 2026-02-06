# Customer Engagement Monitor API Documentation

## Overview

This document describes the public API for the customer engagement monitoring system.

## Configuration Models

### EngagementDataConfig

Configuration for engagement data source.

**Fields:**
- `file_path` (str): Path to engagement data file
- `format` (str): File format (`csv` or `json`)
- `customer_id_column` (str): Column name for customer ID
- `touchpoint_column` (str): Column name for touchpoint type
- `timestamp_column` (str): Column name for timestamp
- `engagement_score_column` (Optional[str]): Column name for engagement score

### PurchaseDataConfig

Configuration for purchase data source.

**Fields:**
- `file_path` (str): Path to purchase data file
- `format` (str): File format (`csv` or `json`)
- `customer_id_column` (str): Column name for customer ID
- `purchase_date_column` (str): Column name for purchase date
- `amount_column` (str): Column name for purchase amount

### LTVConfig

Configuration for LTV calculation.

**Fields:**
- `discount_rate` (float): Discount rate for LTV calculation
- `average_customer_lifespan_years` (float): Average customer lifespan in years
- `lookback_months` (int): Months to look back for revenue calculation

### SegmentationConfig

Configuration for customer segmentation.

**Fields:**
- `ltv_threshold_high` (float): High LTV threshold
- `ltv_threshold_medium` (float): Medium LTV threshold
- `engagement_threshold_high` (float): High engagement threshold
- `engagement_threshold_low` (float): Low engagement threshold
- `recency_threshold_days` (int): Days for recency threshold

## Data Models

### EngagementRecord

Represents an engagement record.

**Fields:**
- `customer_id` (str): Customer identifier
- `touchpoint` (TouchpointType): Touchpoint type
- `timestamp` (datetime): Engagement timestamp
- `engagement_score` (Optional[float]): Engagement score

### PurchaseRecord

Represents a purchase record.

**Fields:**
- `customer_id` (str): Customer identifier
- `purchase_date` (datetime): Purchase date
- `amount` (float): Purchase amount

### CustomerMetrics

Customer engagement and value metrics.

**Fields:**
- `customer_id` (str): Customer identifier
- `lifetime_value` (float): Calculated LTV
- `total_revenue` (float): Total revenue
- `purchase_count` (int): Number of purchases
- `engagement_score` (float): Engagement score (0.0 to 1.0)
- `touchpoint_count` (Dict[TouchpointType, int]): Count by touchpoint type
- `last_engagement_date` (Optional[datetime]): Last engagement date
- `days_since_last_engagement` (Optional[int]): Days since last engagement
- `segment` (SegmentTier): Assigned segment tier

### SegmentAnalysis

Analysis for a customer segment.

**Fields:**
- `segment` (SegmentTier): Segment tier
- `customer_count` (int): Number of customers in segment
- `avg_ltv` (float): Average LTV for segment
- `avg_engagement_score` (float): Average engagement score
- `total_revenue` (float): Total revenue for segment
- `recommendations` (List[str]): Engagement strategy recommendations

### EngagementAnalysis

Complete engagement analysis results.

**Fields:**
- `total_customers` (int): Total number of customers
- `customer_metrics` (List[CustomerMetrics]): Metrics for all customers
- `segment_analyses` (List[SegmentAnalysis]): Analysis for each segment
- `overall_metrics` (Dict[str, float]): Overall metrics
- `generated_at` (datetime): Analysis generation timestamp

## Enumerations

### TouchpointType

Customer touchpoint types.

**Values:**
- `EMAIL`: Email engagement
- `WEB`: Web engagement
- `MOBILE`: Mobile app engagement
- `SOCIAL`: Social media engagement
- `SUPPORT`: Support interaction
- `PURCHASE`: Purchase transaction
- `REVIEW`: Product review

### SegmentTier

Customer segment tier levels.

**Values:**
- `CHAMPION`: High LTV and high engagement
- `LOYAL`: High LTV or high engagement
- `POTENTIAL`: Medium value with growth opportunity
- `AT_RISK`: Low recent engagement
- `LOST`: No engagement for extended period

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

### calculate_ltv(purchases: List[PurchaseRecord], customer_id: str, config: LTVConfig) -> Tuple[float, float, int]

Calculate customer lifetime value.

**Parameters:**
- `purchases` (List[PurchaseRecord]): List of purchase records
- `customer_id` (str): Customer identifier
- `config` (LTVConfig): LTV configuration

**Returns:**
- `Tuple[float, float, int]`: (LTV, total_revenue, purchase_count)

### calculate_engagement_score(engagements: List[EngagementRecord], customer_id: str) -> Tuple[float, Dict[TouchpointType, int], Optional[datetime]]

Calculate customer engagement score.

**Parameters:**
- `engagements` (List[EngagementRecord]): List of engagement records
- `customer_id` (str): Customer identifier

**Returns:**
- `Tuple[float, Dict[TouchpointType, int], Optional[datetime]]`: (score, touchpoint_counts, last_engagement)

### assign_segment(metrics: CustomerMetrics, config: SegmentationConfig) -> SegmentTier

Assign customer to segment based on metrics.

**Parameters:**
- `metrics` (CustomerMetrics): Customer metrics
- `config` (SegmentationConfig): Segmentation configuration

**Returns:**
- `SegmentTier`: Assigned segment tier

### generate_segment_strategies(segment: SegmentTier, analysis: SegmentAnalysis) -> List[str]

Generate engagement strategies for a segment.

**Parameters:**
- `segment` (SegmentTier): Segment tier
- `analysis` (SegmentAnalysis): Segment analysis

**Returns:**
- `List[str]`: List of strategy recommendations

### process_engagement_analysis(config_path: Path) -> EngagementAnalysis

Process engagement data and generate analysis.

**Parameters:**
- `config_path` (Path): Path to configuration file

**Returns:**
- `EngagementAnalysis`: Complete engagement analysis

**Raises:**
- `FileNotFoundError`: If config or data files are missing
- `ValueError`: If configuration is invalid

## Example Usage

```python
from pathlib import Path
from customer_engagement_monitor.src.main import process_engagement_analysis

config_path = Path("config.yaml")
analysis = process_engagement_analysis(config_path)

print(f"Total Customers: {analysis.total_customers}")
print(f"Average LTV: ${analysis.overall_metrics['avg_ltv']:,.2f}")

for segment_analysis in analysis.segment_analyses:
    print(f"\n{segment_analysis.segment.value}: {segment_analysis.customer_count} customers")
    print(f"Average LTV: ${segment_analysis.avg_ltv:,.2f}")
    print("Strategies:")
    for strategy in segment_analysis.recommendations:
        print(f"  - {strategy}")
```
