#!/usr/bin/env python3
"""
Multi-Agent System Demo

This script demonstrates the marketing multi-agent system in action with real data.
Shows lead processing, agent handoffs, and memory storage.

Run with: python scripts/demo_system.py
"""

import sys
import os
import asyncio
import json
import pandas as pd
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
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_agent_message(agent_type, message):
    """Print agent-specific colored messages"""
    colors = {
        "LeadTriage": Colors.BLUE,
        "Engagement": Colors.GREEN,
        "CampaignOptimization": Colors.PURPLE,
        "System": Colors.CYAN
    }
    color = colors.get(agent_type, Colors.YELLOW)
    print(f"{color}{Colors.BOLD}[{agent_type}]{Colors.END} {color}{message}{Colors.END}")

def print_header(title):
    """Print demo section header"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title:^70}{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

async def load_sample_data():
    """Load sample leads from the dataset"""
    print_header("LOADING SAMPLE DATA")
    
    try:
        data_dir = project_root / "marketing_multi_agent_dataset_v1_final"
        leads_file = data_dir / "leads.csv"
        
        if not leads_file.exists():
            print_agent_message("System", "❌ Leads data file not found!")
            return []
        
        df = pd.read_csv(leads_file)
        print_agent_message("System", f"✅ Loaded {len(df)} leads from dataset")
        
        # Get a diverse sample of leads
        sample_leads = []
        
        # Get leads from different sources and industries
        for source in ['organic_search', 'referral', 'social_media', 'paid_search']:
            source_leads = df[df['source'] == source].head(2)
            sample_leads.extend(source_leads.to_dict('records'))
        
        print_agent_message("System", f"✅ Selected {len(sample_leads)} sample leads for demo")
        return sample_leads[:5]  # Limit to 5 for demo
        
    except Exception as e:
        print_agent_message("System", f"❌ Error loading data: {e}")
        return []

async def demo_lead_triage():
    """Demonstrate Lead Triage Agent"""
    print_header("LEAD TRIAGE AGENT DEMONSTRATION")
    
    try:
        # Import and setup
        from agents.lead_triage_agent import LeadTriageAgent
        
        # Mock dependencies for demo
        class DemoMemoryManager:
            def __init__(self):
                self.stored_data = {}
            
            async def get_short_term(self, conversation_id):
                return self.stored_data.get(conversation_id, {})
            
            async def store_short_term(self, conversation_id, lead_id, context, ttl=None):
                self.stored_data[conversation_id] = {
                    "conversation_id": conversation_id,
                    "lead_id": lead_id,
                    "context": context
                }
                return True
            
            async def search_episodic_memory(self, query_context, agent_type=None):
                # Return mock similar experiences
                return [
                    {
                        "scenario": "lead_triage",
                        "outcome_score": 0.85,
                        "context": {"source": "organic_search", "industry": "technology"}
                    }
                ]
            
            async def get_historical_performance(self, context):
                # Return mock historical data
                return {"conversion_rate": 0.18}
            
            async def log_agent_action(self, action):
                print_agent_message("System", f"📝 Logged action: {action.action_type}")
                return True
        
        class DemoRPCClient:
            async def call(self, method, params):
                print_agent_message("System", f"🔗 RPC Call: {method}")
                return {"success": True}
        
        # Create agent
        memory_manager = DemoMemoryManager()
        rpc_client = DemoRPCClient()
        
        triage_agent = LeadTriageAgent(
            agent_id="demo_triage_001",
            memory_manager=memory_manager,
            rpc_client=rpc_client
        )
        
        print_agent_message("LeadTriage", "🤖 Lead Triage Agent initialized")
        
        # Load sample leads
        sample_leads = await load_sample_data()
        
        if not sample_leads:
            print_agent_message("LeadTriage", "⚠️ No sample data available, using mock data")
            sample_leads = [
                {
                    "lead_id": "demo_lead_001",
                    "source": "organic_search",
                    "company_size": "medium",
                    "industry": "technology",
                    "email_opens": 3,
                    "website_visits": 5,
                    "content_downloads": 1,
                    "demo_requests": 0,
                    "contact_form_fills": 1
                },
                {
                    "lead_id": "demo_lead_002", 
                    "source": "paid_search",
                    "company_size": "large",
                    "industry": "financial_services",
                    "email_opens": 8,
                    "website_visits": 12,
                    "content_downloads": 3,
                    "demo_requests": 1,
                    "contact_form_fills": 2
                }
            ]
        
        # Process each lead
        for i, lead_data in enumerate(sample_leads[:3], 1):  # Demo first 3 leads
            print(f"\n{Colors.BOLD}--- Processing Lead {i} ---{Colors.END}")
            
            # Display lead info
            print_agent_message("System", f"📋 Lead ID: {lead_data.get('lead_id', 'unknown')}")
            print_agent_message("System", f"📋 Source: {lead_data.get('source', 'unknown')}")
            print_agent_message("System", f"📋 Industry: {lead_data.get('industry', 'unknown')}")
            print_agent_message("System", f"📋 Company Size: {lead_data.get('company_size', 'unknown')}")
            
            # Start conversation
            conversation_id = f"conv_{lead_data.get('lead_id', 'unknown')}"
            await triage_agent.start_conversation(
                lead_id=lead_data.get('lead_id', 'unknown'),
                initial_context={"lead_source": lead_data.get('source', 'unknown')}
            )
            
            print_agent_message("LeadTriage", f"💬 Started conversation: {conversation_id}")
            
            # Process triage
            context = {"lead_data": lead_data, "conversation_id": conversation_id}
            action = await triage_agent.process_action("triage", context)
            
            # Display results
            result = action.result
            print_agent_message("LeadTriage", f"📊 Lead Score: {result.get('lead_score', 'N/A'):.1f}/100")
            print_agent_message("LeadTriage", f"🏷️ Category: {result.get('triage_category', 'N/A')}")
            
            # Check for handoff
            updated_context = context.copy()
            updated_context["lead_data"].update({
                "lead_score": result.get('lead_score'),
                "triage_category": result.get('triage_category')
            })
            
            handoff = await triage_agent.should_handoff(updated_context)
            
            if handoff:
                print_agent_message("LeadTriage", f"🔄 Handoff recommended to: {handoff.target_agent}")
                print_agent_message("LeadTriage", f"🔄 Reason: {handoff.handoff_reason}")
                
                # Simulate handoff
                if handoff.target_agent == "Engagement":
                    print_agent_message("Engagement", "✅ Handoff received - will begin engagement sequence")
                elif handoff.target_agent == "CampaignOptimization":
                    print_agent_message("CampaignOptimization", "✅ Handoff received - adding to retargeting campaign")
            else:
                print_agent_message("LeadTriage", "⏸️ No handoff needed - continuing processing")
        
        print_agent_message("LeadTriage", "✅ Demo completed successfully!")
        return True
        
    except Exception as e:
        print_agent_message("LeadTriage", f"❌ Demo error: {e}")
        return False

async def demo_data_analysis():
    """Demonstrate data analysis capabilities"""
    print_header("DATA ANALYSIS DEMONSTRATION")
    
    try:
        data_dir = project_root / "marketing_multi_agent_dataset_v1_final"
        
        # Load core datasets
        datasets = {}
        files = ['leads.csv', 'conversions.csv', 'agent_actions.csv', 'interactions.csv']
        
        for filename in files:
            filepath = data_dir / filename
            if filepath.exists():
                df = pd.read_csv(filepath)
                datasets[filename.replace('.csv', '')] = df
                print_agent_message("System", f"📊 Loaded {filename}: {df.shape[0]:,} records")
        
        if 'leads' in datasets and 'conversions' in datasets:
            leads = datasets['leads']
            conversions = datasets['conversions']
            
            # Calculate key metrics
            total_leads = len(leads)
            total_conversions = len(conversions)
            conversion_rate = (total_conversions / total_leads) * 100 if total_leads > 0 else 0
            
            print_agent_message("System", f"📈 Total Leads: {total_leads:,}")
            print_agent_message("System", f"📈 Total Conversions: {total_conversions:,}")
            print_agent_message("System", f"📈 Conversion Rate: {conversion_rate:.2f}%")
            
            # Analyze by triage category
            if 'triage_category' in leads.columns:
                triage_analysis = leads['triage_category'].value_counts()
                print_agent_message("System", "📊 Leads by Triage Category:")
                for category, count in triage_analysis.items():
                    pct = (count / total_leads) * 100
                    print_agent_message("System", f"   • {category}: {count:,} ({pct:.1f}%)")
            
            # Analyze lead scores
            if 'lead_score' in leads.columns:
                avg_score = leads['lead_score'].mean()
                max_score = leads['lead_score'].max()
                min_score = leads['lead_score'].min()
                
                print_agent_message("System", f"📊 Lead Score Analysis:")
                print_agent_message("System", f"   • Average: {avg_score:.1f}")
                print_agent_message("System", f"   • Range: {min_score:.1f} - {max_score:.1f}")
        
        if 'agent_actions' in datasets:
            actions = datasets['agent_actions']
            action_types = actions['action_type'].value_counts()
            
            print_agent_message("System", "🤖 Agent Action Analysis:")
            for action_type, count in action_types.head().items():
                print_agent_message("System", f"   • {action_type}: {count:,}")
        
        return True
        
    except Exception as e:
        print_agent_message("System", f"❌ Analysis error: {e}")
        return False

async def demo_system_capabilities():
    """Demonstrate system capabilities overview"""
    print_header("SYSTEM CAPABILITIES OVERVIEW")
    
    capabilities = [
        ("🎯 Lead Triage", "Intelligent categorization and scoring of incoming leads"),
        ("🤝 Agent Collaboration", "Seamless handoffs between specialized agents"),
        ("🧠 Adaptive Memory", "4-tier memory system for learning and adaptation"),
        ("🔧 MCP Protocol", "Secure data access via JSON-RPC 2.0"),
        ("📡 Real-time Communication", "WebSocket and HTTP transport layers"),
        ("📊 Performance Analytics", "Comprehensive monitoring and optimization"),
        ("🔒 Security", "Authentication, authorization, and audit logging"),
        ("📈 Scalability", "Designed for 10x load increase")
    ]
    
    for capability, description in capabilities:
        print_agent_message("System", f"{capability}: {description}")
    
    print_agent_message("System", "\n🎉 Ready for production deployment!")

async def main():
    """Run the complete demo"""
    print_header("MARKETING MULTI-AGENT SYSTEM DEMO")
    print_agent_message("System", "🚀 Starting comprehensive system demonstration...")
    
    demos = [
        ("System Capabilities", demo_system_capabilities),
        ("Data Analysis", demo_data_analysis), 
        ("Lead Triage Agent", demo_lead_triage)
    ]
    
    success_count = 0
    
    for demo_name, demo_func in demos:
        try:
            print_agent_message("System", f"▶️ Starting {demo_name} demo...")
            result = await demo_func()
            if result:
                success_count += 1
                print_agent_message("System", f"✅ {demo_name} demo completed successfully")
            else:
                print_agent_message("System", f"⚠️ {demo_name} demo completed with issues")
        except Exception as e:
            print_agent_message("System", f"❌ {demo_name} demo failed: {e}")
    
    # Final summary
    print_header("DEMO SUMMARY")
    print_agent_message("System", f"📊 Completed {success_count}/{len(demos)} demos successfully")
    
    if success_count == len(demos):
        print_agent_message("System", "🎉 All demos passed! System is ready for assessment.")
    else:
        print_agent_message("System", "⚠️ Some demos had issues. Check output above.")
    
    print_agent_message("System", "\n📝 Next steps:")
    print_agent_message("System", "1. Run Jupyter notebook for detailed analysis")
    print_agent_message("System", "2. Review system architecture in docs/adrs/")
    print_agent_message("System", "3. Explore agent implementations in agents/")
    print_agent_message("System", "4. Test MCP server components")

if __name__ == "__main__":
    asyncio.run(main())
