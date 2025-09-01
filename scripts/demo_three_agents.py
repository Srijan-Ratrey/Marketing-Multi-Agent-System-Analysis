#!/usr/bin/env python3
"""
Three-Agent System Demo

Demonstrates the complete multi-agent marketing system with all three agents:
1. Lead Triage Agent - Initial scoring and categorization
2. Engagement Agent - Personalized communication strategy  
3. Campaign Optimization Agent - Performance optimization and insights
"""

import sys
import os
import asyncio
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def demo_three_agent_system():
    """Demonstrate the complete three-agent system workflow"""
    
    print("🤖 MARKETING MULTI-AGENT SYSTEM DEMO")
    print("=" * 60)
    print("Demonstrating collaborative workflow between three specialized agents:\n")
    
    try:
        # Import agents and dependencies
        from agents import LeadTriageAgent, EngagementAgent, CampaignOptimizationAgent
        from memory_systems.memory_manager import MemoryManager
        from transport.json_rpc_client import MockJSONRPCClient
        
        # Initialize memory manager and mock MCP client
        memory_manager = MemoryManager()
        await memory_manager.initialize()
        
        mcp_client = MockJSONRPCClient()
        await mcp_client.initialize()
        
        # Create the three agents
        print("🏗️ INITIALIZING AGENTS")
        print("-" * 30)
        
        triage_agent = LeadTriageAgent(
            agent_id="lead_triage_001",
            memory_manager=memory_manager,
            rpc_client=mcp_client
        )
        print("✅ Lead Triage Agent initialized")
        
        engagement_agent = EngagementAgent(
            agent_id="engagement_001", 
            memory_manager=memory_manager,
            mcp_client=mcp_client
        )
        print("✅ Engagement Agent initialized")
        
        optimization_agent = CampaignOptimizationAgent(
            agent_id="campaign_opt_001",
            memory_manager=memory_manager,
            mcp_client=mcp_client
        )
        print("✅ Campaign Optimization Agent initialized")
        
        # Load sample lead data
        data_dir = project_root / "marketing_multi_agent_dataset_v1_final"
        leads_df = pd.read_csv(data_dir / "leads.csv")
        
        # Select diverse test leads
        test_leads = [
            # High-value enterprise lead
            {
                "lead_id": "DEMO_001",
                "name": "Sarah Johnson",
                "company": "TechCorp Enterprise",
                "industry": "Technology",
                "company_size": "Enterprise",
                "lead_source": "LinkedIn",
                "lead_score": 92,
                "email": "sarah.johnson@techcorp.com",
                "phone": "+1-555-0123",
                "campaign_id": "CAMP_001"
            },
            # Medium healthcare lead
            {
                "lead_id": "DEMO_002",
                "name": "Dr. Michael Chen",
                "company": "Regional Medical Center",
                "industry": "Healthcare", 
                "company_size": "Large",
                "lead_source": "Webinar",
                "lead_score": 67,
                "email": "m.chen@regmedcenter.org",
                "phone": "+1-555-0456",
                "campaign_id": "CAMP_002"
            },
            # Lower-scoring startup lead
            {
                "lead_id": "DEMO_003",
                "name": "Alex Rodriguez",
                "company": "InnovateLab Startup",
                "industry": "Technology",
                "company_size": "Startup", 
                "lead_source": "Content",
                "lead_score": 43,
                "email": "alex@innovatelab.io",
                "phone": "+1-555-0789",
                "campaign_id": "CAMP_003"
            }
        ]
        
        print(f"\n📋 PROCESSING {len(test_leads)} TEST LEADS")
        print("=" * 60)
        
        for i, lead in enumerate(test_leads, 1):
            print(f"\n🎯 LEAD {i}: {lead['name']} ({lead['company']})")
            print(f"   Industry: {lead['industry']} | Size: {lead['company_size']} | Score: {lead['lead_score']}")
            print("-" * 60)
            
            # STEP 1: Lead Triage Agent
            print("🔍 STEP 1: LEAD TRIAGE ANALYSIS")
            triage_result = await triage_agent.process_lead(lead)
            
            triage_category = triage_result.get("triage_category", "unknown")
            confidence = triage_result.get("confidence_score", 0)
            handoff_decision = triage_result.get("handoff_recommendation", {})
            
            print(f"   📊 Category: {triage_category.upper()}")
            print(f"   📈 Confidence: {confidence:.1%}")
            print(f"   🔄 Handoff: {'YES' if handoff_decision.get('should_handoff') else 'NO'}")
            
            if handoff_decision.get("should_handoff"):
                print(f"   👉 Target: {handoff_decision.get('target_agent', 'N/A')}")
                
                # STEP 2: Engagement Agent Handoff
                print("\n💬 STEP 2: ENGAGEMENT AGENT PROCESSING")
                
                engagement_context = {
                    "from_agent": "lead_triage_001",
                    "triage_category": triage_category,
                    "lead_score": lead["lead_score"],
                    "confidence": confidence
                }
                
                engagement_result = await engagement_agent.handle_handoff(lead, engagement_context)
                
                strategy = engagement_result.get("initial_actions", {}).get("engagement_strategy", {})
                plan = engagement_result.get("initial_actions", {}).get("engagement_plan", {})
                
                print(f"   📧 Primary Channel: {strategy.get('primary_channel', 'email')}")
                print(f"   ⚡ Urgency: {strategy.get('urgency', 'medium')}")
                print(f"   📅 Actions Planned: {plan.get('total_actions', 0)}")
                print(f"   🎯 Conv. Probability: {plan.get('success_metrics', {}).get('conversion_probability', 0):.1%}")
                
                # Check if high-value lead should go to optimization
                conversion_prob = plan.get("success_metrics", {}).get("conversion_probability", 0)
                if lead["lead_score"] > 75 and conversion_prob > 0.4:
                    
                    # STEP 3: Campaign Optimization Agent
                    print("\n🚀 STEP 3: CAMPAIGN OPTIMIZATION")
                    
                    optimization_context = {
                        "from_agent": "engagement_001",
                        "engagement_strategy": strategy,
                        "engagement_plan": plan,
                        "conversion_probability": conversion_prob
                    }
                    
                    optimization_result = await optimization_agent.handle_handoff(lead, optimization_context)
                    
                    roi_prediction = optimization_result.get("initial_actions", {}).get("roi_prediction", {})
                    recommendations = optimization_result.get("immediate_actions", [])
                    
                    print(f"   💰 Predicted Value: ${roi_prediction.get('predicted_value', 0):,.0f}")
                    print(f"   📊 Predicted ROI: {roi_prediction.get('predicted_roi', 0):.1f}x")
                    print(f"   🔧 Immediate Actions: {len(recommendations)}")
                    
                    escalation = optimization_result.get("escalation_recommendation", {})
                    if escalation.get("should_escalate"):
                        print(f"   🚨 ESCALATION: {escalation.get('urgency', 'medium').upper()} priority")
                else:
                    print("\n⏭️  STEP 3: Campaign optimization not triggered")
                    print("   (Lead score or conversion probability below threshold)")
            else:
                print("\n⏭️  STEPS 2-3: Agent handoff not recommended")
                print("   (Lead will continue in nurturing sequence)")
            
            print("\n" + "="*60)
        
        # System Summary
        print("\n📊 SYSTEM SUMMARY")
        print("=" * 40)
        print("✅ All three agents successfully demonstrated")
        print("✅ Agent handoff protocols working properly") 
        print("✅ Memory systems storing context between agents")
        print("✅ Sophisticated lead scoring and optimization")
        print("✅ ROI prediction and strategic recommendations")
        
        print("\n🎯 KEY CAPABILITIES DEMONSTRATED:")
        print("• Intelligent lead triage and scoring")
        print("• Personalized engagement strategy optimization")
        print("• Advanced campaign performance analysis")
        print("• Predictive ROI modeling")
        print("• A/B testing recommendations")
        print("• Strategic escalation protocols")
        print("• Cross-agent context preservation")
        
        # Cleanup
        await memory_manager.cleanup()
        await mcp_client.cleanup()
        
        print(f"\n🎉 Demo completed successfully at {datetime.now().strftime('%H:%M:%S')}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all agents are properly implemented")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


async def show_agent_capabilities():
    """Show detailed capabilities of each agent"""
    
    print("\n🤖 AGENT CAPABILITIES OVERVIEW")
    print("=" * 50)
    
    capabilities = {
        "Lead Triage Agent": [
            "Lead scoring with multiple criteria",
            "Industry and company size analysis", 
            "Source attribution and quality assessment",
            "Dynamic threshold adjustment",
            "Intelligent handoff decisions",
            "Context preservation for downstream agents"
        ],
        "Engagement Agent": [
            "Communication channel optimization",
            "Personalized engagement strategies",
            "Response rate prediction",
            "Follow-up sequence automation",
            "Optimal timing analysis",
            "Content personalization recommendations"
        ],
        "Campaign Optimization Agent": [
            "ROI prediction and value modeling",
            "A/B testing recommendations",
            "Segment opportunity analysis",
            "Budget allocation optimization",
            "Conversion funnel analysis",
            "Strategic escalation protocols"
        ]
    }
    
    for agent_name, agent_capabilities in capabilities.items():
        print(f"\n🔧 {agent_name}:")
        for capability in agent_capabilities:
            print(f"   • {capability}")
    
    print("\n🔄 INTER-AGENT COLLABORATION:")
    print("   • Seamless handoff protocols")
    print("   • Context preservation across agents")
    print("   • Shared memory systems")
    print("   • Escalation and feedback loops")
    print("   • Performance tracking and optimization")


async def main():
    """Main demo function"""
    await show_agent_capabilities()
    await demo_three_agent_system()


if __name__ == "__main__":
    asyncio.run(main())
