"""Core functionality tests for Firebase MCP Server."""

import pytest
from unittest.mock import Mock, patch
from src.mcp_server_firebase.firebase_client import FirebaseClient


@pytest.mark.unit
class TestFirebaseClientCore:
    """Test core Firebase client functionality."""

    def test_initialization(self, test_credentials_file):
        """Test basic initialization."""
        client = FirebaseClient(test_credentials_file)
        assert client.credentials_path == test_credentials_file
        assert client._app is None
        assert client._db is None
        assert client._bucket is None

    def test_properties_before_init(self, test_credentials_file):
        """Test properties raise error when not initialized."""
        client = FirebaseClient(test_credentials_file)
        
        with pytest.raises(RuntimeError, match="Firebase client not initialized"):
            _ = client.db
            
        with pytest.raises(RuntimeError, match="Firebase client not initialized"):
            _ = client.bucket

    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_successful_initialization(self, mock_bucket, mock_firestore, mock_app, mock_cert, test_credentials_file):
        """Test successful Firebase initialization."""
        # Setup mocks
        mock_cert.return_value = Mock()
        mock_app.return_value = Mock()
        mock_db = Mock()
        mock_bucket_obj = Mock()
        mock_firestore.return_value = mock_db
        mock_bucket.return_value = mock_bucket_obj
        
        # Test
        client = FirebaseClient(test_credentials_file)
        client.initialize()
        
        # Verify
        assert client.db == mock_db
        assert client.bucket == mock_bucket_obj
        mock_cert.assert_called_once()
        mock_app.assert_called_once()
        mock_firestore.assert_called_once()
        mock_bucket.assert_called_once_with("owndays-dam.firebasestorage.app")


@pytest.mark.unit  
class TestSearchFunctionality:
    """Test search functionality with mocked Firebase."""

    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_search_assets(self, mock_bucket, mock_firestore, mock_app, mock_cert, test_credentials_file):
        """Test assets search functionality."""
        # Setup mocks
        mock_cert.return_value = Mock()
        mock_app.return_value = Mock()
        
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection
        mock_firestore.return_value = mock_db
        mock_bucket.return_value = Mock()
        
        # Setup document response
        mock_doc = Mock()
        mock_doc.id = "test_asset"
        mock_doc.to_dict.return_value = {
            "title": "Test Asset",
            "category": "Template",
            "visibility": "public"
        }
        mock_collection.stream.return_value = [mock_doc]
        
        # Test
        client = FirebaseClient(test_credentials_file)
        client.initialize()
        results = client.search_assets()
        
        # Verify
        assert len(results) == 1
        assert results[0]["id"] == "test_asset"
        assert results[0]["title"] == "Test Asset"
        mock_db.collection.assert_called_with("assets")

    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_search_asset_files(self, mock_bucket, mock_firestore, mock_app, mock_cert, test_credentials_file):
        """Test asset files search functionality."""
        from datetime import datetime
        
        # Setup mocks
        mock_cert.return_value = Mock()
        mock_app.return_value = Mock()
        mock_firestore.return_value = Mock()
        
        mock_bucket_obj = Mock()
        mock_bucket.return_value = mock_bucket_obj
        
        # Setup blob response
        mock_blob = Mock()
        mock_blob.name = "assets/test.jpg"
        mock_blob.size = 1024
        mock_blob.content_type = "image/jpeg"
        mock_blob.time_created = datetime(2024, 1, 1)
        mock_blob.public_url = "https://test.com/test.jpg"
        mock_blob.etag = "test-etag"
        mock_blob.generation = 1
        mock_bucket_obj.list_blobs.return_value = [mock_blob]
        
        # Test
        client = FirebaseClient(test_credentials_file)
        client.initialize()
        results = client.search_asset_files()
        
        # Verify
        assert len(results) == 1
        assert results[0]["name"] == "assets/test.jpg"
        assert results[0]["contentType"] == "image/jpeg"
        assert results[0]["size"] == 1024
        mock_bucket_obj.list_blobs.assert_called_with(prefix="")

    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_search_with_filters(self, mock_bucket, mock_firestore, mock_app, mock_cert, test_credentials_file):
        """Test search with filters."""
        # Setup mocks
        mock_cert.return_value = Mock()
        mock_app.return_value = Mock()
        
        mock_db = Mock()
        mock_collection = Mock()
        mock_query = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.where.return_value = mock_query
        mock_firestore.return_value = mock_db
        mock_bucket.return_value = Mock()
        
        # Setup filtered response
        mock_doc = Mock()
        mock_doc.id = "filtered_asset"
        mock_doc.to_dict.return_value = {"title": "Filtered Asset", "visibility": "public"}
        mock_query.stream.return_value = [mock_doc]
        
        # Test
        client = FirebaseClient(test_credentials_file)
        client.initialize()
        results = client.search_assets({"visibility": "public"})
        
        # Verify
        assert len(results) == 1
        assert results[0]["id"] == "filtered_asset"
        mock_collection.where.assert_called()

    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_error_handling(self, mock_bucket, mock_firestore, mock_app, mock_cert, test_credentials_file):
        """Test error handling."""
        # Setup mocks
        mock_cert.return_value = Mock()
        mock_app.return_value = Mock()
        
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.stream.side_effect = Exception("Database error")
        mock_firestore.return_value = mock_db
        mock_bucket.return_value = Mock()
        
        # Test
        client = FirebaseClient(test_credentials_file)
        client.initialize()
        
        with pytest.raises(Exception, match="Database error"):
            client.search_assets()


@pytest.mark.unit
class TestMCPServerIntegration:
    """Test MCP server integration components."""

    @patch('src.mcp_server_firebase.server.FirebaseClient')
    def test_server_initialization(self, mock_firebase_client_class):
        """Test server initialization process."""
        from src.mcp_server_firebase.server import initialize_firebase_client, get_firebase_client
        
        mock_client = Mock()
        mock_firebase_client_class.return_value = mock_client
        
        # Test initialization
        initialize_firebase_client("/test/credentials.json")
        
        # Verify
        mock_firebase_client_class.assert_called_once_with("/test/credentials.json")
        mock_client.initialize.assert_called_once()
        
        # Test getting client
        result = get_firebase_client()
        assert result == mock_client

    def test_uninitialized_client_error(self):
        """Test error when accessing uninitialized client."""
        from src.mcp_server_firebase.server import get_firebase_client
        import src.mcp_server_firebase.server as server_module
        
        # Reset global state
        server_module.firebase_client = None
        
        with pytest.raises(RuntimeError, match="Firebase client not initialized"):
            get_firebase_client()


@pytest.mark.unit
class TestUtilityFunctions:
    """Test utility functions and helpers."""

    def test_date_parsing(self):
        """Test date parsing functionality."""
        from dateutil.parser import parse as parse_datetime
        
        # Test various date formats
        test_dates = [
            "2024-01-01",
            "2024-01-01T10:00:00Z",
            "2024-06-15T14:30:00.123Z"
        ]
        
        for date_str in test_dates:
            parsed = parse_datetime(date_str)
            assert parsed.year == 2024
            assert isinstance(parsed.month, int)
            assert isinstance(parsed.day, int)

    def test_filter_operators(self):
        """Test filter operator recognition."""
        # Test various filter patterns
        filters = {
            "equality": "public",
            "date_gte": ">=2024-01-01",
            "date_lte": "<=2024-12-31",
            "array": ["tag1", "tag2"]
        }
        
        # Verify filter patterns
        for key, value in filters.items():
            if key == "equality":
                assert isinstance(value, str) and not value.startswith((">=", "<="))
            elif key.startswith("date_"):
                assert isinstance(value, str) and (value.startswith(">=") or value.startswith("<="))
            elif key == "array":
                assert isinstance(value, list)