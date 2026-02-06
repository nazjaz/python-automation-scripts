"""Recommend query optimizations."""

from typing import Dict, List, Optional
import re

from src.database import DatabaseManager


class OptimizationRecommender:
    """Recommend query optimizations."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize optimization recommender.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def recommend_optimizations(
        self, database_id: str, query_id: Optional[str] = None
    ) -> Dict[str, any]:
        """Recommend optimizations for queries.

        Args:
            database_id: Database identifier.
            query_id: Optional query ID to optimize specific query.

        Returns:
            Dictionary with optimization recommendations.
        """
        database = self.db_manager.get_database(database_id)

        if not database:
            return {"error": "Database not found"}

        if query_id:
            query = self.db_manager.get_query(query_id)
            queries = [query] if query else []
        else:
            queries = self.db_manager.get_slow_queries(database_id=database.id, limit=50)

        if not queries:
            return {"error": "No queries found"}

        optimizations_created = []

        for query in queries:
            query_optimizations = self._analyze_query(query)

            for opt_data in query_optimizations:
                optimization_id = f"OPT-{query.query_id}-{len(optimizations_created) + 1}"

                optimization = self.db_manager.add_optimization(
                    optimization_id=optimization_id,
                    database_id=database.id,
                    query_id=query.id,
                    optimization_type=opt_data["type"],
                    optimization_description=opt_data["description"],
                    priority=opt_data["priority"],
                    estimated_improvement_percent=opt_data.get("improvement_percent"),
                )

                if opt_data.get("index_suggestion"):
                    self.db_manager.add_index_suggestion(
                        optimization_id=optimization.id,
                        table_name=opt_data["index_suggestion"]["table_name"],
                        column_names=opt_data["index_suggestion"]["column_names"],
                        index_type=opt_data["index_suggestion"].get("index_type"),
                        index_name=opt_data["index_suggestion"].get("index_name"),
                        estimated_improvement_percent=opt_data["index_suggestion"].get(
                            "improvement_percent"
                        ),
                    )

                optimizations_created.append({
                    "optimization_id": optimization_id,
                    "type": opt_data["type"],
                    "priority": opt_data["priority"],
                })

        return {
            "success": True,
            "database_id": database_id,
            "optimizations_created": len(optimizations_created),
            "optimizations": optimizations_created,
        }

    def _analyze_query(self, query) -> List[Dict[str, any]]:
        """Analyze query and generate optimization recommendations.

        Args:
            query: Query object.

        Returns:
            List of optimization dictionaries.
        """
        optimizations = []
        query_text = query.query_text.lower()

        if query.execution_time_ms >= 5000:
            priority = "urgent"
        elif query.execution_time_ms >= 2000:
            priority = "high"
        elif query.execution_time_ms >= 1000:
            priority = "medium"
        else:
            priority = "low"

        if "select" in query_text:
            optimizations.extend(self._analyze_select_query(query, query_text, priority))

        if "join" in query_text:
            optimizations.extend(self._analyze_join_query(query, query_text, priority))

        if "where" in query_text:
            optimizations.extend(self._analyze_where_clause(query, query_text, priority))

        if "order by" in query_text:
            optimizations.extend(self._analyze_order_by(query, query_text, priority))

        return optimizations

    def _analyze_select_query(
        self, query, query_text: str, priority: str
    ) -> List[Dict[str, any]]:
        """Analyze SELECT query.

        Args:
            query: Query object.
            query_text: Query text (lowercase).
            priority: Base priority.

        Returns:
            List of optimization dictionaries.
        """
        optimizations = []

        if "select *" in query_text:
            optimizations.append({
                "type": "query_rewrite",
                "description": "Avoid SELECT * - specify only needed columns",
                "priority": priority,
                "improvement_percent": 10.0,
            })

        return optimizations

    def _analyze_join_query(
        self, query, query_text: str, priority: str
    ) -> List[Dict[str, any]]:
        """Analyze JOIN query.

        Args:
            query: Query object.
            query_text: Query text (lowercase).
            priority: Base priority.

        Returns:
            List of optimization dictionaries.
        """
        optimizations = []

        join_pattern = r"join\s+(\w+)\s+on\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)"
        matches = re.findall(join_pattern, query_text)

        for match in matches:
            table_name = match[0]
            left_table = match[1]
            left_column = match[2]
            right_table = match[3]
            right_column = match[4]

            optimizations.append({
                "type": "index",
                "description": f"Add index on {table_name}.{right_column} for JOIN optimization",
                "priority": priority,
                "improvement_percent": 30.0,
                "index_suggestion": {
                    "table_name": table_name,
                    "column_names": right_column,
                    "index_type": "btree",
                    "index_name": f"idx_{table_name}_{right_column}",
                    "improvement_percent": 30.0,
                },
            })

        return optimizations

    def _analyze_where_clause(
        self, query, query_text: str, priority: str
    ) -> List[Dict[str, any]]:
        """Analyze WHERE clause.

        Args:
            query: Query object.
            query_text: Query text (lowercase).
            priority: Base priority.

        Returns:
            List of optimization dictionaries.
        """
        optimizations = []

        where_pattern = r"where\s+(\w+)\.(\w+)\s*="
        matches = re.findall(where_pattern, query_text)

        for match in matches:
            table_name = match[0]
            column_name = match[1]

            if query.table_name and table_name == query.table_name.lower():
                optimizations.append({
                    "type": "index",
                    "description": f"Add index on {table_name}.{column_name} for WHERE clause",
                    "priority": priority,
                    "improvement_percent": 40.0,
                    "index_suggestion": {
                        "table_name": table_name,
                        "column_names": column_name,
                        "index_type": "btree",
                        "index_name": f"idx_{table_name}_{column_name}",
                        "improvement_percent": 40.0,
                    },
                })

        return optimizations

    def _analyze_order_by(
        self, query, query_text: str, priority: str
    ) -> List[Dict[str, any]]:
        """Analyze ORDER BY clause.

        Args:
            query: Query object.
            query_text: Query text (lowercase).
            priority: Base priority.

        Returns:
            List of optimization dictionaries.
        """
        optimizations = []

        order_by_pattern = r"order\s+by\s+(\w+)\.(\w+)"
        matches = re.findall(order_by_pattern, query_text)

        for match in matches:
            table_name = match[0]
            column_name = match[1]

            if query.table_name and table_name == query.table_name.lower():
                optimizations.append({
                    "type": "index",
                    "description": f"Add index on {table_name}.{column_name} for ORDER BY",
                    "priority": priority,
                    "improvement_percent": 25.0,
                    "index_suggestion": {
                        "table_name": table_name,
                        "column_names": column_name,
                        "index_type": "btree",
                        "index_name": f"idx_{table_name}_{column_name}_order",
                        "improvement_percent": 25.0,
                    },
                })

        return optimizations

    def get_optimizations(
        self, database_id: Optional[str] = None, status: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, any]]:
        """Get optimizations.

        Args:
            database_id: Optional database identifier.
            status: Optional status to filter by.
            limit: Maximum number of optimizations to return.

        Returns:
            List of optimization dictionaries.
        """
        db_id_int = None
        if database_id:
            database = self.db_manager.get_database(database_id)
            if database:
                db_id_int = database.id

        optimizations = self.db_manager.get_optimizations(
            database_id=db_id_int, status=status, limit=limit
        )

        result = []
        for opt in optimizations:
            index_suggestions = self.db_manager.get_index_suggestions(optimization_id=opt.id)

            result.append({
                "optimization_id": opt.optimization_id,
                "type": opt.optimization_type,
                "description": opt.optimization_description,
                "priority": opt.priority,
                "status": opt.status,
                "estimated_improvement_percent": opt.estimated_improvement_percent,
                "index_suggestions": [
                    {
                        "table_name": s.table_name,
                        "column_names": s.column_names,
                        "index_type": s.index_type,
                        "index_name": s.index_name,
                        "estimated_improvement_percent": s.estimated_improvement_percent,
                    }
                    for s in index_suggestions
                ],
            })

        return result
