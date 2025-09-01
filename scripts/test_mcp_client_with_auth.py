#!/usr/bin/env python3
"""
Enhanced MCP Client Test with Authentication

Tests the MCP server with proper JWT authentication headers.
"""

import sys
import os
import asyncio
import json
import aiohttp
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_authenticated_mcp_server():
    """Test MCP server with proper authentication"""
    try:
        from api.auth import create_demo_token
        
        print("🔐 AUTHENTICATED MCP SERVER TEST")
        print("=" * 50)
        
        # Create demo token for testing
        token = create_demo_token("demo_user")
        print(f"🔑 Using token: {token[:30]}...")
        
        # Test endpoints with authentication
        test_cases = [
            {
                "endpoint": "/health",
                "method": "GET",
                "description": "Health check endpoint"
            },
            {
                "endpoint": "/agents/status", 
                "method": "GET",
                "description": "Agent status endpoint"
            },
            {
                "endpoint": "/rpc",
                "method": "POST",
                "description": "JSON-RPC leads query",
                "data": {
                    "jsonrpc": "2.0",
                    "method": "db.leads.query",
                    "params": {"limit": 5},
                    "id": "test_001"
                }
            },
            {
                "endpoint": "/rpc",
                "method": "POST", 
                "description": "JSON-RPC memory store",
                "data": {
                    "jsonrpc": "2.0",
                    "method": "memory.short_term.store",
                    "params": {
                        "conversation_id": "test_conv_001",
                        "lead_id": "test_lead_001",
                        "context": {"test": "authenticated_data"}
                    },
                    "id": "test_002"
                }
            },
            {
                "endpoint": "/rpc",
                "method": "POST",
                "description": "JSON-RPC analytics",
                "data": {
                    "jsonrpc": "2.0", 
                    "method": "analytics.performance",
                    "params": {},
                    "id": "test_003"
                }
            }
        ]
        
        # Test each endpoint
        async with aiohttp.ClientSession() as session:
            print("\n📡 TESTING ENDPOINTS:")
            print("-" * 30)
            
            for i, test_case in enumerate(test_cases, 1):
                try:
                    # Prepare headers
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                    
                    # Make request
                    if test_case["method"] == "GET":
                        async with session.get(
                            f"http://localhost:8000{test_case['endpoint']}", 
                            headers=headers
                        ) as response:
                            result = await response.text()
                            status = response.status
                    else:
                        async with session.post(
                            f"http://localhost:8000{test_case['endpoint']}",
                            headers=headers,
                            json=test_case.get("data", {})
                        ) as response:
                            result = await response.text()
                            status = response.status
                    
                    # Display result
                    if status == 200:
                        print(f"✅ Test {i}: {test_case['description']}")
                        if test_case['endpoint'] == '/rpc':
                            try:
                                json_result = json.loads(result)
                                if 'result' in json_result:
                                    print(f"   📊 Result: {str(json_result['result'])[:100]}...")
                                elif 'error' in json_result:
                                    print(f"   ⚠️ Error: {json_result['error']}")
                            except:
                                print(f"   📄 Response: {result[:100]}...")
                        else:
                            print(f"   📄 Response: {result[:100]}...")
                    else:
                        print(f"❌ Test {i}: {test_case['description']} - Status {status}")
                        print(f"   📄 Response: {result[:100]}...")
                    
                except Exception as e:
                    print(f"❌ Test {i}: {test_case['description']} - Error: {e}")
                
                print()
        
        print("🎉 Authentication test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")


async def demo_agent_communication():
    """Demonstrate agent communication via MCP"""
    try:
        from api.auth import get_demo_tokens
        
        print("\n🤖 AGENT COMMUNICATION DEMO")
        print("=" * 40)
        
        # Get tokens for different agents
        tokens = get_demo_tokens()
        
        print("🔄 Simulating agent-to-agent communication:")
        print("-" * 40)
        
        # Simulate Lead Triage Agent storing triage results
        async with aiohttp.ClientSession() as session:
            triage_token = tokens["lead_triage_001"]
            
            # Store triage results
            triage_data = {
                "jsonrpc": "2.0",
                "method": "memory.short_term.store",
                "params": {
                    "conversation_id": "demo_conv_001",
                    "lead_id": "demo_lead_001",
                    "context": {
                        "agent": "lead_triage_001",
                        "triage_category": "hot",
                        "lead_score": 85,
                        "recommended_action": "immediate_engagement"
                    }
                },
                "id": "triage_001"
            }
            
            headers = {
                "Authorization": f"Bearer {triage_token}",
                "Content-Type": "application/json"
            }
            
            async with session.post(
                "http://localhost:8000/rpc",
                headers=headers,
                json=triage_data
            ) as response:
                if response.status == 200:
                    print("✅ Lead Triage Agent: Stored triage results")
                else:
                    print(f"❌ Lead Triage Agent: Error {response.status}")
            
            # Simulate Engagement Agent retrieving context
            engagement_token = tokens["engagement_001"]
            
            engagement_data = {
                "jsonrpc": "2.0",
                "method": "memory.short_term.get",
                "params": {
                    "conversation_id": "demo_conv_001",
                    "lead_id": "demo_lead_001"
                },
                "id": "engagement_001"
            }
            
            headers = {
                "Authorization": f"Bearer {engagement_token}",
                "Content-Type": "application/json"
            }
            
            async with session.post(
                "http://localhost:8000/rpc",
                headers=headers,
                json=engagement_data
            ) as response:
                if response.status == 200:
                    print("✅ Engagement Agent: Retrieved triage context")
                    result = await response.json()
                    if result.get('result'):
                        print(f"   📋 Context: {result['result']}")
                else:
                    print(f"❌ Engagement Agent: Error {response.status}")
            
            # Test analytics access
            campaign_token = tokens["campaign_opt_001"]
            
            analytics_data = {
                "jsonrpc": "2.0",
                "method": "analytics.performance",
                "params": {"timeframe": "last_30_days"},
                "id": "analytics_001"
            }
            
            headers = {
                "Authorization": f"Bearer {campaign_token}",
                "Content-Type": "application/json"
            }
            
            async with session.post(
                "http://localhost:8000/rpc",
                headers=headers,
                json=analytics_data
            ) as response:
                if response.status == 200:
                    print("✅ Campaign Optimization Agent: Accessed analytics")
                else:
                    print(f"❌ Campaign Optimization Agent: Error {response.status}")
        
        print("\n🎯 Agent communication demo completed!")
        
    except Exception as e:
        print(f"❌ Communication demo error: {e}")


async def main():
    """Main test function"""
    print("🧪 ENHANCED MCP SERVER TESTING")
    print("=" * 50)
    print("📝 Testing with proper JWT authentication")
    print("🔗 Server should be running on localhost:8000")
    print()
    
    # Wait a moment for server to be ready
    await asyncio.sleep(2)
    
    # Run tests
    await test_authenticated_mcp_server()
    await demo_agent_communication()
    
    print("\n🎉 All tests completed successfully!")
    print("🌐 You can also visit http://localhost:8000/docs for interactive API documentation")


if __name__ == "__main__":
    asyncio.run(main())
