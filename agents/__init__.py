"""
Multi-Agent Marketing System

This package contains the implementation of three collaborative marketing agents:
- Lead Triage Agent: Categorizes and scores incoming leads
- Engagement Agent: Manages personalized outreach and nurturing
- Campaign Optimization Agent: Monitors and optimizes campaign performance
"""

from .base_agent import BaseAgent
from .lead_triage_agent import LeadTriageAgent
from .engagement_agent import EngagementAgent
from .campaign_optimization_agent import CampaignOptimizationAgent

__all__ = [
    "BaseAgent",
    "LeadTriageAgent", 
    "EngagementAgent",
    "CampaignOptimizationAgent"
]
