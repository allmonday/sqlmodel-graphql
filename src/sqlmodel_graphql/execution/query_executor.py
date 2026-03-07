"""Query execution for GraphQL operations."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from graphql import FieldNode, OperationDefinitionNode, parse

from sqlmodel_graphql.execution.argument_builder import ArgumentBuilder
from sqlmodel_graphql.execution.field_tree_builder import FieldTreeBuilder
from sqlmodel_graphql.response_builder import serialize_with_model

if TYPE_CHECKING:
    from sqlmodel import SQLModel


class QueryExecutor:
    """Executes GraphQL queries and mutations."""

    def __init__(
        self,
        query_methods: dict[str, tuple[type[SQLModel], Any]],
        mutation_methods: dict[str, tuple[type[SQLModel], Any]],
    ):
        """Initialize the query executor.

        Args:
            query_methods: Mapping of query names to (entity, method) tuples.
            mutation_methods: Mapping of mutation names to (entity, method) tuples.
        """
        self._query_methods = query_methods
        self._mutation_methods = mutation_methods
        self._argument_builder = ArgumentBuilder()
        self._field_tree_builder = FieldTreeBuilder()

    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        parsed_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query string.
            variables: Optional variables for the query.
            parsed_meta: Parsed QueryMeta from the query.

        Returns:
            Query result dictionary with 'data' and/or 'errors' keys.
        """
        document = parse(query)
        data: dict[str, Any] = {}
        errors: list[dict[str, Any]] = []

        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                op_type = definition.operation.value  # 'query' or 'mutation'

                for selection in definition.selection_set.selections:
                    if isinstance(selection, FieldNode):
                        field_name = selection.name.value

                        try:
                            result = await self._execute_field(
                                op_type, field_name, selection, variables, parsed_meta
                            )
                            if result is not None:
                                data[field_name] = result
                        except Exception as e:
                            errors.append({
                                "message": str(e),
                                "path": [field_name],
                            })

        response: dict[str, Any] = {}
        if data:
            response["data"] = data
        if errors:
            response["errors"] = errors

        return response

    async def _execute_field(
        self,
        op_type: str,
        field_name: str,
        selection: FieldNode,
        variables: dict[str, Any] | None,
        parsed_meta: dict[str, Any] | None,
    ) -> Any:
        """Execute a single GraphQL field.

        Args:
            op_type: Operation type ('query' or 'mutation').
            field_name: Name of the field.
            selection: GraphQL FieldNode.
            variables: GraphQL variables.
            parsed_meta: Parsed QueryMeta.

        Returns:
            Execution result.
        """
        # Get the method for this field
        if op_type == "query":
            method_info = self._query_methods.get(field_name)
        else:
            method_info = self._mutation_methods.get(field_name)

        if method_info is None:
            op_name = op_type.title()
            msg = f"Cannot query field '{field_name}' on type '{op_name}'"
            raise ValueError(msg)

        entity, method = method_info

        # Build arguments
        args = self._argument_builder.build(selection, variables, method, entity)

        # Add query_meta if available (only for queries, not mutations)
        if op_type == "query" and parsed_meta and field_name in parsed_meta:
            args["query_meta"] = parsed_meta[field_name]

        # Execute the method
        result = method(**args)
        if inspect.isawaitable(result):
            result = await result

        # Extract requested fields from selection set
        requested_fields = self._field_tree_builder.build_field_tree(selection)

        # Serialize using dynamic Pydantic model (filters FK fields)
        return serialize_with_model(
            result,
            entity=entity,
            field_tree=requested_fields,
        )
