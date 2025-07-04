"""Pytest configuration and fixtures."""

import json
import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

# Valid test credentials for mocking
TEST_CREDENTIALS = {
    "type": "service_account",
    "project_id": "test-project",
    "private_key_id": "test-key-id",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQCv1+g2XgLY4KKy\n2pq2kW2R7c8cV5l0xY1HHy1C9D8fCVx1f3VQ5g4O1J9Y3YON1bA1k2dF7aD5x1Q\nabc123defghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUV\nWXYZ+/0123456789abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJ\nKLMNOPQRSTUVWXYZ/0123456789abcdefghijklmnopqrstuvwxyz0123456789A\nBCDEFGHIJKLMNOPQRSTUVWXYZ/0123456789abcdefghijklmnopqrstuvwxyz012\n-----END PRIVATE KEY-----\n",
    "client_email": "test@test-project.iam.gserviceaccount.com",
    "client_id": "123456789",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test",
    "universe_domain": "googleapis.com",
}

# Test data for mocking Firebase responses
TEST_ASSETS = [
    {
        "id": "asset1",
        "title": "Test Asset 1",
        "description": "Test Description 1",
        "category": "Template",
        "tags": ["test", "banner"],
        "uploader": "Test User",
        "uploadedAt": "2024-01-01T10:00:00Z",
        "updatedAt": "2024-01-01T10:00:00Z",
        "visibility": "public",
        "latestVersionId": "version1",
    },
    {
        "id": "asset2",
        "title": "Test Asset 2",
        "description": "Test Description 2",
        "category": "Image",
        "tags": ["test"],
        "uploader": "Test User 2",
        "uploadedAt": "2024-01-02T10:00:00Z",
        "updatedAt": "2024-01-02T10:00:00Z",
        "visibility": "private",
        "latestVersionId": "version2",
    },
]

TEST_VERSIONS = [
    {
        "id": "version1",
        "assetId": "asset1",
        "version": "1.0",
        "fileUrl": "https://test.com/file1.jpg",
        "fileName": "test1.jpg",
        "fileType": "image/jpeg",
        "fileSize": 1024,
        "updatedAt": "2024-01-01T10:00:00Z",
        "updatedBy": "Test User",
    },
    {
        "id": "version2",
        "assetId": "asset2",
        "version": "1.0",
        "fileUrl": "https://test.com/file2.png",
        "fileName": "test2.png",
        "fileType": "image/png",
        "fileSize": 2048,
        "updatedAt": "2024-01-02T10:00:00Z",
        "updatedBy": "Test User 2",
    },
]

TEST_COMMENTS = [
    {
        "id": "comment1",
        "assetId": "asset1",
        "user": "Test User",
        "text": "Test comment 1",
        "createdAt": "2024-01-01T11:00:00Z",
    },
    {
        "id": "comment2",
        "assetId": "asset1",
        "user": "Test User 2",
        "text": "Test comment 2",
        "createdAt": "2024-01-01T12:00:00Z",
    },
]

TEST_FILES = [
    {
        "name": "assets/test1.jpg",
        "size": 1024,
        "contentType": "image/jpeg",
        "uploadedAt": "2024-01-01T10:00:00+00:00",
        "downloadUrl": "https://test.com/test1.jpg",
        "etag": "test-etag-1",
        "generation": 1,
    },
    {
        "name": "assets/test2.png",
        "size": 2048,
        "contentType": "image/png",
        "uploadedAt": "2024-01-02T10:00:00+00:00",
        "downloadUrl": "https://test.com/test2.png",
        "etag": "test-etag-2",
        "generation": 2,
    },
]


@pytest.fixture
def test_credentials_file():
    """Create a temporary credentials file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(TEST_CREDENTIALS, f)
        credentials_path = f.name

    yield credentials_path

    # Cleanup
    if os.path.exists(credentials_path):
        os.unlink(credentials_path)


@pytest.fixture
def mock_firebase_app():
    """Mock Firebase App."""
    with patch("firebase_admin.initialize_app") as mock:
        mock_app = Mock()
        mock.return_value = mock_app
        yield mock_app


@pytest.fixture
def mock_firestore_client():
    """Mock Firestore client."""
    with patch("firebase_admin.firestore.client") as mock:
        mock_client = Mock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_storage_bucket():
    """Mock Storage bucket."""
    with patch("firebase_admin.storage.bucket") as mock:
        mock_bucket = Mock()
        mock.return_value = mock_bucket
        yield mock_bucket


@pytest.fixture
def mock_firestore_query():
    """Mock Firestore query with test data."""

    def _create_mock_doc(data):
        mock_doc = Mock()
        mock_doc.id = data["id"]
        mock_doc.to_dict.return_value = {k: v for k, v in data.items() if k != "id"}
        return mock_doc

    mock_query = Mock()

    # Default behavior: return all assets
    mock_query.stream.return_value = [_create_mock_doc(asset) for asset in TEST_ASSETS]
    mock_query.where.return_value = mock_query
    mock_query.limit.return_value = mock_query

    return mock_query


@pytest.fixture
def mock_storage_blobs():
    """Mock Storage blobs."""

    def _create_mock_blob(file_data):
        mock_blob = Mock()
        mock_blob.name = file_data["name"]
        mock_blob.size = file_data["size"]
        mock_blob.content_type = file_data["contentType"]
        mock_blob.time_created = datetime.fromisoformat(
            file_data["uploadedAt"].replace("Z", "+00:00")
        )
        mock_blob.public_url = file_data["downloadUrl"]
        mock_blob.etag = file_data["etag"]
        mock_blob.generation = file_data["generation"]
        return mock_blob

    return [_create_mock_blob(file_data) for file_data in TEST_FILES]


@pytest.fixture
def sample_filter():
    """Sample filter for testing."""
    return {"visibility": "public"}


@pytest.fixture
def date_filter():
    """Date filter for testing."""
    return {"uploadedAt": ">=2024-01-01"}


# Markers for organizing tests
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "firebase: Tests requiring Firebase connection")
