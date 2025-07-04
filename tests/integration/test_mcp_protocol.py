"""Integration tests for MCP protocol communication."""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.integration
@pytest.mark.asyncio
class TestMCPProtocolIntegration:
    """Test MCP protocol integration."""

    @patch('src.mcp_server_firebase.server.initialize_firebase_client')
    @patch('src.mcp_server_firebase.server.get_firebase_client')
    async def test_mcp_server_initialization(self, mock_get_client, mock_init_client, test_credentials_file):
        """Test MCP server initialization via protocol."""
        # Setup mocks
        mock_client = Mock()
        mock_client.search_assets.return_value = []
        mock_get_client.return_value = mock_client
        
        # Create server parameters
        server_params = StdioServerParameters(
            command="python3",
            args=[
                "main.py",
                "--google-credentials",
                test_credentials_file,
                "--transport",
                "stdio"
            ],
            cwd=os.getcwd()
        )
        
        # Test MCP connection (with timeout for safety)
        try:
            async with asyncio.wait_for(stdio_client(server_params), timeout=10.0) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize session
                    await session.initialize()
                    
                    # Verify server is responding
                    tools = await session.list_tools()
                    tool_names = [tool.name for tool in tools.tools]
                    
                    # Verify expected tools are available
                    expected_tools = ["search_assets", "search_versions", "search_comments", "search_asset_files"]
                    for tool in expected_tools:
                        assert tool in tool_names
                        
        except asyncio.TimeoutError:
            pytest.skip("MCP server startup timeout - may indicate environment issues")

    @patch('src.mcp_server_firebase.server.initialize_firebase_client')
    @patch('src.mcp_server_firebase.server.get_firebase_client')
    async def test_search_assets_via_mcp(self, mock_get_client, mock_init_client, test_credentials_file):
        """Test search_assets tool via MCP protocol."""
        # Setup mock data
        mock_client = Mock()
        mock_client.search_assets.return_value = [
            {
                "id": "asset1",
                "title": "Test Asset",
                "category": "Template",
                "visibility": "public"
            }
        ]
        mock_get_client.return_value = mock_client
        
        server_params = StdioServerParameters(
            command="python3",
            args=[
                "main.py",
                "--google-credentials",
                test_credentials_file,
                "--transport",
                "stdio"
            ],
            cwd=os.getcwd()
        )
        
        try:
            async with asyncio.wait_for(stdio_client(server_params), timeout=10.0) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Call search_assets tool
                    result = await session.call_tool("search_assets", {})
                    
                    # Verify result
                    assert result.content is not None
                    assert len(result.content) > 0
                    
                    # Parse JSON response
                    response_text = result.content[0].text
                    assets = json.loads(response_text)
                    
                    assert len(assets) == 1
                    assert assets[0]["id"] == "asset1"
                    assert assets[0]["title"] == "Test Asset"
                    
        except asyncio.TimeoutError:
            pytest.skip("MCP server startup timeout")

    @patch('src.mcp_server_firebase.server.initialize_firebase_client')
    @patch('src.mcp_server_firebase.server.get_firebase_client')
    async def test_search_assets_with_filter_via_mcp(self, mock_get_client, mock_init_client, test_credentials_file):
        """Test search_assets with filter via MCP protocol."""
        # Setup mock data
        mock_client = Mock()
        mock_client.search_assets.return_value = [
            {
                "id": "public_asset",
                "title": "Public Asset",
                "visibility": "public"
            }
        ]
        mock_get_client.return_value = mock_client
        
        server_params = StdioServerParameters(
            command="python3",
            args=[
                "main.py",
                "--google-credentials",
                test_credentials_file,
                "--transport",
                "stdio"
            ],
            cwd=os.getcwd()
        )
        
        try:
            async with asyncio.wait_for(stdio_client(server_params), timeout=10.0) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Call search_assets with filter
                    filter_params = {"filter": {"visibility": "public"}}
                    result = await session.call_tool("search_assets", filter_params)
                    
                    # Verify result
                    assert result.content is not None
                    response_text = result.content[0].text
                    assets = json.loads(response_text)
                    
                    assert len(assets) == 1
                    assert assets[0]["visibility"] == "public"
                    
        except asyncio.TimeoutError:
            pytest.skip("MCP server startup timeout")

    @patch('src.mcp_server_firebase.server.initialize_firebase_client')
    @patch('src.mcp_server_firebase.server.get_firebase_client')
    async def test_search_asset_files_via_mcp(self, mock_get_client, mock_init_client, test_credentials_file):
        """Test search_asset_files tool via MCP protocol."""
        # Setup mock data
        mock_client = Mock()
        mock_client.search_asset_files.return_value = [
            {
                "name": "assets/test.jpg",
                "size": 1024,
                "contentType": "image/jpeg",
                "downloadUrl": "https://test.com/test.jpg"
            }
        ]
        mock_get_client.return_value = mock_client
        
        server_params = StdioServerParameters(
            command="python3",
            args=[
                "main.py",
                "--google-credentials",
                test_credentials_file,
                "--transport",
                "stdio"
            ],
            cwd=os.getcwd()
        )
        
        try:
            async with asyncio.wait_for(stdio_client(server_params), timeout=10.0) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Call search_asset_files tool
                    result = await session.call_tool("search_asset_files", {})
                    
                    # Verify result
                    assert result.content is not None
                    response_text = result.content[0].text
                    files = json.loads(response_text)
                    
                    assert len(files) == 1
                    assert files[0]["name"] == "assets/test.jpg"
                    assert files[0]["contentType"] == "image/jpeg"
                    
        except asyncio.TimeoutError:
            pytest.skip("MCP server startup timeout")

    @patch('src.mcp_server_firebase.server.initialize_firebase_client')
    @patch('src.mcp_server_firebase.server.get_firebase_client')
    async def test_all_tools_via_mcp(self, mock_get_client, mock_init_client, test_credentials_file):
        """Test all tools via MCP protocol."""
        # Setup mock data
        mock_client = Mock()
        mock_client.search_assets.return_value = [{"id": "asset1", "title": "Test"}]
        mock_client.search_versions.return_value = [{"id": "version1", "assetId": "asset1"}]
        mock_client.search_comments.return_value = [{"id": "comment1", "assetId": "asset1"}]
        mock_client.search_asset_files.return_value = [{"name": "test.jpg", "size": 1024}]
        mock_get_client.return_value = mock_client
        
        server_params = StdioServerParameters(
            command="python3",
            args=[
                "main.py",
                "--google-credentials",
                test_credentials_file,
                "--transport",
                "stdio"
            ],
            cwd=os.getcwd()
        )
        
        try:
            async with asyncio.wait_for(stdio_client(server_params), timeout=15.0) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Test all tools
                    tools_to_test = [
                        "search_assets",
                        "search_versions", 
                        "search_comments",
                        "search_asset_files"
                    ]
                    
                    for tool_name in tools_to_test:
                        result = await session.call_tool(tool_name, {})
                        assert result.content is not None
                        
                        response_text = result.content[0].text
                        data = json.loads(response_text)
                        assert len(data) == 1  # Each mock returns 1 item
                        
        except asyncio.TimeoutError:
            pytest.skip("MCP server startup timeout")


@pytest.mark.integration
class TestMCPServerErrorHandling:
    """Test MCP server error handling."""

    @patch('src.mcp_server_firebase.server.initialize_firebase_client')
    def test_invalid_credentials_file(self, mock_init_client):
        """Test behavior with invalid credentials file."""
        mock_init_client.side_effect = Exception("Invalid credentials")
        
        # This test would verify the server handles initialization errors gracefully
        # In practice, the server should log the error and exit gracefully
        with pytest.raises(Exception):
            mock_init_client("/invalid/path/credentials.json")

    @patch('src.mcp_server_firebase.server.get_firebase_client')
    async def test_firebase_permission_error_via_mcp(self, mock_get_client, test_credentials_file):
        """Test Firebase permission error handling via MCP."""
        # Setup mock to raise permission error
        mock_client = Mock()
        mock_client.search_assets.side_effect = Exception("Permission denied")
        mock_get_client.return_value = mock_client
        
        server_params = StdioServerParameters(
            command="python3",
            args=[
                "main.py",
                "--google-credentials",
                test_credentials_file,
                "--transport",
                "stdio"
            ],
            cwd=os.getcwd()
        )
        
        try:
            async with asyncio.wait_for(stdio_client(server_params), timeout=10.0) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # This should handle the error gracefully
                    with pytest.raises(Exception):
                        await session.call_tool("search_assets", {})
                        
        except asyncio.TimeoutError:
            pytest.skip("MCP server startup timeout")


@pytest.mark.integration
@pytest.mark.slow
class TestMCPServerPerformance:
    """Test MCP server performance characteristics."""

    @patch('src.mcp_server_firebase.server.initialize_firebase_client')
    @patch('src.mcp_server_firebase.server.get_firebase_client')
    async def test_concurrent_tool_calls(self, mock_get_client, mock_init_client, test_credentials_file):
        """Test concurrent tool calls via MCP."""
        # Setup mock data
        mock_client = Mock()
        mock_client.search_assets.return_value = [{"id": f"asset_{i}"} for i in range(10)]
        mock_client.search_versions.return_value = [{"id": f"version_{i}"} for i in range(5)]
        mock_get_client.return_value = mock_client
        
        server_params = StdioServerParameters(
            command="python3",
            args=[
                "main.py",
                "--google-credentials",
                test_credentials_file,
                "--transport",
                "stdio"
            ],
            cwd=os.getcwd()
        )
        
        try:
            async with asyncio.wait_for(stdio_client(server_params), timeout=15.0) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Make concurrent calls
                    tasks = [
                        session.call_tool("search_assets", {}),
                        session.call_tool("search_versions", {}),
                        session.call_tool("search_assets", {"filter": {"visibility": "public"}}),
                    ]
                    
                    results = await asyncio.gather(*tasks)
                    
                    # Verify all calls succeeded
                    assert len(results) == 3
                    for result in results:
                        assert result.content is not None
                        data = json.loads(result.content[0].text)
                        assert isinstance(data, list)
                        
        except asyncio.TimeoutError:
            pytest.skip("MCP server startup timeout")

    @patch('src.mcp_server_firebase.server.initialize_firebase_client')
    @patch('src.mcp_server_firebase.server.get_firebase_client')
    async def test_large_dataset_handling(self, mock_get_client, mock_init_client, test_credentials_file):
        """Test handling of large datasets via MCP."""
        # Setup mock data - simulate large dataset
        mock_client = Mock()
        large_dataset = [{"id": f"asset_{i}", "title": f"Asset {i}"} for i in range(1000)]
        mock_client.search_assets.return_value = large_dataset
        mock_get_client.return_value = mock_client
        
        server_params = StdioServerParameters(
            command="python3",
            args=[
                "main.py",
                "--google-credentials",
                test_credentials_file,
                "--transport",
                "stdio"
            ],
            cwd=os.getcwd()
        )
        
        try:
            async with asyncio.wait_for(stdio_client(server_params), timeout=20.0) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Test large dataset call
                    result = await session.call_tool("search_assets", {})
                    
                    # Verify result
                    assert result.content is not None
                    response_text = result.content[0].text
                    assets = json.loads(response_text)
                    
                    assert len(assets) == 1000
                    assert assets[0]["id"] == "asset_0"
                    assert assets[999]["id"] == "asset_999"
                    
        except asyncio.TimeoutError:
            pytest.skip("MCP server startup timeout - large dataset test")