"""Generates visualizations from research data."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class VisualizationGenerator:
    """Generates visualizations from research data."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize visualization generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.viz_config = config.get("visualization", {})
        self._setup_style()

    def _setup_style(self) -> None:
        """Setup matplotlib style."""
        style = self.viz_config.get("default_style", "publication")
        plt.style.use(style if style in plt.style.available else "default")

        sns.set_palette(self.viz_config.get("color_palette", "Set2"))

    def scatter_plot(
        self,
        x: pd.Series,
        y: pd.Series,
        title: str = "Scatter Plot",
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """Create scatter plot.

        Args:
            x: X-axis data.
            y: Y-axis data.
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            figsize: Optional figure size.

        Returns:
            Matplotlib Figure object.
        """
        if figsize is None:
            figsize = (
                self.viz_config.get("figure_size", {}).get("width", 8),
                self.viz_config.get("figure_size", {}).get("height", 6),
            )

        fig, ax = plt.subplots(figsize=figsize)
        ax.scatter(x, y, alpha=0.6)
        ax.set_title(title)
        ax.set_xlabel(xlabel or x.name)
        ax.set_ylabel(ylabel or y.name)
        ax.grid(True, alpha=0.3)

        logger.info(f"Created scatter plot: {title}")

        return fig

    def line_plot(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        title: str = "Line Plot",
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """Create line plot.

        Args:
            data: Input DataFrame.
            x: X-axis column name.
            y: Y-axis column name.
            title: Plot title.
            figsize: Optional figure size.

        Returns:
            Matplotlib Figure object.
        """
        if figsize is None:
            figsize = (
                self.viz_config.get("figure_size", {}).get("width", 8),
                self.viz_config.get("figure_size", {}).get("height", 6),
            )

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(data[x], data[y], marker="o")
        ax.set_title(title)
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.grid(True, alpha=0.3)

        logger.info(f"Created line plot: {title}")

        return fig

    def bar_plot(
        self,
        data: pd.Series,
        title: str = "Bar Plot",
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """Create bar plot.

        Args:
            data: Input Series.
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            figsize: Optional figure size.

        Returns:
            Matplotlib Figure object.
        """
        if figsize is None:
            figsize = (
                self.viz_config.get("figure_size", {}).get("width", 8),
                self.viz_config.get("figure_size", {}).get("height", 6),
            )

        fig, ax = plt.subplots(figsize=figsize)
        data.plot(kind="bar", ax=ax)
        ax.set_title(title)
        ax.set_xlabel(xlabel or data.index.name or "")
        ax.set_ylabel(ylabel or data.name or "")
        ax.grid(True, alpha=0.3, axis="y")

        logger.info(f"Created bar plot: {title}")

        return fig

    def histogram(
        self,
        data: pd.Series,
        title: str = "Histogram",
        bins: int = 30,
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """Create histogram.

        Args:
            data: Input Series.
            title: Plot title.
            bins: Number of bins.
            figsize: Optional figure size.

        Returns:
            Matplotlib Figure object.
        """
        if figsize is None:
            figsize = (
                self.viz_config.get("figure_size", {}).get("width", 8),
                self.viz_config.get("figure_size", {}).get("height", 6),
            )

        fig, ax = plt.subplots(figsize=figsize)
        ax.hist(data, bins=bins, edgecolor="black", alpha=0.7)
        ax.set_title(title)
        ax.set_xlabel(data.name or "")
        ax.set_ylabel("Frequency")
        ax.grid(True, alpha=0.3, axis="y")

        logger.info(f"Created histogram: {title}")

        return fig

    def boxplot(
        self,
        data: pd.DataFrame,
        title: str = "Box Plot",
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """Create boxplot.

        Args:
            data: Input DataFrame.
            title: Plot title.
            figsize: Optional figure size.

        Returns:
            Matplotlib Figure object.
        """
        if figsize is None:
            figsize = (
                self.viz_config.get("figure_size", {}).get("width", 8),
                self.viz_config.get("figure_size", {}).get("height", 6),
            )

        fig, ax = plt.subplots(figsize=figsize)
        data.boxplot(ax=ax)
        ax.set_title(title)
        ax.set_ylabel("Value")
        ax.grid(True, alpha=0.3, axis="y")

        logger.info(f"Created boxplot: {title}")

        return fig

    def heatmap(
        self,
        data: pd.DataFrame,
        title: str = "Heatmap",
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """Create heatmap.

        Args:
            data: Input DataFrame.
            title: Plot title.
            figsize: Optional figure size.

        Returns:
            Matplotlib Figure object.
        """
        if figsize is None:
            figsize = (
                self.viz_config.get("figure_size", {}).get("width", 8),
                self.viz_config.get("figure_size", {}).get("height", 6),
            )

        fig, ax = plt.subplots(figsize=figsize)
        sns.heatmap(data, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
        ax.set_title(title)

        logger.info(f"Created heatmap: {title}")

        return fig

    def correlation_matrix(
        self,
        data: pd.DataFrame,
        title: str = "Correlation Matrix",
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """Create correlation matrix visualization.

        Args:
            data: Input DataFrame.
            title: Plot title.
            figsize: Optional figure size.

        Returns:
            Matplotlib Figure object.
        """
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        corr_matrix = data[numeric_cols].corr()

        return self.heatmap(corr_matrix, title=title, figsize=figsize)

    def save_figure(
        self,
        fig: plt.Figure,
        output_path: str,
        formats: Optional[List[str]] = None,
        dpi: Optional[int] = None,
    ) -> List[str]:
        """Save figure to file(s).

        Args:
            fig: Matplotlib Figure object.
            output_path: Output file path.
            formats: Optional list of formats to save.
            dpi: Optional DPI setting.

        Returns:
            List of saved file paths.
        """
        if formats is None:
            formats = self.viz_config.get("figure_formats", ["png"])

        if dpi is None:
            dpi = self.viz_config.get("dpi", 300)

        output_path_obj = Path(output_path)
        saved_paths = []

        for fmt in formats:
            file_path = output_path_obj.with_suffix(f".{fmt}")
            fig.savefig(file_path, dpi=dpi, bbox_inches="tight", format=fmt)
            saved_paths.append(str(file_path))

        logger.info(
            f"Saved figure: {output_path}",
            extra={"formats": formats, "saved_paths": saved_paths},
        )

        return saved_paths
