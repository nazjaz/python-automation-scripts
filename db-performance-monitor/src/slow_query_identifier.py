"""Identify slow queries."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib

from src.database import DatabaseManager


class SlowQueryIdentifier:
    """Identify slow queries."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize slow query identifier.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.slow_query_threshold_ms = config.get("slow_query_threshold_ms", 1000.0)

    def identify_slow_queries(
        self,
        database_id: str,
        queries: List[Dict[str, any]],
    ) -> Dict[str, any]:
        """Identify slow queries from query list.

        Args:
            database_id: Database identifier.
            queries: List of query dictionaries with text and execution_time_ms.

        Returns:
            Dictionary with identification results.
        """
        database = self.db_manager.get_database(database_id)

        if not database:
            return {"error": "Database not found"}

        slow_queries = []
        processed_queries = []

        for query_data in queries:
            query_text = query_data.get("query_text", "")
            execution_time_ms = query_data.get("execution_time_ms", 0.0)

            query_id = self._generate_query_id(query_text)

            is_slow = execution_time_ms >= self.slow_query_threshold_ms

            query = self.db_manager.add_query(
                query_id=query_id,
                database_id=database.id,
                query_text=query_text,
                execution_time_ms=execution_time_ms,
                slow_query_threshold_ms=self.slow_query_threshold_ms,
                table_name=query_data.get("table_name"),
                query_type=query_data.get("query_type"),
            )

            processed_queries.append(query.id)

            if is_slow:
                slow_queries.append({
                    "query_id": query.query_id,
                    "query_text": query.query_text[:200],
                    "execution_time_ms": query.execution_time_ms,
                    "table_name": query.table_name,
                    "query_type": query.query_type,
                })

        return {
            "success": True,
            "database_id": database_id,
            "total_queries": len(processed_queries),
            "slow_queries_count": len(slow_queries),
            "slow_queries": slow_queries,
        }

    def _generate_query_id(self, query_text: str) -> str:
        """Generate query ID from query text.

        Args:
            query_text: Query text.

        Returns:
            Query identifier (hash).
        """
        normalized = query_text.strip().lower()
        return hashlib.md5(normalized.encode()).hexdigest()

    def get_slow_queries(
        self, database_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, any]]:
        """Get slow queries.

        Args:
            database_id: Optional database ID to filter by.
            limit: Maximum number of queries to return.

        Returns:
            List of slow query dictionaries.
        """
        db_id_int = None
        if database_id:
            database = self.db_manager.get_database(database_id)
            if database:
                db_id_int = database.id

        slow_queries = self.db_manager.get_slow_queries(
            database_id=db_id_int, limit=limit
        )

        return [
            {
                "query_id": q.query_id,
                "query_text": q.query_text[:200],
                "execution_time_ms": q.execution_time_ms,
                "average_execution_time_ms": q.average_execution_time_ms,
                "execution_count": q.execution_count,
                "table_name": q.table_name,
                "query_type": q.query_type,
                "first_seen_at": q.first_seen_at,
                "last_seen_at": q.last_seen_at,
            }
            for q in slow_queries
        ]

    def get_slow_query_statistics(
        self, database_id: Optional[str] = None, days: int = 7
    ) -> Dict[str, any]:
        """Get slow query statistics.

        Args:
            database_id: Optional database identifier.
            days: Number of days to analyze.

        Returns:
            Dictionary with slow query statistics.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Query

            cutoff = datetime.utcnow() - timedelta(days=days)

            query = session.query(Query).filter(Query.is_slow == "true")

            if database_id:
                database = self.db_manager.get_database(database_id)
                if database:
                    query = query.filter(Query.database_id == database.id)

            slow_queries = query.filter(Query.last_seen_at >= cutoff).all()

            if not slow_queries:
                return {
                    "days": days,
                    "total_slow_queries": 0,
                    "average_execution_time_ms": 0.0,
                }

            total_execution_time = sum(q.execution_time_ms for q in slow_queries)
            average_execution_time = total_execution_time / len(slow_queries)

            query_types = {}
            for q in slow_queries:
                query_type = q.query_type or "unknown"
                query_types[query_type] = query_types.get(query_type, 0) + 1

            return {
                "days": days,
                "total_slow_queries": len(slow_queries),
                "average_execution_time_ms": average_execution_time,
                "by_query_type": query_types,
            }
        finally:
            session.close()
