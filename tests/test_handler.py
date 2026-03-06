"""Tests for GraphQLHandler."""

from __future__ import annotations

from typing import Optional

import pytest
from sqlmodel import Field, SQLModel

from sqlmodel_graphql import GraphQLHandler, QueryMeta, mutation, query


# Define test base class
class HandlerTestBase(SQLModel):
    """Base class for test entities."""

    pass


class HandlerTestUser(HandlerTestBase, table=False):
    """Test user entity."""

    id: int = Field(primary_key=True)
    name: str
    email: str

    @query(name="test_users")
    async def get_all(
        cls, limit: int = 10, query_meta: Optional[QueryMeta] = None
    ) -> list["HandlerTestUser"]:
        """Get all test users."""
        return [
            HandlerTestUser(id=1, name="Alice", email="alice@example.com"),
            HandlerTestUser(id=2, name="Bob", email="bob@example.com"),
        ][:limit]

    @query(name="test_user")
    async def get_by_id(cls, id: int, query_meta: Optional[QueryMeta] = None) -> Optional["HandlerTestUser"]:
        """Get test user by ID."""
        return HandlerTestUser(id=id, name="Test", email="test@example.com")


class HandlerTestPost(HandlerTestBase, table=False):
    """Test post entity."""

    id: int = Field(primary_key=True)
    title: str
    content: str = ""

    @query(name="test_posts")
    async def get_all(cls, query_meta: Optional[QueryMeta] = None) -> list["HandlerTestPost"]:
        """Get all test posts."""
        return []

    @mutation(name="create_test_post")
    async def create(cls, title: str, content: str) -> "HandlerTestPost":
        """Create a test post."""
        return HandlerTestPost(id=1, title=title, content=content)


class HandlerTestNoDecorators(HandlerTestBase, table=False):
    """Entity without @query or @mutation decorators - should be ignored."""

    id: int = Field(primary_key=True)
    name: str


class TestDiscoverFromBase:
    """Tests for _discover_from_base method."""

    def test_discovers_entities_with_query(self) -> None:
        """Test that entities with @query are discovered."""
        handler = GraphQLHandler(base=HandlerTestBase)

        entity_names = [e.__name__ for e in handler.entities]
        assert "HandlerTestUser" in entity_names
        assert "HandlerTestPost" in entity_names

    def test_discovers_entities_with_mutation(self) -> None:
        """Test that entities with @mutation are discovered."""
        handler = GraphQLHandler(base=HandlerTestBase)

        entity_names = [e.__name__ for e in handler.entities]
        assert "HandlerTestPost" in entity_names  # Has @mutation

    def test_ignores_entities_without_decorators(self) -> None:
        """Test that entities without @query/@mutation are ignored."""
        handler = GraphQLHandler(base=HandlerTestBase)

        entity_names = [e.__name__ for e in handler.entities]
        assert "HandlerTestNoDecorators" not in entity_names


class TestGraphQLHandlerWithBase:
    """Tests for GraphQLHandler with base parameter."""

    @pytest.fixture
    def handler(self) -> GraphQLHandler:
        """Create handler with base parameter."""
        return GraphQLHandler(base=HandlerTestBase)

    def test_handler_creates_sdl_generator(self, handler: GraphQLHandler) -> None:
        """Test that handler creates SDL generator with discovered entities."""
        sdl = handler.get_sdl()

        assert "type HandlerTestUser" in sdl
        assert "type HandlerTestPost" in sdl

    def test_handler_discovers_query_methods(self, handler: GraphQLHandler) -> None:
        """Test that handler discovers query methods."""
        assert "test_users" in handler._query_methods
        assert "test_user" in handler._query_methods
        assert "test_posts" in handler._query_methods

    def test_handler_discovers_mutation_methods(self, handler: GraphQLHandler) -> None:
        """Test that handler discovers mutation methods."""
        assert "create_test_post" in handler._mutation_methods

    @pytest.mark.asyncio
    async def test_execute_query(self, handler: GraphQLHandler) -> None:
        """Test executing a query."""
        result = await handler.execute("{ test_users { id name } }")

        assert "data" in result
        assert "test_users" in result["data"]
        assert len(result["data"]["test_users"]) == 2
        assert result["data"]["test_users"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_execute_mutation(self, handler: GraphQLHandler) -> None:
        """Test executing a mutation."""
        result = await handler.execute(
            'mutation { create_test_post(title: "Hello", content: "World") { id title } }'
        )

        assert "data" in result
        assert "create_test_post" in result["data"]
        assert result["data"]["create_test_post"]["title"] == "Hello"

    @pytest.mark.asyncio
    async def test_introspection_query(self, handler: GraphQLHandler) -> None:
        """Test introspection query."""
        result = await handler.execute("{ __schema { queryType { name } } }")

        assert "data" in result
        assert result["data"]["__schema"]["queryType"]["name"] == "Query"
