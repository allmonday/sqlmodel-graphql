"""Argument building for GraphQL field arguments."""

from __future__ import annotations

import inspect
from typing import Any


class ArgumentBuilder:
    """Builds method arguments from GraphQL field arguments."""

    def _extract_value(self, node: Any) -> Any:
        """Extract Python value from a GraphQL AST value node.

        Args:
            node: A GraphQL ValueNode (StringValueNode, IntValueNode,
                  ListValueNode, ObjectValueNode, etc.)

        Returns:
            The corresponding Python value.
        """
        # Handle list values (ListValueNode)
        if hasattr(node, "values") and node.__class__.__name__ == "ListValueNode":
            return [self._extract_value(v) for v in node.values]

        # Handle object values (ObjectValueNode)
        if hasattr(node, "fields") and node.__class__.__name__ == "ObjectValueNode":
            return {field.name.value: self._extract_value(field.value) for field in node.fields}

        # Handle variable references (VariableNode)
        if hasattr(node, "name") and node.__class__.__name__ == "VariableNode":
            # Variable reference - caller should resolve using variables dict
            return node  # Return the node itself, will be resolved later

        # Handle null value (NullValueNode)
        if node.__class__.__name__ == "NullValueNode":
            return None

        # Handle enum value (EnumValueNode)
        if hasattr(node, "value") and node.__class__.__name__ == "EnumValueNode":
            return node.value

        # Handle simple scalar values (String, Int, Float, Boolean)
        if hasattr(node, "value"):
            return node.value

        # Fallback - return the node itself
        return node

    def build_arguments(
        self,
        selection: Any,
        variables: dict[str, Any] | None,
        method: Any,
        entity: type,
    ) -> dict[str, Any]:
        """Build method arguments from GraphQL field arguments.

        Args:
            selection: GraphQL FieldNode with argument info.
            variables: GraphQL variables dict.
            method: The method to call.
            entity: The SQLModel entity class.

        Returns:
            Dictionary of argument name to value.
        """
        args: dict[str, Any] = {}
        variables = variables or {}

        if not selection.arguments:
            return args

        # Get method signature for type info
        func = method.__func__ if hasattr(method, "__func__") else method
        sig = inspect.signature(func)

        for arg in selection.arguments:
            arg_name = arg.name.value

            # Extract the value using helper method
            value = self._extract_value(arg.value)

            # Handle variable references
            if value.__class__.__name__ == "VariableNode":
                var_name = value.name.value
                value = variables.get(var_name)

            # Use argument name directly
            param_name = arg_name

            # Check if this param exists in the method signature
            if param_name in sig.parameters:
                args[param_name] = value
            elif arg_name in sig.parameters:
                args[arg_name] = value

        return args
