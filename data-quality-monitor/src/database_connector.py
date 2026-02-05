"""Database connection management for multiple database types."""

import logging
from typing import Optional

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Manages connections to multiple databases."""

    def __init__(self, name: str, connection_string: str, db_type: str = "postgresql"):
        """Initialize database connector.

        Args:
            name: Database identifier.
            connection_string: SQLAlchemy connection string.
            db_type: Database type (postgresql, mysql, sqlite).

        Raises:
            ValueError: If database type is not supported.
        """
        self.name = name
        self.connection_string = connection_string
        self.db_type = db_type.lower()
        self.engine: Optional[Engine] = None

        if self.db_type not in ["postgresql", "mysql", "sqlite"]:
            raise ValueError(f"Unsupported database type: {db_type}")

    def connect(self) -> bool:
        """Establish database connection.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            self.engine = create_engine(
                self.connection_string, pool_pre_ping=True, echo=False
            )
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info(f"Connected to database: {self.name}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to database {self.name}: {e}")
            return False

    def disconnect(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info(f"Disconnected from database: {self.name}")

    def get_tables(self) -> list[str]:
        """Get list of table names in the database.

        Returns:
            List of table names.

        Raises:
            RuntimeError: If not connected to database.
        """
        if not self.engine:
            raise RuntimeError(f"Not connected to database: {self.name}")

        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get tables from {self.name}: {e}")
            return []

    def get_table_columns(self, table_name: str) -> list[dict]:
        """Get column information for a table.

        Args:
            table_name: Name of the table.

        Returns:
            List of dictionaries with column information.

        Raises:
            RuntimeError: If not connected to database.
        """
        if not self.engine:
            raise RuntimeError(f"Not connected to database: {self.name}")

        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            return [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "primary_key": col.get("primary_key", False),
                }
                for col in columns
            ]
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to get columns for table {table_name} from {self.name}: {e}"
            )
            return []

    def get_foreign_keys(self, table_name: str) -> list[dict]:
        """Get foreign key relationships for a table.

        Args:
            table_name: Name of the table.

        Returns:
            List of dictionaries with foreign key information.

        Raises:
            RuntimeError: If not connected to database.
        """
        if not self.engine:
            raise RuntimeError(f"Not connected to database: {self.name}")

        try:
            inspector = inspect(self.engine)
            foreign_keys = inspector.get_foreign_keys(table_name)
            return [
                {
                    "constrained_columns": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"],
                }
                for fk in foreign_keys
            ]
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to get foreign keys for table {table_name} from {self.name}: {e}"
            )
            return []

    def execute_query(self, query: str) -> list[dict]:
        """Execute a SQL query and return results.

        Args:
            query: SQL query string.

        Returns:
            List of dictionaries representing query results.

        Raises:
            RuntimeError: If not connected to database.
            SQLAlchemyError: If query execution fails.
        """
        if not self.engine:
            raise RuntimeError(f"Not connected to database: {self.name}")

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed on {self.name}: {e}")
            raise

    def get_row_count(self, table_name: str) -> int:
        """Get total row count for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Number of rows in the table.

        Raises:
            RuntimeError: If not connected to database.
        """
        if not self.engine:
            raise RuntimeError(f"Not connected to database: {self.name}")

        try:
            query = f'SELECT COUNT(*) as count FROM "{table_name}"'
            if self.db_type == "mysql":
                query = f"SELECT COUNT(*) as count FROM `{table_name}`"
            result = self.execute_query(query)
            return result[0]["count"] if result else 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to get row count for {table_name}: {e}")
            return 0
