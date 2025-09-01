#!/usr/bin/env python3
"""
Test MCP Client

Script to test the MCP server by making JSON-RPC calls.
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_mcp_server():
    """Test MCP server functionality"""
    try:
        from transport.json_rpc_client import JSONRPCClient
        from api.auth import create_demo_token
        
        print("🧪 Testing MCP Server Connection...")
        
        # Create client
        client = JSONRPCClient("http://localhost:8000")
        await client.initialize()
        
        # Create demo token
        token = create_demo_token("demo_user")
        print(f"🔑 Created demo token: {token[:20]}...")
        
        # Test methods
        test_methods = [
            ("db.leads.query", {"limit": 5}),
            ("memory.short_term.store", {
                "conversation_id": "test_conv_001",
                "lead_id": "test_lead_001", 
                "context": {"test": "data"}
            }),
            ("analytics.performance", {}),
        ]
        
        print("\n📡 Testing JSON-RPC methods:")
        
        for method, params in test_methods:
            try:
                result = await client.call(method, params)
                print(f"✅ {method}: {result}")
            except Exception as e:
                print(f"❌ {method}: {e}")
        
        await client.cleanup()
        print("\n🎉 MCP client test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")


async def show_demo_tokens():
    """Show demo authentication tokens"""
    try:
        from api.auth import get_demo_tokens
        
        print("🔑 Demo Authentication Tokens:")
        print("=" * 50)
        
        tokens = get_demo_tokens()
        for agent_id, token in tokens.items():
            print(f"Agent: {agent_id}")
            print(f"Token: {token}")
            print("-" * 30)
        
        print("\n💡 Use these tokens in Authorization header:")
        print("   Authorization: Bearer <token>")
        
    except Exception as e:
        print(f"❌ Error generating tokens: {e}")


async def main():
    """Main test function"""
    print("🧪 MCP Server Test Suite")
    print("=" * 40)
    
    # Show demo tokens
    await show_demo_tokens()
    
    print("\n🔗 Testing server connection...")
    print("📝 Note: Make sure MCP server is running on localhost:8000")
    print("   Start with: python scripts/run_mcp_server.py")
    
    # Test server connection
    await test_mcp_server()


if __name__ == "__main__":
    asyncio.run(main())
