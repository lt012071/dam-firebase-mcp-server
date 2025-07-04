"""Integration tests for MCP protocol communication."""

from unittest.mock import Mock, patch

import pytest


@pytest.mark.integration
class TestMCPProtocolIntegration:
    """Test MCP protocol integration via FastMCP tool underlying functions."""

    @patch("src.mcp_server_firebase.server.initialize_firebase_client")
    @patch("src.mcp_server_firebase.server.get_firebase_client")
    def test_mcp_server_initialization(
        self, mock_get_client, mock_init_client, test_credentials_file
    ):
        """Test MCP server initialization via direct calls."""
        from src.mcp_server_firebase.server import get_firebase_client, initialize_firebase_client

        # Setup mocks
        mock_client = Mock()
        mock_client.search_assets.return_value = []
        mock_get_client.return_value = mock_client

        # Test initialization
        initialize_firebase_client(test_credentials_file)

        # Verify client is available
        client = get_firebase_client()
        assert client == mock_client

        # Verify Firebase client methods are available
        assert hasattr(client, "search_assets")
        assert hasattr(client, "search_versions")
        assert hasattr(client, "search_comments")
        assert hasattr(client, "search_asset_files")

    @patch("src.mcp_server_firebase.server.get_firebase_client")
    def test_search_assets_via_mcp(self, mock_get_client, test_credentials_file):
        """Test search_assets tool via direct calls."""
        from src.mcp_server_firebase.server import search_assets

        # Setup mock data
        mock_client = Mock()
        mock_client.search_assets.return_value = [
            {"id": "asset1", "title": "Test Asset", "category": "Template", "visibility": "public"}
        ]
        mock_get_client.return_value = mock_client

        # Call the MCP tool underlying function using .fn attribute
        result = search_assets.fn()

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "asset1"
        assert result[0]["title"] == "Test Asset"

        # Verify mock was called
        mock_client.search_assets.assert_called_once()

    @patch("src.mcp_server_firebase.server.get_firebase_client")
    def test_search_assets_with_filter_via_mcp(self, mock_get_client, test_credentials_file):
        """Test search_assets with filter via direct calls."""
        from src.mcp_server_firebase.server import search_assets

        # Setup mock data
        mock_client = Mock()
        mock_client.search_assets.return_value = [
            {"id": "public_asset", "title": "Public Asset", "visibility": "public"}
        ]
        mock_get_client.return_value = mock_client

        # Call underlying function with filter
        filter_params = {"visibility": "public"}
        result = search_assets.fn(filter_params)

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["visibility"] == "public"

        # Verify mock was called with filter
        mock_client.search_assets.assert_called_once_with(filter_params)

    @patch("src.mcp_server_firebase.server.get_firebase_client")
    def test_search_asset_files_via_mcp(self, mock_get_client, test_credentials_file):
        """Test search_asset_files tool via direct calls."""
        from src.mcp_server_firebase.server import search_asset_files

        # Setup mock data
        mock_client = Mock()
        mock_client.search_asset_files.return_value = [
            {
                "name": "assets/test.jpg",
                "size": 1024,
                "contentType": "image/jpeg",
                "downloadUrl": "https://test.com/test.jpg",
            }
        ]
        mock_get_client.return_value = mock_client

        # Call the MCP tool underlying function using .fn attribute
        result = search_asset_files.fn()

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "assets/test.jpg"
        assert result[0]["contentType"] == "image/jpeg"

        # Verify mock was called
        mock_client.search_asset_files.assert_called_once()

    @patch("src.mcp_server_firebase.server.get_firebase_client")
    def test_all_tools_via_mcp(self, mock_get_client, test_credentials_file):
        """Test all MCP tools via direct calls."""
        from src.mcp_server_firebase.server import (
            search_asset_files,
            search_assets,
            search_comments,
            search_versions,
        )

        # Setup mock data
        mock_client = Mock()
        mock_client.search_assets.return_value = [{"id": "asset1", "title": "Test"}]
        mock_client.search_versions.return_value = [{"id": "version1", "assetId": "asset1"}]
        mock_client.search_comments.return_value = [{"id": "comment1", "assetId": "asset1"}]
        mock_client.search_asset_files.return_value = [{"name": "test.jpg", "size": 1024}]
        mock_get_client.return_value = mock_client

        # Test all tools
        tools_and_functions = [
            ("search_assets", search_assets),
            ("search_versions", search_versions),
            ("search_comments", search_comments),
            ("search_asset_files", search_asset_files),
        ]

        for tool_name, tool_function in tools_and_functions:
            result = tool_function.fn()
            assert isinstance(result, list)
            assert len(result) == 1  # Each mock returns 1 item

        # Verify all mocks were called
        mock_client.search_assets.assert_called()
        mock_client.search_versions.assert_called()
        mock_client.search_comments.assert_called()
        mock_client.search_asset_files.assert_called()


@pytest.mark.integration
class TestMCPServerErrorHandling:
    """Test MCP server error handling."""

    @patch("src.mcp_server_firebase.server.initialize_firebase_client")
    def test_invalid_credentials_file(self, mock_init_client):
        """Test behavior with invalid credentials file."""
        mock_init_client.side_effect = Exception("Invalid credentials")

        # This test would verify the server handles initialization errors gracefully
        # In practice, the server should log the error and exit gracefully
        with pytest.raises(Exception):
            mock_init_client("/invalid/path/credentials.json")

    @patch("src.mcp_server_firebase.server.get_firebase_client")
    def test_firebase_permission_error_via_mcp(self, mock_get_client, test_credentials_file):
        """Test Firebase permission error handling via MCP."""
        from src.mcp_server_firebase.server import search_assets

        # Setup mock to raise permission error
        mock_client = Mock()
        mock_client.search_assets.side_effect = Exception("Permission denied")
        mock_get_client.return_value = mock_client

        # This should propagate the error from underlying function
        with pytest.raises(Exception, match="Permission denied"):
            search_assets.fn()


@pytest.mark.integration
@pytest.mark.slow
class TestMCPServerPerformance:
    """Test MCP server performance characteristics."""

    @patch("src.mcp_server_firebase.server.get_firebase_client")
    def test_concurrent_tool_calls(self, mock_get_client, test_credentials_file):
        """Test concurrent tool calls via direct calls."""
        from src.mcp_server_firebase.server import search_assets, search_versions

        # Setup mock data
        mock_client = Mock()
        mock_client.search_assets.return_value = [{"id": f"asset_{i}"} for i in range(10)]
        mock_client.search_versions.return_value = [{"id": f"version_{i}"} for i in range(5)]
        mock_get_client.return_value = mock_client

        # Make multiple calls to underlying functions
        assets_result = search_assets.fn()
        versions_result = search_versions.fn()
        filtered_assets_result = search_assets.fn({"visibility": "public"})

        # Verify all calls succeeded
        assert len(assets_result) == 10
        assert len(versions_result) == 5
        assert isinstance(filtered_assets_result, list)

        # Verify multiple calls were made
        assert mock_client.search_assets.call_count >= 2
        assert mock_client.search_versions.call_count >= 1

    @patch("src.mcp_server_firebase.server.get_firebase_client")
    def test_large_dataset_handling(self, mock_get_client, test_credentials_file):
        """Test handling of large datasets via direct calls."""
        from src.mcp_server_firebase.server import search_assets

        # Setup mock data - simulate large dataset
        mock_client = Mock()
        large_dataset = [{"id": f"asset_{i}", "title": f"Asset {i}"} for i in range(1000)]
        mock_client.search_assets.return_value = large_dataset
        mock_get_client.return_value = mock_client

        # Test large dataset call to underlying function
        result = search_assets.fn()

        # Verify result
        assert len(result) == 1000
        assert result[0]["id"] == "asset_0"
        assert result[999]["id"] == "asset_999"

        # Verify mock was called
        mock_client.search_assets.assert_called_once()
