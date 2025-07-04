"""MCP Server implementation for Firebase access."""

import logging
from typing import Dict, Any, List, Optional

from fastmcp import FastMCP
from .firebase_client import FirebaseClient

logger = logging.getLogger(__name__)

# Global Firebase client instance
firebase_client: Optional[FirebaseClient] = None


def initialize_firebase_client(credentials_path: str) -> None:
    """Initialize the global Firebase client.
    
    Args:
        credentials_path: Path to the service account JSON file
    """
    global firebase_client
    firebase_client = FirebaseClient(credentials_path)
    firebase_client.initialize()


def get_firebase_client() -> FirebaseClient:
    """Get the initialized Firebase client.
    
    Returns:
        The Firebase client instance
        
    Raises:
        RuntimeError: If the client is not initialized
    """
    if firebase_client is None:
        raise RuntimeError("Firebase client not initialized")
    return firebase_client


# Initialize FastMCP
mcp = FastMCP("Firebase MCP Server")


@mcp.tool()
def search_assets(filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Search assets in the Firestore assets collection.
    
    The assets collection contains digital asset metadata with the following fields:
    - id: string - Unique asset identifier
    - title: string - Asset title
    - description: string - Asset description
    - category: string - Asset category (e.g., "image", "video", "document")
    - tags: string[] - Array of tags for categorization
    - uploader: string - User ID who uploaded the asset
    - uploadedAt: string - Upload timestamp in ISO8601 format
    - updatedAt: string - Last update timestamp in ISO8601 format
    - visibility: 'public' | 'private' - Asset visibility level
    - latestVersionId: string (optional) - ID of the latest version
    
    Args:
        filter: Optional dictionary of filters to apply. Supported filters:
            - category: string - Filter by asset category
            - tags: string[] - Filter by tags (array-contains-any)
            - visibility: 'public' | 'private' - Filter by visibility
            - uploader: string - Filter by uploader user ID
            - uploadedAt: string - Filter by upload date (use ">=2024-06-01" format)
            - updatedAt: string - Filter by update date (use ">=2024-06-01" format)
    
    Returns:
        List of asset documents matching the filters
        
    Example:
        ```python
        # Search for public image assets with banner tag uploaded after June 1, 2024
        search_assets({
            "category": "image",
            "tags": ["banner"],
            "visibility": "public",
            "uploadedAt": ">=2024-06-01"
        })
        ```
    """
    try:
        client = get_firebase_client()
        return client.search_assets(filter)
    except Exception as e:
        logger.error(f"Error in search_assets: {e}")
        raise


@mcp.tool()
def search_versions(filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Search versions in the Firestore versions collection.
    
    The versions collection contains version metadata for assets with the following fields:
    - id: string - Unique version identifier
    - assetId: string - ID of the parent asset
    - version: string - Version number or identifier
    - fileUrl: string - URL to the actual file
    - fileName: string - Original filename
    - fileType: string - MIME type of the file
    - fileSize: number - File size in bytes
    - updatedAt: string - Update timestamp in ISO8601 format
    - updatedBy: string - User ID who updated this version
    
    Args:
        filter: Optional dictionary of filters to apply. Supported filters:
            - assetId: string - Filter by parent asset ID
            - version: string - Filter by version identifier
            - fileType: string - Filter by MIME type
            - updatedBy: string - Filter by user who updated the version
            - updatedAt: string - Filter by update date (use ">=2024-06-01" format)
    
    Returns:
        List of version documents matching the filters
        
    Example:
        ```python
        # Search for PNG versions of a specific asset updated after June 1, 2024
        search_versions({
            "assetId": "asset123",
            "fileType": "image/png",
            "updatedAt": ">=2024-06-01"
        })
        ```
    """
    try:
        client = get_firebase_client()
        return client.search_versions(filter)
    except Exception as e:
        logger.error(f"Error in search_versions: {e}")
        raise


@mcp.tool()
def search_comments(filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Search comments in the Firestore comments collection.
    
    The comments collection contains user comments on assets with the following fields:
    - id: string - Unique comment identifier
    - assetId: string - ID of the asset being commented on
    - user: string - User ID who made the comment
    - text: string - Comment text content
    - createdAt: string - Comment creation timestamp in ISO8601 format
    
    Args:
        filter: Optional dictionary of filters to apply. Supported filters:
            - assetId: string - Filter by asset ID
            - user: string - Filter by user ID
            - createdAt: string - Filter by creation date (use ">=2024-06-01" format)
    
    Returns:
        List of comment documents matching the filters
        
    Example:
        ```python
        # Search for comments on a specific asset by a specific user after June 1, 2024
        search_comments({
            "assetId": "asset123",
            "user": "user456",
            "createdAt": ">=2024-06-01"
        })
        ```
    """
    try:
        client = get_firebase_client()
        return client.search_comments(filter)
    except Exception as e:
        logger.error(f"Error in search_comments: {e}")
        raise


@mcp.tool()
def search_asset_files(filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Search files in the Firebase Storage bucket.
    
    This tool searches for files in the 'owndays-dam.firebasestorage.app' bucket
    which contains the actual asset files referenced by the Firestore documents.
    
    Args:
        filter: Optional dictionary of filters to apply. Supported filters:
            - prefix: string - Filter by file path prefix (e.g., "assets/")
            - contentType: string - Filter by MIME type (e.g., "image/png")
            - uploadedAt: string - Filter by upload date (use ">=2024-06-01" format)
    
    Returns:
        List of file metadata dictionaries with the following fields:
        - name: string - Full file path in the bucket
        - size: number - File size in bytes
        - contentType: string - MIME type of the file
        - uploadedAt: string - Upload timestamp in ISO8601 format
        - downloadUrl: string - Public download URL
        - etag: string - ETag for versioning
        - generation: number - File generation number
        
    Example:
        ```python
        # Search for PNG images in the assets folder uploaded after June 1, 2024
        search_asset_files({
            "prefix": "assets/",
            "contentType": "image/png",
            "uploadedAt": ">=2024-06-01"
        })
        ```
    """
    try:
        client = get_firebase_client()
        return client.search_asset_files(filter)
    except Exception as e:
        logger.error(f"Error in search_asset_files: {e}")
        raise