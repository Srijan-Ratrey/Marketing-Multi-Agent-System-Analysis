#!/usr/bin/env python3
"""
Run MCP Server

Script to start the Model Context Protocol server for the marketing multi-agent system.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run the MCP server"""
    try:
        # Import MCP server
        from mcp_server.server import MCPServer
        
        # Create and start server
        server = MCPServer()
        
        print("🚀 Starting Marketing Multi-Agent MCP Server...")
        print("📡 Server will be available at: http://localhost:8000")
        print("📋 API Documentation: http://localhost:8000/docs")
        print("🔍 Health Check: http://localhost:8000/health")
        print("\n🔧 Available endpoints:")
        print("  • POST /rpc - JSON-RPC 2.0 endpoint")
        print("  • WS /ws/{agent_id} - WebSocket for agents")
        print("  • GET /agents/status - Agent status")
        print("  • GET /resources/access-log - Resource access logs")
        print("\nPress Ctrl+C to stop the server\n")
        
        # Start server
        await server.start_server(host="0.0.0.0", port=8000)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try installing missing dependencies:")
        print("   pip install fastapi uvicorn pydantic")
    except Exception as e:
        print(f"❌ Server error: {e}")
        logger.exception("Server startup failed")


if __name__ == "__main__":
    asyncio.run(main())
