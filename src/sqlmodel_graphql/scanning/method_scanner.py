"""Method scanning for GraphQL decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class MethodScanner:
    """Scans entities for @query and @mutation methods."""

    def scan(
        self,
        entities: list[type],
    ) -> tuple[
        dict[str, tuple[type, Callable[..., Any]]],
        dict[str, tuple[type, Callable[..., Any]]],
    ]:
        """Scan all entities for @query and @mutation methods.

        Args:
            entities: List of entity classes to scan.

        Returns:
            Tuple of (query_methods, mutation_methods) where each is a
            mapping of field names to (entity, method) tuples.
        """
        query_methods: dict[str, tuple[type, Callable[..., Any]]] = {}
        mutation_methods: dict[str, tuple[type, Callable[..., Any]]] = {}

        for entity in entities:
            for name in dir(entity):
                try:
                    attr = getattr(entity, name)
                    if not callable(attr):
                        continue

                    # Check for @query decorator
                    if hasattr(attr, "_graphql_query"):
                        func = attr.__func__ if hasattr(attr, "__func__") else attr
                        gql_name = getattr(func, "_graphql_query_name", None)
                        if gql_name is None:
                            gql_name = func.__name__
                        query_methods[gql_name] = (entity, attr)

                    # Check for @mutation decorator
                    if hasattr(attr, "_graphql_mutation"):
                        func = attr.__func__ if hasattr(attr, "__func__") else attr
                        gql_name = getattr(func, "_graphql_mutation_name", None)
                        if gql_name is None:
                            gql_name = func.__name__
                        mutation_methods[gql_name] = (entity, attr)

                except Exception:
                    continue

        return query_methods, mutation_methods
