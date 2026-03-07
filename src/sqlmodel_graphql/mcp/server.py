"""MCP Server for sqlmodel-graphql.

Provides a FastMCP server that exposes GraphQL operations as MCP tools.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel_graphql.handler import GraphQLHandler
from sqlmodel_graphql.mcp.builders.schema_formatter import SchemaFormatter
from sqlmodel_graphql.mcp.tools import (
    register_get_schema_tool,
    register_graphql_mutation_tool,
    register_graphql_query_tool,
)

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP
    from sqlmodel import SQLModel


def create_mcp_server(
    base: type[SQLModel],
    name: str = "SQLModel GraphQL API",
    query_description: str | None = None,
    mutation_description: str | None = None,
) -> FastMCP:
    """Create an MCP server that exposes GraphQL operations as tools.

    This function creates a FastMCP server with three tools:
    - get_schema: Discover available queries, mutations, and types
    - graphql_query: Execute dynamic GraphQL queries
    - graphql_mutation: Execute dynamic GraphQL mutations

    Args:
        base: SQLModel base class. All subclasses with @query/@mutation
              decorators will be automatically discovered.
        name: Name of the MCP server (shown in MCP clients).
        query_description: Optional custom description for Query type.
        mutation_description: Optional custom description for Mutation type.

    Returns:
        A configured FastMCP server instance.

    Example:
        ```python
        from myapp.models import BaseEntity
        from sqlmodel_graphql.mcp import create_mcp_server

        mcp = create_mcp_server(
            base=BaseEntity,
            name="My Blog GraphQL API",
            query_description="查询用户、文章和评论的 API",
            mutation_description="创建和更新数据的 API",
        )

        # Run with stdio transport (default)
        mcp.run()

        # Or run with HTTP transport
        mcp.run(transport="streamable-http")
        ```
    """
    from mcp.server.fastmcp import FastMCP

    # Create the GraphQL handler
    handler = GraphQLHandler(
        base=base,
        query_description=query_description,
        mutation_description=mutation_description,
    )

    # Create the schema formatter
    formatter = SchemaFormatter(handler)

    # Create the FastMCP server
    mcp = FastMCP(name)

    # Register the tools
    register_get_schema_tool(mcp, formatter)
    register_graphql_query_tool(mcp, handler)
    register_graphql_mutation_tool(mcp, handler)

    return mcp
