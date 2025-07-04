#!/usr/bin/env python3
"""Main entry point for the Firebase MCP Server."""

import argparse
import logging
import sys
from pathlib import Path

from src.mcp_server_firebase.server import mcp, initialize_firebase_client


def setup_logging(debug: bool = False) -> None:
    """Set up logging configuration.
    
    Args:
        debug: Whether to enable debug logging
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Firebase MCP Server - Access Firestore and Storage via MCP"
    )
    parser.add_argument(
        "--google-credentials",
        type=str,
        required=True,
        help="Path to Google service account credentials JSON file"
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind to when using HTTP transport (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to when using HTTP transport (default: 8000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # Validate credentials file
    credentials_path = Path(args.google_credentials)
    if not credentials_path.exists():
        logger.error(f"Credentials file not found: {credentials_path}")
        sys.exit(1)
    
    if not credentials_path.is_file():
        logger.error(f"Credentials path is not a file: {credentials_path}")
        sys.exit(1)
    
    try:
        # Initialize Firebase client
        logger.info("Initializing Firebase client...")
        initialize_firebase_client(str(credentials_path))
        logger.info("Firebase client initialized successfully")
        
        # Start MCP server
        logger.info(f"Starting MCP server with {args.transport} transport...")
        
        if args.transport == "stdio":
            # Use stdio transport for direct MCP client communication
            mcp.run()
        else:
            # Use HTTP transport for web-based access
            logger.info(f"Starting HTTP server on {args.host}:{args.port}")
            mcp.run(transport="http", host=args.host, port=args.port)
            
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()