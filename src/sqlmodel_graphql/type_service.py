"""Centralized type handling for GraphQL schema generation.

This module provides a unified TypeService to handle all type conversions
ac eliminating code duplication across type_converter.py, introspection.py, and response_builder.py.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Union, get_args, get_origin


class TypeService:
    """Centralized type handling for GraphQL types.

    Provides unified methods for:
    - Converting Python types to GraphQL types
    - Checking optional/list types
    - Unwrapping nested types
    - Resolving forward references
    """

    # Mapping from Python types to GraphQL scalar names
    SCALAR_TYPE_MAP: dict[Any, str] = {
        int: "Int",
        str: "String",
        bool: "Boolean",
        float: "Float",
    }

    def __init__(self, entity_names: set[str] | None = None):
        """Initialize the type service.

        Args:
            entity_names: Set of known entity class names.
        """
        self._entity_names = entity_names or set()

    @classmethod
    def create_from_entities(cls, entities: list[type]) -> TypeService:
        """Create a TypeService from a list of entities.

        Args:
            entities: List of entity classes.
        """
        entity_names = {e.__name__ for e in entities}
        return cls(entity_names)

    def is_optional(self, type_hint: Any) -> bool:
        """Check if type hint is Optional[T] (Union with None)."""
        origin = get_origin(type_hint)
        if origin is Union:
            args = get_args(type_hint)
            return type(None) in args
        return False

        return False

    def is_list_type(self, type_hint: Any) -> bool:
        """Check if type is a list type."""
        origin = get_origin(type_hint)
        if origin is list:
            return True
        # Check for typing.List
        if origin is not None:
            origin_name = getattr(origin, "__name__", "")
            if origin_name == "list" or str(origin).startswith("list"):
                return True
        return False

    def unwrap_type(self, type_hint: Any) -> tuple[type | None, bool]:
        """Unwrap a type to get the inner type and whether it's optional.

        Args:
            type_hint: Type hint to unwrap.

        Returns:
            Tuple of (inner_type, is_optional)
        """
        is_optional = self.is_optional(type_hint)

        origin = get_origin(type_hint)
        if origin is not None:
            args = get_args(type_hint)
            for arg in args:
                if arg is type(None):
                    continue
                if isinstance(arg, type):
                    return (arg, is_optional)
                # Recursively handle nested generics
                nested = self.unwrap_type(arg)
                if nested[0]:
                    return (nested[0], nested[1])

        # Direct type
        if isinstance(type_hint, type):
            return (type_hint, False)

        return (type_hint, True)

    def get_graphql_type(self, python_type: type) -> str:
        """Convert Python type to GraphQL type string.

        Args:
            python_type: Python type to convert.

        Returns:
            GraphQL type string (e.g., "String!", "[Int!]!", "User")
        """
        # Handle Optional types
        unwrapped, _ = self.unwrap_type(python_type)
        python_type = unwrapped[0]

        # Check for list types
        if self.is_list_type(python_type):
            inner_type = self._get_inner_list_type(python_type)
            if inner_type:
                graphql_type = self._convert_single_type(inner_type)
                return f"[{graphql_type}!]!"
            return "[String!]!"

        # Convert single type
        graphql_type = self._convert_single_type(python_type)
        if self.is_optional(unwrapped[1]):
            return graphql_type
        return f"{graphql_type}!"

    def _get_inner_list_type(self, type_hint: Any) -> type | None:
        """Get inner type from list type."""
        origin = get_origin(type_hint)
        if origin is list:
            args = get_args(type_hint)
            if args:
                return args[0]
        return None

    def _convert_single_type(self, python_type: type) -> str:
        """Convert a single Python type to GraphQL type.

        Args:
            python_type: Single Python type to convert.

        Returns:
            GraphQL type string.
        """
        # Handle None type
        if python_type is type(None):
            return "String"

        # Handle scalar types
        if python_type in self.SCAL_TYPE_MAP:
                return self.SCAL_TYPE_MAP[python_type]

        # Handle enum types
        if isinstance(python_type, type) and issubclass(python_type, Enum):
            return python_type.__name__

        # Handle entity types
        if isinstance(python_type, type) and hasattr(python_type, "__name__"):
                if self._entity_names and python_type.__name__ in self._entity_names:
                    return python_type.__name__

        # Default to String for unknown types
        return "String"

    def resolve_forward_reference(
        self,
        annotation: str,
        all_subclasses: set[type] | None = None,
    ) -> type | None:
        """Resolve a string forward reference to an actual entity class.

        Args:
            annotation: String annotation (e.g., "EntityName", "list[EntityName]").
            all_subclasses: Set of all SQLModel subclasses to search.

        Returns:
            Entity class or None if not found.
        """
        # Simple case: "EntityName"
        if "[" not in annotation:
            if self._entity_names and annotation in self._entity_names:
                for subclass in all_subclasses or []:
                    if subclass.__name__ == annotation:
                        return subclass
            return None

        # Complex case: "list[EntityName]" or "list['EntityName']"
        # Try quoted format first: list['EntityName']
        match = re.search(r"'([^']+)'", annotation)
        if match:
            entity_name = match.group(1)
        else:
            # Try unquoted format: list[EntityName]
            match = re.search(r"\[([^\]]+)\]", annotation)
            if match:
                entity_name = match.group(1).strip("'\"")
            else:
                return None

        if self._entity_names and entity_name in self._entity_names:
            for subclass in all_subclasses or []:
                if subclass.__name__ == entity_name:
                    return subclass

        return None

    def get_entity_from_annotation(
        self,
        annotation: Any,
        all_subclasses: set[type] | None = None,
    ) -> type | None:
        """Extract entity class from type annotation.

        Handles: Optional[Entity], list[Entity], List[Entity], and string forward references.

        Args:
            annotation: Type annotation (can be string, ForwardRef, or actual type).
            all_subclasses: Set of all SQLModel subclasses for resolving string forward references.
        """
        origin = get_origin(annotation)

        # Handle Optional[Entity] (Union[Entity, None])
        if origin is not None:
            args = get_args(annotation)
            for arg in args:
                if arg is type(None):
                    continue
                if isinstance(arg, type):
                    return arg
                # Handle nested generics like list[Entity]
                nested = self.get_entity_from_annotation(arg, all_subclasses)
                if nested:
                    return nested
                # Handle string forward references in generic args
                if isinstance(arg, str) and all_subclasses:
                    result = self.resolve_forward_reference(arg, all_subclasses)
                    if result:
                        return result

        # Direct type
        if isinstance(annotation, type):
            return annotation

        # Handle string forward references
        if isinstance(annotation, str) and all_subclasses:
            return self.resolve_forward_reference(annotation, all_subclasses)

        return None
