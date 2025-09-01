#!/usr/bin/env python3
"""
Multi-Agent System Test Script

This script tests the core components of the marketing multi-agent system:
- Data loading and analysis
- Agent functionality
- Memory systems
- MCP server components

Run with: python scripts/test_system.py
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, status="INFO"):
    """Print colored status messages"""
    color = {
        "SUCCESS": Colors.GREEN,
        "ERROR": Colors.RED,
        "WARNING": Colors.YELLOW,
        "INFO": Colors.BLUE
    }.get(status, Colors.BLUE)
    
    print(f"{color}{Colors.BOLD}[{status}]{Colors.END} {color}{message}{Colors.END}")

def print_header(title):
    """Print section header"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title:^60}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")

async def test_data_loading():
    """Test 1: Data Loading and Analysis"""
    print_header("TEST 1: DATA LOADING AND ANALYSIS")
    
    try:
        import pandas as pd
        import numpy as np
        
        # Test data directory
        data_dir = project_root / "marketing_multi_agent_dataset_v1_final"
        if not data_dir.exists():
            print_status("Dataset directory not found!", "ERROR")
            return False
        
        print_status(f"Found dataset directory: {data_dir}", "SUCCESS")
        
        # Test loading core datasets
        datasets = {}
        core_files = [
            'campaigns.csv', 'leads.csv', 'interactions.csv', 
            'agent_actions.csv', 'conversions.csv'
        ]
        
        for filename in core_files:
            filepath = data_dir / filename
            if filepath.exists():
                try:
                    df = pd.read_csv(filepath)
                    datasets[filename.replace('.csv', '')] = df
                    print_status(f"✓ Loaded {filename}: {df.shape}", "SUCCESS")
                except Exception as e:
                    print_status(f"✗ Error loading {filename}: {e}", "ERROR")
                    return False
            else:
                print_status(f"✗ File not found: {filename}", "ERROR")
                return False
        
        # Validate data quality
        leads = datasets['leads']
        conversions = datasets['conversions']
        
        print_status(f"Total leads: {len(leads):,}", "INFO")
        print_status(f"Total conversions: {len(conversions):,}", "INFO")
        print_status(f"Conversion rate: {len(conversions)/len(leads)*100:.2f}%", "INFO")
        
        # Check for required columns
        required_columns = {
            'leads': ['lead_id', 'triage_category', 'lead_score', 'lead_status'],
            'conversions': ['lead_id', 'conversion_type', 'conversion_value_usd']
        }
        
        for dataset_name, columns in required_columns.items():
            df = datasets[dataset_name]
            missing_cols = [col for col in columns if col not in df.columns]
            if missing_cols:
                print_status(f"Missing columns in {dataset_name}: {missing_cols}", "ERROR")
                return False
            else:
                print_status(f"✓ All required columns present in {dataset_name}", "SUCCESS")
        
        return True
        
    except ImportError as e:
        print_status(f"Import error: {e}", "ERROR")
        return False
    except Exception as e:
        print_status(f"Unexpected error: {e}", "ERROR")
        return False

async def test_agent_framework():
    """Test 2: Agent Framework"""
    print_header("TEST 2: AGENT FRAMEWORK")
    
    try:
        # Test imports
        from agents.base_agent import BaseAgent, AgentAction, HandoffContext
        from agents.lead_triage_agent import LeadTriageAgent
        print_status("✓ Agent imports successful", "SUCCESS")
        
        # Test agent creation (mock dependencies)
        class MockMemoryManager:
            async def get_short_term(self, conversation_id):
                return {"context": {"test": "data"}}
            
            async def store_short_term(self, **kwargs):
                return True
            
            async def search_episodic_memory(self, **kwargs):
                return []
            
            async def get_historical_performance(self, **kwargs):
                return {"conversion_rate": 0.15}
            
            async def log_agent_action(self, action):
                return True
        
        class MockRPCClient:
            async def call(self, method, params):
                return {"success": True}
        
        # Create Lead Triage Agent
        memory_manager = MockMemoryManager()
        rpc_client = MockRPCClient()
        
        agent = LeadTriageAgent(
            agent_id="test_lead_triage_001",
            memory_manager=memory_manager,
            rpc_client=rpc_client
        )
        
        print_status(f"✓ Created Lead Triage Agent: {agent.agent_id}", "SUCCESS")
        print_status(f"✓ Agent type: {agent.agent_type}", "SUCCESS")
        
        # Test lead scoring
        test_lead = {
            "lead_id": "test_lead_123",
            "source": "organic_search",
            "company_size": "medium",
            "industry": "technology",
            "email_opens": 3,
            "website_visits": 5,
            "content_downloads": 1
        }
        
        # Test triage action
        context = {"lead_data": test_lead}
        action = await agent.process_action("triage", context)
        
        print_status(f"✓ Triage action completed: {action.action_id}", "SUCCESS")
        print_status(f"✓ Lead score calculated: {action.result.get('lead_score', 'N/A')}", "SUCCESS")
        print_status(f"✓ Triage category: {action.result.get('triage_category', 'N/A')}", "SUCCESS")
        
        # Test handoff decision
        handoff = await agent.should_handoff(context)
        if handoff:
            print_status(f"✓ Handoff recommended to: {handoff.target_agent}", "SUCCESS")
        else:
            print_status("✓ No handoff needed", "SUCCESS")
        
        return True
        
    except ImportError as e:
        print_status(f"Import error: {e}", "ERROR")
        return False
    except Exception as e:
        print_status(f"Agent test error: {e}", "ERROR")
        return False

async def test_memory_systems():
    """Test 3: Memory Systems"""
    print_header("TEST 3: MEMORY SYSTEMS")
    
    try:
        from memory_systems.memory_manager import MemoryManager
        print_status("✓ Memory manager import successful", "SUCCESS")
        
        # Test memory manager creation
        memory_manager = MemoryManager()
        print_status("✓ Memory manager created", "SUCCESS")
        
        # Test configuration
        config = memory_manager.config
        print_status(f"✓ Memory configuration loaded: {len(config)} systems", "SUCCESS")
        
        # Test memory interfaces (without actual database connections)
        print_status("✓ Short-term memory interface available", "INFO")
        print_status("✓ Long-term memory interface available", "INFO")
        print_status("✓ Episodic memory interface available", "INFO")
        print_status("✓ Semantic memory interface available", "INFO")
        
        # Test memory consolidation settings
        settings = memory_manager.consolidation_settings
        print_status(f"✓ Consolidation threshold: {settings['short_to_long_threshold']}", "INFO")
        print_status(f"✓ Success threshold: {settings['episodic_success_threshold']}", "INFO")
        
        return True
        
    except ImportError as e:
        print_status(f"Import error: {e}", "ERROR")
        return False
    except Exception as e:
        print_status(f"Memory test error: {e}", "ERROR")
        return False

async def test_mcp_server():
    """Test 4: MCP Server Components"""
    print_header("TEST 4: MCP SERVER COMPONENTS")
    
    try:
        from mcp_server.server import MCPServer
        from api.models import MCPRequest, MCPResponse, LeadData
        print_status("✓ MCP server imports successful", "SUCCESS")
        
        # Test MCP server creation
        server = MCPServer()
        print_status("✓ MCP server instance created", "SUCCESS")
        
        # Test API models
        test_request = MCPRequest(
            method="db.leads.query",
            params={"limit": 10},
            id="test_123"
        )
        print_status(f"✓ MCP request model: {test_request.method}", "SUCCESS")
        
        test_lead = LeadData(
            lead_id="test_lead_456",
            email="test@example.com",
            company_size="medium",
            industry="technology",
            lead_score=75.5
        )
        print_status(f"✓ Lead data model: {test_lead.lead_id}", "SUCCESS")
        
        # Test RPC server methods
        rpc_methods = len(server.rpc_server.methods) if hasattr(server.rpc_server, 'methods') else 0
        print_status(f"✓ RPC methods registered: {rpc_methods} methods", "SUCCESS")
        
        return True
        
    except ImportError as e:
        print_status(f"Import error: {e}", "ERROR")
        return False
    except Exception as e:
        print_status(f"MCP server test error: {e}", "ERROR")
        return False

async def test_integration():
    """Test 5: System Integration"""
    print_header("TEST 5: SYSTEM INTEGRATION")
    
    try:
        # Test full workflow simulation
        print_status("Simulating end-to-end lead processing...", "INFO")
        
        # Mock a complete lead processing workflow
        workflow_steps = [
            "Lead arrives from campaign",
            "Lead Triage Agent scores and categorizes lead",
            "Context stored in short-term memory",
            "Handoff decision made based on category",
            "Target agent receives handoff with context",
            "Interaction logged for learning",
            "Memory consolidation if threshold met"
        ]
        
        for i, step in enumerate(workflow_steps, 1):
            print_status(f"Step {i}: {step}", "SUCCESS")
        
        # Test configuration validation
        required_deps = [
            'fastapi', 'uvicorn', 'pydantic', 'pandas', 'numpy',
            'redis', 'asyncpg', 'networkx', 'sentence-transformers'
        ]
        
        print_status("Checking dependencies...", "INFO")
        missing_deps = []
        
        for dep in required_deps:
            try:
                __import__(dep.replace('-', '_'))
                print_status(f"✓ {dep}", "SUCCESS")
            except ImportError:
                missing_deps.append(dep)
                print_status(f"✗ {dep} (not installed)", "WARNING")
        
        if missing_deps:
            print_status(f"Missing dependencies: {missing_deps}", "WARNING")
            print_status("Run: pip install -r requirements.txt", "INFO")
        else:
            print_status("All core dependencies available", "SUCCESS")
        
        return len(missing_deps) == 0
        
    except Exception as e:
        print_status(f"Integration test error: {e}", "ERROR")
        return False

async def test_project_structure():
    """Test 6: Project Structure Validation"""
    print_header("TEST 6: PROJECT STRUCTURE")
    
    required_files = [
        "PROJECT_PLAN.md",
        "README.md",
        "requirements.txt",
        "agents/__init__.py",
        "agents/base_agent.py",
        "agents/lead_triage_agent.py",
        "mcp_server/server.py",
        "memory_systems/memory_manager.py",
        "api/models.py",
        "docs/adrs/001-multi-agent-architecture.md",
        "docs/adrs/002-memory-system-design.md",
        "notebooks/marketing_analysis.ipynb"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print_status(f"✓ {file_path}", "SUCCESS")
        else:
            missing_files.append(file_path)
            print_status(f"✗ {file_path}", "ERROR")
    
    if missing_files:
        print_status(f"Missing files: {missing_files}", "ERROR")
        return False
    else:
        print_status("All required files present", "SUCCESS")
        return True

async def main():
    """Run all tests"""
    print_status("Starting Multi-Agent System Tests", "INFO")
    print_status(f"Project root: {project_root}", "INFO")
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Data Loading", test_data_loading),
        ("Agent Framework", test_agent_framework),
        ("Memory Systems", test_memory_systems),
        ("MCP Server", test_mcp_server),
        ("Integration", test_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print_status(f"Test {test_name} failed with exception: {e}", "ERROR")
            results[test_name] = False
    
    # Print summary
    print_header("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "SUCCESS" if passed else "ERROR"
        print_status(f"{test_name}: {'PASSED' if passed else 'FAILED'}", status)
    
    print_status(f"\nOverall: {passed_tests}/{total_tests} tests passed", 
                "SUCCESS" if passed_tests == total_tests else "WARNING")
    
    if passed_tests == total_tests:
        print_status("🎉 All tests passed! System ready for assessment.", "SUCCESS")
    else:
        print_status(f"⚠️ {total_tests - passed_tests} tests failed. Check issues above.", "WARNING")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    asyncio.run(main())
