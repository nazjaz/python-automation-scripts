"""Research data processor automation system.

Automatically processes research data by cleaning datasets, performing statistical
analysis, generating visualizations, and creating publication-ready figures.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt

from src.config import get_settings, load_config
from src.data_cleaner import DataCleaner
from src.database import DatabaseManager, Dataset
from src.figure_creator import FigureCreator
from src.statistical_analyzer import StatisticalAnalyzer
from src.visualization_generator import VisualizationGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/research_data_processor.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=log_config.get("max_bytes", 10485760),
        backupCount=log_config.get("backup_count", 5),
    )

    formatter = logging.Formatter(log_config.get("format"))
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def clean_data(
    config: dict,
    settings: object,
    input_file: str,
    output_file: Optional[str] = None,
    missing_strategy: Optional[str] = None,
) -> dict:
    """Clean research dataset.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        input_file: Input file path.
        output_file: Optional output file path.
        missing_strategy: Optional missing value strategy.

    Returns:
        Dictionary with cleaning results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    cleaner = DataCleaner(db_manager, config)

    logger.info("Cleaning dataset", extra={"input_file": input_file})

    df = cleaner.load_dataset(input_file)

    if output_file is None:
        output_path = Path(input_file)
        output_file = str(output_path.parent / f"{output_path.stem}_cleaned{output_path.suffix}")

    df_cleaned, report = cleaner.clean_dataset(df, missing_value_strategy=missing_strategy)
    cleaner.save_cleaned_dataset(df_cleaned, output_file)

    dataset = db_manager.add_dataset(
        dataset_id=Path(input_file).stem,
        name=Path(input_file).name,
        file_path=input_file,
        file_type=Path(input_file).suffix,
        row_count=df_cleaned.shape[0],
        column_count=df_cleaned.shape[1],
    )

    dataset.cleaned = True
    session = db_manager.get_session()
    try:
        session.merge(dataset)
        session.commit()
    finally:
        session.close()

    logger.info(
        f"Cleaned dataset: {input_file} -> {output_file}",
        extra={"report": report},
    )

    return {
        "success": True,
        "input_file": input_file,
        "output_file": output_file,
        "report": report,
    }


def analyze_data(
    config: dict,
    settings: object,
    input_file: str,
    analysis_types: Optional[list] = None,
) -> dict:
    """Perform statistical analysis on dataset.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        input_file: Input file path.
        analysis_types: Optional list of analysis types.

    Returns:
        Dictionary with analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    cleaner = DataCleaner(db_manager, config)
    analyzer = StatisticalAnalyzer(db_manager, config)

    logger.info("Analyzing dataset", extra={"input_file": input_file})

    df = cleaner.load_dataset(input_file)

    results = analyzer.perform_analysis(df, analysis_types=analysis_types)

    dataset = (
        db_manager.get_session()
        .query(Dataset)
        .filter(Dataset.file_path == input_file)
        .first()
    )

    if not dataset:
        dataset = db_manager.add_dataset(
            dataset_id=Path(input_file).stem,
            name=Path(input_file).name,
            file_path=input_file,
        )

    import json
    for analysis_type, analysis_result in results.items():
        db_manager.add_analysis(
            dataset_id=dataset.id,
            analysis_type=analysis_type,
            results=json.dumps(analysis_result),
        )

    logger.info(
        f"Analyzed dataset: {input_file}",
        extra={"analysis_types": list(results.keys())},
    )

    return {
        "success": True,
        "results": results,
    }


def generate_visualization(
    config: dict,
    settings: object,
    input_file: str,
    figure_type: str,
    x: Optional[str] = None,
    y: Optional[str] = None,
    output_file: Optional[str] = None,
) -> dict:
    """Generate visualization.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        input_file: Input file path.
        figure_type: Type of figure to create.
        x: Optional X-axis column name.
        y: Optional Y-axis column name.
        output_file: Optional output file path.

    Returns:
        Dictionary with visualization results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    cleaner = DataCleaner(db_manager, config)
    viz_generator = VisualizationGenerator(db_manager, config)

    logger.info("Generating visualization", extra={"input_file": input_file, "figure_type": figure_type})

    df = cleaner.load_dataset(input_file)

    if output_file is None:
        output_file = f"output/{Path(input_file).stem}_{figure_type}.png"

    if figure_type == "scatter" and x and y:
        fig = viz_generator.scatter_plot(df[x], df[y], title=f"{x} vs {y}")
    elif figure_type == "line" and x and y:
        fig = viz_generator.line_plot(df, x, y, title=f"{y} over {x}")
    elif figure_type == "bar" and y:
        fig = viz_generator.bar_plot(df[y], title=f"Bar Plot: {y}")
    elif figure_type == "histogram" and y:
        fig = viz_generator.histogram(df[y], title=f"Histogram: {y}")
    elif figure_type == "boxplot":
        fig = viz_generator.boxplot(df, title="Box Plot")
    elif figure_type == "correlation":
        fig = viz_generator.correlation_matrix(df, title="Correlation Matrix")
    else:
        raise ValueError(f"Unsupported figure type: {figure_type} or missing required columns")

    saved_paths = viz_generator.save_figure(fig, output_file)
    plt.close(fig)

    logger.info(
        f"Generated visualization: {output_file}",
        extra={"saved_paths": saved_paths},
    )

    return {
        "success": True,
        "output_file": output_file,
        "saved_paths": saved_paths,
    }


def create_publication_figure(
    config: dict,
    settings: object,
    input_file: str,
    figure_type: str,
    x: Optional[str] = None,
    y: Optional[str] = None,
    size: str = "single_column",
    output_file: Optional[str] = None,
) -> dict:
    """Create publication-ready figure.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        input_file: Input file path.
        figure_type: Type of figure to create.
        x: Optional X-axis column name.
        y: Optional Y-axis column name.
        size: Figure size preset.
        output_file: Optional output file path.

    Returns:
        Dictionary with figure creation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    cleaner = DataCleaner(db_manager, config)
    figure_creator = FigureCreator(db_manager, config)

    logger.info("Creating publication figure", extra={"input_file": input_file, "figure_type": figure_type})

    df = cleaner.load_dataset(input_file)

    if output_file is None:
        output_file = f"figures/{Path(input_file).stem}_{figure_type}_pub.png"

    fig = figure_creator.create_publication_figure(
        figure_type=figure_type,
        data=df,
        x=x,
        y=y,
        size=size,
    )

    saved_paths = figure_creator.save_publication_figure(fig, output_file)

    dataset = (
        db_manager.get_session()
        .query(Dataset)
        .filter(Dataset.file_path == input_file)
        .first()
    )

    if not dataset:
        dataset = db_manager.add_dataset(
            dataset_id=Path(input_file).stem,
            name=Path(input_file).name,
            file_path=input_file,
        )

    from datetime import datetime
    figure_id = f"{Path(input_file).stem}_{figure_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    db_manager.add_figure(
        dataset_id=dataset.id,
        figure_id=figure_id,
        figure_type=figure_type,
        file_path=output_file,
        file_format=Path(output_file).suffix[1:],
        publication_ready=True,
        dpi=config.get("publication", {}).get("dpi", 300),
    )

    logger.info(
        f"Created publication figure: {output_file}",
        extra={"saved_paths": saved_paths},
    )

    return {
        "success": True,
        "output_file": output_file,
        "saved_paths": saved_paths,
    }


def main() -> None:
    """Main entry point for research data processor automation."""
    parser = argparse.ArgumentParser(
        description="Research data processor automation system"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean dataset",
    )
    parser.add_argument(
        "--input", required=True, help="Input file path"
    )
    parser.add_argument(
        "--output", help="Output file path"
    )
    parser.add_argument(
        "--missing-strategy",
        choices=["drop", "mean", "median", "mode", "forward_fill", "backward_fill"],
        help="Missing value handling strategy",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Perform statistical analysis",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate visualization",
    )
    parser.add_argument(
        "--figure-type",
        choices=["scatter", "line", "bar", "histogram", "boxplot", "correlation", "heatmap"],
        help="Type of figure to create",
    )
    parser.add_argument(
        "--x", help="X-axis column name"
    )
    parser.add_argument(
        "--y", help="Y-axis column name"
    )
    parser.add_argument(
        "--publication",
        action="store_true",
        help="Create publication-ready figure",
    )
    parser.add_argument(
        "--size",
        choices=["single_column", "double_column", "full_page"],
        default="single_column",
        help="Figure size preset (default: single_column)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([args.clean, args.analyze, args.visualize, args.publication]):
        parser.print_help()
        sys.exit(1)

    try:
        config = load_config(args.config) if args.config else load_config()
        settings = get_settings()
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.get("logging", {}))

    logger = logging.getLogger(__name__)

    try:
        db_manager = DatabaseManager(settings.database.url)
        db_manager.create_tables()

        if args.clean:
            result = clean_data(
                config=config,
                settings=settings,
                input_file=args.input,
                output_file=args.output,
                missing_strategy=args.missing_strategy,
            )

            print(f"\nData Cleaning:")
            print(f"Input: {result['input_file']}")
            print(f"Output: {result['output_file']}")
            print(f"Rows removed: {result['report']['missing_values_removed'] + result['report']['duplicates_removed']}")

        elif args.analyze:
            result = analyze_data(
                config=config,
                settings=settings,
                input_file=args.input,
            )

            print(f"\nStatistical Analysis:")
            for analysis_type, analysis_result in result["results"].items():
                print(f"  {analysis_type}: Completed")

        elif args.visualize:
            if not args.figure_type:
                print("Error: --figure-type is required for --visualize", file=sys.stderr)
                sys.exit(1)

            result = generate_visualization(
                config=config,
                settings=settings,
                input_file=args.input,
                figure_type=args.figure_type,
                x=args.x,
                y=args.y,
                output_file=args.output,
            )

            print(f"\nVisualization Generated:")
            print(f"Output: {result['output_file']}")

        elif args.publication:
            if not args.figure_type:
                print("Error: --figure-type is required for --publication", file=sys.stderr)
                sys.exit(1)

            result = create_publication_figure(
                config=config,
                settings=settings,
                input_file=args.input,
                figure_type=args.figure_type,
                x=args.x,
                y=args.y,
                size=args.size,
                output_file=args.output,
            )

            print(f"\nPublication Figure Created:")
            print(f"Output: {result['output_file']}")
            print(f"Formats: {', '.join([Path(p).suffix for p in result['saved_paths']])}")

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
