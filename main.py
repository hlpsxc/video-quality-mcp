"""Main entry point for the Video Quality MCP Server."""

import asyncio
import sys
from mcp_server import run_server


def main():
    """Main function to start the MCP server."""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

