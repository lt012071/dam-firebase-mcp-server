# Firebase MCP Server

A Model Context Protocol (MCP) server implementation for accessing Firebase Firestore and Storage, built with Python and FastMCP.

## Overview

This MCP server provides secure access to Firebase Firestore collections and Storage buckets through MCP-compliant tools. It's designed specifically for a Digital Asset Management (DAM) system with predefined collections and access patterns.

## Features

- **MCP Protocol Compliance**: Fully compliant with the official MCP specification
- **Firestore Access**: Query `assets`, `versions`, and `comments` collections
- **Storage Access**: Search files in the Firebase Storage bucket
- **Flexible Filtering**: Support for various filter operators including date ranges
- **Dual Transport**: Support for both stdio and HTTP transports
- **Docker Support**: Containerized deployment with Docker
- **Security**: Service account-based authentication with restricted access

## Installation

### Prerequisites

- Python 3.11 or higher
- Firebase project with Firestore and Storage enabled
- Google Cloud service account with appropriate permissions

### Dependencies

```bash
pip install -r requirements.txt
```

### Required Python Packages

- `fastmcp>=0.1.0`
- `firebase-admin>=6.5.0`
- `python-dateutil>=2.8.2`
- `typing-extensions>=4.9.0`

## Usage

### Command Line

```bash
# Run with stdio transport (for MCP clients)
python main.py --google-credentials /path/to/service-account.json --transport stdio

# Run with HTTP transport (for web access)
python main.py --google-credentials /path/to/service-account.json --transport http --host 0.0.0.0 --port 8000

# Enable debug logging
python main.py --google-credentials /path/to/service-account.json --debug
```

### Docker

```bash
# Build the image
docker build -t firebase-mcp-server .

# Run with docker-compose
docker-compose up -d

# Run manually
docker run -p 8000:8000 -v /path/to/credentials.json:/app/credentials.json firebase-mcp-server
```

## Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "firebase-dam": {
      "command": "python",
      "args": [
        "/path/to/mcp-server/main.py",
        "--google-credentials",
        "/path/to/your/service-account-credentials.json",
        "--transport",
        "stdio"
      ],
      "env": {
        "PYTHONPATH": "/path/to/mcp-server"
      }
    }
  }
}
```

### Service Account Setup

⚠️ **SECURITY WARNING**: Never commit credentials files to version control!

1. Create a service account in your Firebase project
2. Download the JSON credentials file
3. Copy `credentials.json.example` to `credentials.json` and fill in your actual values
4. Grant the service account the following permissions:
   - Firestore: `Firebase Rules System`, `Cloud Datastore User`
   - Storage: `Storage Object Viewer`

## Available Tools

### search_assets

Search assets in the Firestore assets collection.

**Schema:**
- `id`: string - Unique asset identifier
- `title`: string - Asset title
- `description`: string - Asset description
- `category`: string - Asset category
- `tags`: string[] - Array of tags
- `uploader`: string - User ID who uploaded
- `uploadedAt`: string - ISO8601 timestamp
- `updatedAt`: string - ISO8601 timestamp
- `visibility`: 'public' | 'private'
- `latestVersionId`: string (optional)

**Example:**
```json
{
  "category": "image",
  "tags": ["banner"],
  "visibility": "public",
  "uploadedAt": ">=2024-06-01"
}
```

### search_versions

Search versions in the Firestore versions collection.

**Schema:**
- `id`: string - Unique version identifier
- `assetId`: string - Parent asset ID
- `version`: string - Version identifier
- `fileUrl`: string - URL to the file
- `fileName`: string - Original filename
- `fileType`: string - MIME type
- `fileSize`: number - File size in bytes
- `updatedAt`: string - ISO8601 timestamp
- `updatedBy`: string - User ID who updated

**Example:**
```json
{
  "assetId": "asset123",
  "fileType": "image/png",
  "updatedAt": ">=2024-06-01"
}
```

### search_comments

Search comments in the Firestore comments collection.

**Schema:**
- `id`: string - Unique comment identifier
- `assetId`: string - Asset being commented on
- `user`: string - User ID who commented
- `text`: string - Comment text
- `createdAt`: string - ISO8601 timestamp

**Example:**
```json
{
  "assetId": "asset123",
  "user": "user456",
  "createdAt": ">=2024-06-01"
}
```

### search_asset_files

Search files in the Firebase Storage bucket.

**Returns:**
- `name`: string - Full file path
- `size`: number - File size in bytes
- `contentType`: string - MIME type
- `uploadedAt`: string - ISO8601 timestamp
- `downloadUrl`: string - Public URL
- `etag`: string - ETag for versioning
- `generation`: number - File generation

**Example:**
```json
{
  "prefix": "assets/",
  "contentType": "image/png",
  "uploadedAt": ">=2024-06-01"
}
```

## Filter Operators

- `==` - Equality (default)
- `>=` - Greater than or equal (for dates)
- `<=` - Less than or equal (for dates)
- `array_contains_any` - Array contains any of the values
- `in` - Value is in the provided array

## Architecture

```
src/
├── mcp_server_firebase/
│   ├── __init__.py
│   ├── server.py          # FastMCP server with tools
│   └── firebase_client.py # Firebase client wrapper
├── main.py                # Entry point
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Docker Compose setup
└── examples/             # Configuration examples
```

## Security Notes

- Collections and bucket names are hardcoded in the source code
- Access is restricted to read-only operations
- Service account credentials are required for authentication
- No sensitive data is logged or exposed

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

### Linting

```bash
# Run linting
flake8 src/ main.py
black src/ main.py
```

## Troubleshooting

### Common Issues

1. **Credentials not found**: Ensure the service account JSON file path is correct
2. **Permission denied**: Verify the service account has the required Firebase permissions
3. **Connection issues**: Check network connectivity and Firebase project settings
4. **Import errors**: Ensure all dependencies are installed correctly

### Debug Mode

Enable debug logging to see detailed operation logs:

```bash
python main.py --google-credentials /path/to/credentials.json --debug
```

## License

This project is licensed under the MIT License.