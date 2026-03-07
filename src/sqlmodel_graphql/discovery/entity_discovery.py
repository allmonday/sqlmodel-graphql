"""Entity discovery module for GraphQL handlers.

This module provides functionality to discover SQLModel entities
that have @query/@mutation decorators, and traverse relationships to find related entities.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from sqlmodel_graphql.response_builder import (
    get_relation_entity,
    get_relationship_names,
)

if TYPE_CHECKING:
    pass


class EntityDiscovery:
    """Discovers SQLModel entities with @query/@mutation decorators.

    Traverses relationships to include related entities even without decorators.
    """

    def __init__(self, base: type):
        """Initialize the entity discovery.

        Args:
            base: The base class to scan for subclasses.
        """
        self._base = base
        self._all_subclasses = set(base.__subclasses__())

    def discover(self) -> list[type]:
        """Discover all entities with decorators and their related entities.

        Returns:
            List of discovered entity classes.
        """
        root_entities = self._find_root_entities()
        return self._traverse_relationships(root_entities)

    def _find_root_entities(self) -> set[type]:
        """Find entities with @query/@mutation decorators.

        Returns:
            Set of entities that have decorators.
        """
        root_entities: set[type] = set()

        for subclass in self._all_subclasses:
            for name in dir(subclass):
                attr = getattr(subclass, name, None)
                if hasattr(attr, "_graphql_query") or hasattr(attr, "_graphql_mutation"):
                    root_entities.add(subclass)
                    break

        return root_entities

    def _traverse_relationships(self, root_entities: set[type]) -> list[type]:
        """Traverse relationships to find all related entities.

        Uses BFS to discover entities connected through relationships.

        Args:
            root_entities: Starting entities with decorators.

        Returns:
            List of all discovered entities (roots + related).
        """
        discovered: set[type] = set()
        queue = deque(root_entities)

        while queue:
            current = queue.popleft()
            if current in discovered:
                continue
            discovered.add(current)

            # Traverse all relationships of current entity
            for rel_name in get_relationship_names(current):
                target_entity = get_relation_entity(
                    current, rel_name, self._all_subclasses
                )
                if target_entity and target_entity not in discovered:
                    if target_entity in self._all_subclasses:
                        queue.append(target_entity)

        return list(discovered)
