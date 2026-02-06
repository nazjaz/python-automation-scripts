"""Creates publication-ready figures."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.database import DatabaseManager
from src.visualization_generator import VisualizationGenerator

logger = logging.getLogger(__name__)


class FigureCreator:
    """Creates publication-ready figures."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize figure creator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.pub_config = config.get("publication", {})
        self.viz_generator = VisualizationGenerator(db_manager, config)
        self._setup_publication_style()

    def _setup_publication_style(self) -> None:
        """Setup publication-ready matplotlib style."""
        font_settings = self.pub_config.get("font_settings", {})
        plt.rcParams["font.family"] = font_settings.get("family", "Arial")
        plt.rcParams["font.size"] = font_settings.get("size", 10)
        plt.rcParams["font.weight"] = font_settings.get("weight", "normal")

        axis_settings = self.pub_config.get("axis_settings", {})
        plt.rcParams["axes.linewidth"] = axis_settings.get("linewidth", 1.0)
        plt.rcParams["xtick.major.width"] = axis_settings.get("tick_width", 0.5)
        plt.rcParams["ytick.major.width"] = axis_settings.get("tick_width", 0.5)
        plt.rcParams["xtick.major.size"] = axis_settings.get("tick_length", 4)
        plt.rcParams["ytick.major.size"] = axis_settings.get("tick_length", 4)

        legend_settings = self.pub_config.get("legend_settings", {})
        plt.rcParams["legend.frameon"] = legend_settings.get("frameon", True)
        plt.rcParams["legend.fancybox"] = legend_settings.get("fancybox", False)
        plt.rcParams["legend.shadow"] = legend_settings.get("shadow", False)
        plt.rcParams["legend.framealpha"] = legend_settings.get("framealpha", 1.0)

    def create_publication_figure(
        self,
        figure_type: str,
        data: pd.DataFrame,
        x: Optional[str] = None,
        y: Optional[str] = None,
        title: Optional[str] = None,
        size: str = "single_column",
        **kwargs,
    ) -> plt.Figure:
        """Create publication-ready figure.

        Args:
            figure_type: Type of figure to create.
            data: Input DataFrame.
            x: Optional X-axis column name.
            y: Optional Y-axis column name.
            title: Optional figure title.
            size: Figure size preset (single_column, double_column, full_page).
            **kwargs: Additional arguments for figure creation.

        Returns:
            Matplotlib Figure object.
        """
        size_config = self.pub_config.get("figure_size", {})
        figsize = tuple(size_config.get(size, size_config.get("single_column", [3.5, 2.5])))

        if figure_type == "scatter" and x and y:
            fig = self.viz_generator.scatter_plot(
                data[x], data[y], title=title or f"{x} vs {y}", figsize=figsize
            )
        elif figure_type == "line" and x and y:
            fig = self.viz_generator.line_plot(data, x, y, title=title or f"{y} over {x}", figsize=figsize)
        elif figure_type == "bar" and y:
            fig = self.viz_generator.bar_plot(
                data[y] if isinstance(data, pd.DataFrame) else data,
                title=title or f"Bar Plot: {y}",
                figsize=figsize,
            )
        elif figure_type == "histogram" and y:
            fig = self.viz_generator.histogram(
                data[y] if isinstance(data, pd.DataFrame) else data,
                title=title or f"Histogram: {y}",
                figsize=figsize,
            )
        elif figure_type == "boxplot":
            fig = self.viz_generator.boxplot(data, title=title or "Box Plot", figsize=figsize)
        elif figure_type == "heatmap":
            fig = self.viz_generator.heatmap(data, title=title or "Heatmap", figsize=figsize)
        elif figure_type == "correlation":
            fig = self.viz_generator.correlation_matrix(data, title=title or "Correlation Matrix", figsize=figsize)
        else:
            raise ValueError(f"Unsupported figure type: {figure_type}")

        fig.tight_layout()

        logger.info(
            f"Created publication-ready figure: {figure_type}",
            extra={"figure_type": figure_type, "size": size},
        )

        return fig

    def save_publication_figure(
        self,
        fig: plt.Figure,
        output_path: str,
        formats: Optional[List[str]] = None,
        dpi: Optional[int] = None,
    ) -> List[str]:
        """Save publication-ready figure.

        Args:
            fig: Matplotlib Figure object.
            output_path: Output file path.
            formats: Optional list of formats to save.
            dpi: Optional DPI setting.

        Returns:
            List of saved file paths.
        """
        if formats is None:
            formats = self.pub_config.get("formats", ["png", "pdf"])

        if dpi is None:
            dpi = self.pub_config.get("dpi", 300)

        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        saved_paths = []

        for fmt in formats:
            file_path = output_path_obj.with_suffix(f".{fmt}")
            fig.savefig(
                file_path,
                dpi=dpi,
                bbox_inches="tight",
                format=fmt,
                facecolor="white",
                edgecolor="none",
            )
            saved_paths.append(str(file_path))

        plt.close(fig)

        logger.info(
            f"Saved publication figure: {output_path}",
            extra={"formats": formats, "saved_paths": saved_paths},
        )

        return saved_paths
