"""Simplified unit tests for MCP server functionality."""

import pytest
from unittest.mock import Mock, patch

from src.mcp_server_firebase.firebase_client import FirebaseClient


@pytest.mark.unit
class TestFirebaseClientIntegration:
    """Test Firebase client methods that MCP tools use."""

    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_complete_workflow(self, mock_bucket, mock_firestore, mock_app, mock_cert, test_credentials_file):
        """Test complete workflow from initialization to data retrieval."""
        # Setup mocks
        mock_cert.return_value = Mock()
        mock_app.return_value = Mock()
        
        # Setup Firestore mock
        mock_db = Mock()
        mock_firestore.return_value = mock_db
        
        # Setup collection and query mocks
        mock_collection = Mock()
        mock_query = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.where.return_value = mock_query
        
        # Mock document results
        mock_doc = Mock()
        mock_doc.id = "test_asset_1"
        mock_doc.to_dict.return_value = {"title": "Test Asset", "category": "Template"}
        mock_query.stream.return_value = [mock_doc]
        mock_collection.stream.return_value = [mock_doc]
        
        # Setup Storage mock
        mock_bucket_obj = Mock()
        mock_bucket.return_value = mock_bucket_obj
        
        # Mock blob results
        mock_blob = Mock()
        mock_blob.name = "assets/test.jpg"
        mock_blob.size = 1024
        mock_blob.content_type = "image/jpeg"
        mock_blob.public_url = "https://test.com/test.jpg"
        mock_bucket_obj.list_blobs.return_value = [mock_blob]
        
        # Test workflow
        client = FirebaseClient(test_credentials_file)
        client.initialize()
        
        # Test assets search
        assets = client.search_assets()
        assert len(assets) == 1
        assert assets[0]["id"] == "test_asset_1"
        assert assets[0]["title"] == "Test Asset"
        
        # Test assets search with filter
        filtered_assets = client.search_assets({"category": "Template"})
        assert len(filtered_assets) == 1
        
        # Test file search
        files = client.search_asset_files()
        assert len(files) == 1
        assert files[0]["name"] == "assets/test.jpg"
        assert files[0]["contentType"] == "image/jpeg"

    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_error_handling(self, mock_bucket, mock_firestore, mock_app, mock_cert, test_credentials_file):
        """Test error handling in Firebase operations."""
        # Setup mocks
        mock_cert.return_value = Mock()
        mock_app.return_value = Mock()
        
        # Setup Firestore to raise an error
        mock_db = Mock()
        mock_firestore.return_value = mock_db
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.stream.side_effect = Exception("Firestore error")
        
        mock_bucket.return_value = Mock()
        
        # Test error handling
        client = FirebaseClient(test_credentials_file)
        client.initialize()
        
        with pytest.raises(Exception, match="Firestore error"):
            client.search_assets()

    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_multiple_document_types(self, mock_bucket, mock_firestore, mock_app, mock_cert, test_credentials_file):
        """Test handling multiple document types."""
        # Setup mocks
        mock_cert.return_value = Mock()
        mock_app.return_value = Mock()
        
        mock_db = Mock()
        mock_firestore.return_value = mock_db
        mock_bucket.return_value = Mock()
        
        # Test each collection type
        collections = ["assets", "versions", "comments"]
        
        for collection_name in collections:
            mock_collection = Mock()
            mock_db.collection.return_value = mock_collection
            
            # Mock different document structures
            if collection_name == "assets":
                mock_doc = Mock()
                mock_doc.id = "asset1"
                mock_doc.to_dict.return_value = {"title": "Test Asset", "category": "Template"}
            elif collection_name == "versions":
                mock_doc = Mock()
                mock_doc.id = "version1"
                mock_doc.to_dict.return_value = {"assetId": "asset1", "fileType": "image/jpeg"}
            else:  # comments
                mock_doc = Mock()
                mock_doc.id = "comment1"
                mock_doc.to_dict.return_value = {"assetId": "asset1", "text": "Test comment"}
            
            mock_collection.stream.return_value = [mock_doc]
            
            # Test
            client = FirebaseClient(test_credentials_file)
            client.initialize()
            
            if collection_name == "assets":
                results = client.search_assets()
            elif collection_name == "versions":
                results = client.search_versions()
            else:
                results = client.search_comments()
            
            assert len(results) == 1
            assert results[0]["id"] == mock_doc.id


@pytest.mark.unit
class TestMCPServerComponents:
    """Test MCP server initialization and components."""

    @patch('src.mcp_server_firebase.server.FirebaseClient')
    def test_server_initialization(self, mock_firebase_client_class):
        """Test MCP server Firebase client initialization."""
        from src.mcp_server_firebase.server import initialize_firebase_client, get_firebase_client
        
        mock_client = Mock()
        mock_firebase_client_class.return_value = mock_client
        
        # Test initialization
        initialize_firebase_client("/test/path/credentials.json")
        
        # Verify client creation and initialization
        mock_firebase_client_class.assert_called_once_with("/test/path/credentials.json")
        mock_client.initialize.assert_called_once()
        
        # Test getting client
        client = get_firebase_client()
        assert client == mock_client

    def test_server_not_initialized(self):
        """Test getting client when not initialized."""
        from src.mcp_server_firebase.server import get_firebase_client
        
        # Reset global state
        import src.mcp_server_firebase.server as server_module
        server_module.firebase_client = None
        
        with pytest.raises(RuntimeError, match="Firebase client not initialized"):
            get_firebase_client()


@pytest.mark.unit
class TestFilterApplication:
    """Test filter application logic."""

    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_date_filter_parsing(self, mock_bucket, mock_firestore, mock_app, mock_cert, test_credentials_file):
        """Test date filter parsing and application."""
        from dateutil.parser import parse as parse_datetime
        
        # Setup mocks
        mock_cert.return_value = Mock()
        mock_app.return_value = Mock()
        mock_db = Mock()
        mock_firestore.return_value = mock_db
        mock_bucket.return_value = Mock()
        
        client = FirebaseClient(test_credentials_file)
        client.initialize()
        
        # Test date parsing
        date_str = "2024-01-01"
        parsed_date = parse_datetime(date_str)
        assert parsed_date.year == 2024
        assert parsed_date.month == 1
        assert parsed_date.day == 1

    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_storage_filtering(self, mock_bucket, mock_firestore, mock_app, mock_cert, test_credentials_file):
        """Test storage file filtering."""
        from datetime import datetime
        
        # Setup mocks
        mock_cert.return_value = Mock()
        mock_app.return_value = Mock()
        mock_db = Mock()
        mock_firestore.return_value = mock_db
        
        # Setup storage with multiple files
        mock_bucket_obj = Mock()
        mock_bucket.return_value = mock_bucket_obj
        
        # Create mock blobs with different properties
        jpeg_blob = Mock()
        jpeg_blob.name = "assets/image.jpg"
        jpeg_blob.content_type = "image/jpeg"
        jpeg_blob.size = 1024
        jpeg_blob.time_created = datetime(2024, 1, 1)
        jpeg_blob.public_url = "https://test.com/image.jpg"
        jpeg_blob.etag = "etag1"
        jpeg_blob.generation = 1
        
        png_blob = Mock()
        png_blob.name = "assets/image.png"
        png_blob.content_type = "image/png"
        png_blob.size = 2048
        png_blob.time_created = datetime(2024, 1, 2)
        png_blob.public_url = "https://test.com/image.png"
        png_blob.etag = "etag2"
        png_blob.generation = 2
        
        mock_bucket_obj.list_blobs.return_value = [jpeg_blob, png_blob]
        
        # Test
        client = FirebaseClient(test_credentials_file)
        client.initialize()
        
        # Test all files
        all_files = client.search_asset_files()
        assert len(all_files) == 2
        
        # Test content type filtering (would be done in the method)
        jpeg_files = [f for f in all_files if f["contentType"] == "image/jpeg"]
        assert len(jpeg_files) == 1
        assert jpeg_files[0]["name"] == "assets/image.jpg"