"""Type utility functions for sqlmodel-graphql."""

from __future__ import annotations

from typing import Any, get_args, get_origin


def get_field_type(entity: type, field_name: str) -> type:
    """Get the type of a field from an entity.

    Args:
        entity: SQLModel entity class.
        field_name: Name of the field.

    Returns:
        Field type or Any if not found.
    """
    if hasattr(entity, "model_fields"):
        field_info = entity.model_fields.get(field_name)
        if field_info and field_info.annotation:
            return field_info.annotation

    # Fallback to annotations
    if hasattr(entity, "__annotations__"):
        return entity.__annotations__.get(field_name, Any)

    return Any


def is_optional_type(annotation: type) -> bool:
    """Check if a type annotation is Optional (Union with None).

    Args:
        annotation: Type annotation to check.

    Returns:
        True if the type is Optional.
    """
    origin = get_origin(annotation)
    if origin is not None:
        args = get_args(annotation)
        return type(None) in args
    return False


def unwrap_optional_type(annotation: type) -> type:
    """Unwrap Optional type to get the inner type.

    Args:
        annotation: Optional type annotation.

    Returns:
        Inner type or original if not Optional.
    """
    origin = get_origin(annotation)
    if origin is not None:
        args = get_args(annotation)
        non_none_args = [a for a in args if a is not type(None)]
        if non_none_args:
            return non_none_args[0]
    return annotation
