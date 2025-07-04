"""Firebase client initialization and management."""

import logging
from typing import Any, Dict, List, Optional

import firebase_admin
from dateutil.parser import parse as parse_datetime
from firebase_admin import credentials, firestore, storage

# from google.cloud import storage as gcs
from google.cloud.firestore_v1 import FieldFilter, Query

logger = logging.getLogger(__name__)


class FirebaseClient:
    """Firebase client for accessing Firestore and Storage."""

    def __init__(self, credentials_path: str):
        """Initialize Firebase client with service account credentials.

        Args:
            credentials_path: Path to the service account JSON file
        """
        self.credentials_path = credentials_path
        self._app: Optional[firebase_admin.App] = None
        self._db: Optional[firestore.firestore.Client] = None
        self._bucket: Optional[Any] = None

    def initialize(self) -> None:
        """Initialize Firebase Admin SDK."""
        try:
            cred = credentials.Certificate(self.credentials_path)
            self._app = firebase_admin.initialize_app(cred)
            self._db = firestore.client()
            self._bucket = storage.bucket("owndays-dam.firebasestorage.app")
            logger.info("Firebase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase client: {e}")
            raise

    @property
    def db(self) -> firestore.firestore.Client:
        """Get Firestore client."""
        if self._db is None:
            raise RuntimeError("Firebase client not initialized")
        return self._db

    @property
    def bucket(self) -> Any:
        """Get Storage bucket."""
        if self._bucket is None:
            raise RuntimeError("Firebase client not initialized")
        return self._bucket

    def _apply_filters(self, query: Query, filters: Dict[str, Any]) -> Query:
        """Apply filters to a Firestore query.

        Args:
            query: Base Firestore query
            filters: Dictionary of field filters

        Returns:
            Modified query with filters applied
        """
        for field, value in filters.items():
            if isinstance(value, str) and value.startswith(">="):
                # Date range filter: ">=2024-06-01"
                date_str = value[2:]
                try:
                    date_value = parse_datetime(date_str)
                    query = query.where(filter=FieldFilter(field, ">=", date_value))
                except ValueError:
                    logger.warning(f"Invalid date format for field {field}: {date_str}")
            elif isinstance(value, str) and value.startswith("<="):
                # Date range filter: "<=2024-12-31"
                date_str = value[2:]
                try:
                    date_value = parse_datetime(date_str)
                    query = query.where(filter=FieldFilter(field, "<=", date_value))
                except ValueError:
                    logger.warning(f"Invalid date format for field {field}: {date_str}")
            elif isinstance(value, list):
                # Array contains any filter
                query = query.where(filter=FieldFilter(field, "array_contains_any", value))
            else:
                # Equality filter
                query = query.where(filter=FieldFilter(field, "==", value))

        return query

    def search_assets(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search assets collection with optional filters.

        Args:
            filters: Optional dictionary of filters to apply

        Returns:
            List of asset documents
        """
        try:
            query = self.db.collection("assets")

            if filters:
                query = self._apply_filters(query, filters)

            docs = query.stream()
            results = []

            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)

            logger.info(f"Found {len(results)} assets")
            return results

        except Exception as e:
            logger.error(f"Error searching assets: {e}")
            raise

    def search_versions(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search versions collection with optional filters.

        Args:
            filters: Optional dictionary of filters to apply

        Returns:
            List of version documents
        """
        try:
            query = self.db.collection("versions")

            if filters:
                query = self._apply_filters(query, filters)

            docs = query.stream()
            results = []

            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)

            logger.info(f"Found {len(results)} versions")
            return results

        except Exception as e:
            logger.error(f"Error searching versions: {e}")
            raise

    def search_comments(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search comments collection with optional filters.

        Args:
            filters: Optional dictionary of filters to apply

        Returns:
            List of comment documents
        """
        try:
            query = self.db.collection("comments")

            if filters:
                query = self._apply_filters(query, filters)

            docs = query.stream()
            results = []

            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)

            logger.info(f"Found {len(results)} comments")
            return results

        except Exception as e:
            logger.error(f"Error searching comments: {e}")
            raise

    def search_asset_files(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search files in the asset storage bucket with optional filters.

        Args:
            filters: Optional dictionary of filters to apply

        Returns:
            List of file metadata dictionaries
        """
        try:
            prefix = filters.get("prefix", "") if filters else ""
            content_type_filter = filters.get("contentType") if filters else None
            uploaded_at_filter = filters.get("uploadedAt") if filters else None

            blobs = self.bucket.list_blobs(prefix=prefix)
            results = []

            for blob in blobs:
                # Apply content type filter
                if content_type_filter and blob.content_type != content_type_filter:
                    continue

                # Apply upload date filter
                if uploaded_at_filter and isinstance(uploaded_at_filter, str):
                    if uploaded_at_filter.startswith(">="):
                        date_str = uploaded_at_filter[2:]
                        try:
                            filter_date = parse_datetime(date_str)
                            if blob.time_created < filter_date:
                                continue
                        except ValueError:
                            logger.warning(f"Invalid date format: {date_str}")
                    elif uploaded_at_filter.startswith("<="):
                        date_str = uploaded_at_filter[2:]
                        try:
                            filter_date = parse_datetime(date_str)
                            if blob.time_created > filter_date:
                                continue
                        except ValueError:
                            logger.warning(f"Invalid date format: {date_str}")

                file_info = {
                    "name": blob.name,
                    "size": blob.size,
                    "contentType": blob.content_type,
                    "uploadedAt": blob.time_created.isoformat() if blob.time_created else None,
                    "downloadUrl": blob.public_url,
                    "etag": blob.etag,
                    "generation": blob.generation,
                }
                results.append(file_info)

            logger.info(f"Found {len(results)} files")
            return results

        except Exception as e:
            logger.error(f"Error searching asset files: {e}")
            raise
