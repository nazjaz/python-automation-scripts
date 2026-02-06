"""Cleans research datasets."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class DataCleaner:
    """Cleans research datasets."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize data cleaner.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.cleaning_config = config.get("data_cleaning", {})

    def load_dataset(
        self,
        file_path: str,
    ) -> pd.DataFrame:
        """Load dataset from file.

        Args:
            file_path: Path to dataset file.

        Returns:
            Loaded DataFrame.

        Raises:
            ValueError: If file format is not supported.
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_extension = file_path_obj.suffix.lower()

        if file_extension == ".csv":
            df = pd.read_csv(file_path)
        elif file_extension in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        elif file_extension == ".json":
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        logger.info(
            f"Loaded dataset: {file_path}",
            extra={"file_path": file_path, "shape": df.shape},
        )

        return df

    def clean_dataset(
        self,
        df: pd.DataFrame,
        missing_value_strategy: Optional[str] = None,
        remove_duplicates: Optional[bool] = None,
        remove_outliers: bool = True,
    ) -> Tuple[pd.DataFrame, Dict]:
        """Clean dataset.

        Args:
            df: Input DataFrame.
            missing_value_strategy: Optional missing value handling strategy.
            remove_duplicates: Optional flag to remove duplicates.
            remove_outliers: Flag to remove outliers.

        Returns:
            Tuple of (cleaned DataFrame, cleaning report dictionary).
        """
        original_shape = df.shape
        report = {
            "original_rows": original_shape[0],
            "original_columns": original_shape[1],
            "missing_values_removed": 0,
            "duplicates_removed": 0,
            "outliers_removed": 0,
        }

        df_cleaned = df.copy()

        missing_strategy = missing_value_strategy or self.cleaning_config.get("missing_value_strategies", ["drop"])[0]

        if missing_strategy == "drop":
            rows_before = len(df_cleaned)
            df_cleaned = df_cleaned.dropna()
            report["missing_values_removed"] = rows_before - len(df_cleaned)
        elif missing_strategy == "mean":
            numeric_cols = df_cleaned.select_dtypes(include=[np.number]).columns
            df_cleaned[numeric_cols] = df_cleaned[numeric_cols].fillna(df_cleaned[numeric_cols].mean())
        elif missing_strategy == "median":
            numeric_cols = df_cleaned.select_dtypes(include=[np.number]).columns
            df_cleaned[numeric_cols] = df_cleaned[numeric_cols].fillna(df_cleaned[numeric_cols].median())
        elif missing_strategy == "mode":
            for col in df_cleaned.columns:
                mode_value = df_cleaned[col].mode()
                if len(mode_value) > 0:
                    df_cleaned[col] = df_cleaned[col].fillna(mode_value[0])
        elif missing_strategy == "forward_fill":
            df_cleaned = df_cleaned.fillna(method="ffill")
        elif missing_strategy == "backward_fill":
            df_cleaned = df_cleaned.fillna(method="bfill")

        if remove_duplicates is None:
            remove_duplicates = self.cleaning_config.get("duplicate_handling", "drop") == "drop"

        if remove_duplicates:
            rows_before = len(df_cleaned)
            df_cleaned = df_cleaned.drop_duplicates()
            report["duplicates_removed"] = rows_before - len(df_cleaned)

        if remove_outliers:
            outlier_count = self._remove_outliers(df_cleaned)
            report["outliers_removed"] = outlier_count

        final_shape = df_cleaned.shape
        report["final_rows"] = final_shape[0]
        report["final_columns"] = final_shape[1]

        logger.info(
            f"Cleaned dataset: {original_shape} -> {final_shape}",
            extra={"report": report},
        )

        return df_cleaned, report

    def _remove_outliers(
        self,
        df: pd.DataFrame,
    ) -> int:
        """Remove outliers from dataset.

        Args:
            df: Input DataFrame.

        Returns:
            Number of outliers removed.
        """
        method = self.cleaning_config.get("outlier_detection", {}).get("method", "iqr")
        threshold = self.cleaning_config.get("outlier_detection", {}).get("threshold", 1.5)

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_mask = pd.Series([False] * len(df))

        for col in numeric_cols:
            if method == "iqr":
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
            elif method == "z_score":
                z_scores = np.abs(stats.zscore(df[col].dropna()))
                z_threshold = self.cleaning_config.get("outlier_detection", {}).get("z_score_threshold", 3.0)
                col_outliers = pd.Series([False] * len(df))
                col_outliers[df[col].notna()] = z_scores > z_threshold
            else:
                continue

            outlier_mask = outlier_mask | col_outliers

        outliers_removed = outlier_mask.sum()
        df.drop(df[outlier_mask].index, inplace=True)

        return outliers_removed

    def save_cleaned_dataset(
        self,
        df: pd.DataFrame,
        output_path: str,
    ) -> None:
        """Save cleaned dataset to file.

        Args:
            df: Cleaned DataFrame.
            output_path: Output file path.
        """
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        file_extension = output_path_obj.suffix.lower()

        if file_extension == ".csv":
            df.to_csv(output_path, index=False)
        elif file_extension in [".xlsx", ".xls"]:
            df.to_excel(output_path, index=False)
        elif file_extension == ".json":
            df.to_json(output_path, orient="records", indent=2)
        else:
            df.to_csv(output_path, index=False)

        logger.info(
            f"Saved cleaned dataset: {output_path}",
            extra={"output_path": output_path, "shape": df.shape},
        )
