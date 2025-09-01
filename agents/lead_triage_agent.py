"""
Lead Triage Agent

Responsible for categorizing incoming marketing leads and assigning appropriate scores.
Determines lead quality and routes them to the appropriate next agent.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from dataclasses import asdict

from .base_agent import BaseAgent, AgentAction, HandoffContext


class LeadTriageAgent(BaseAgent):
    """
    Lead Triage Agent Implementation
    
    Categorizes leads into:
    - Campaign Qualified: High-value leads from campaigns
    - Cold Lead: Unqualified leads requiring nurturing
    - General Inquiry: Information requests requiring follow-up
    
    Assigns lead scores (0-100) based on:
    - Lead source quality
    - Company size and industry
    - Engagement level
    - Historical conversion patterns
    """
    
    def __init__(self, agent_id: str, memory_manager, rpc_client):
        super().__init__(
            agent_id=agent_id,
            agent_type="LeadTriage",
            memory_manager=memory_manager,
            rpc_client=rpc_client
        )
        
        # Lead scoring weights
        self.scoring_weights = {
            "source_quality": 0.3,
            "company_size": 0.25,
            "industry_fit": 0.2,
            "engagement_level": 0.15,
            "historical_performance": 0.1
        }
        
        # Triage thresholds
        self.thresholds = {
            "campaign_qualified": 70,  # Score >= 70
            "general_inquiry": 40,     # Score 40-69
            "cold_lead": 0            # Score < 40
        }
    
    async def process_action(
        self, 
        action_type: str, 
        context: Dict[str, Any]
    ) -> AgentAction:
        """
        Process lead triage actions
        
        Supported actions:
        - triage: Categorize and score a new lead
        - re_evaluate: Re-assess existing lead based on new data
        - bulk_triage: Process multiple leads
        """
        
        if action_type == "triage":
            return await self._triage_lead(context)
        elif action_type == "re_evaluate":
            return await self._re_evaluate_lead(context)
        elif action_type == "bulk_triage":
            return await self._bulk_triage(context)
        else:
            raise ValueError(f"Unsupported action type: {action_type}")
    
    async def should_handoff(
        self, 
        context: Dict[str, Any]
    ) -> Optional[HandoffContext]:
        """
        Determine if lead should be handed off to another agent
        
        Handoff logic:
        - Campaign Qualified -> Engagement Agent (immediate outreach)
        - General Inquiry -> Engagement Agent (nurturing sequence)  
        - Cold Lead -> Campaign Optimization Agent (re-targeting campaigns)
        """
        
        lead_data = context.get("lead_data", {})
        triage_category = lead_data.get("triage_category")
        lead_score = lead_data.get("lead_score", 0)
        
        if not triage_category:
            return None
        
        conversation_id = context.get("conversation_id")
        lead_id = lead_data.get("lead_id")
        
        if triage_category in ["Campaign Qualified", "General Inquiry"]:
            # Hand off to Engagement Agent
            return HandoffContext(
                conversation_id=conversation_id,
                lead_id=lead_id,
                source_agent=self.agent_type,
                target_agent="Engagement",
                context_data={
                    "lead_data": lead_data,
                    "triage_results": {
                        "category": triage_category,
                        "score": lead_score,
                        "priority": "high" if lead_score >= 70 else "medium"
                    },
                    "recommended_actions": await self._get_recommended_actions(lead_data)
                },
                handoff_reason=f"Lead triaged as {triage_category} - requires engagement",
                timestamp=datetime.now()
            )
        
        elif triage_category == "Cold Lead":
            # Hand off to Campaign Optimization Agent
            return HandoffContext(
                conversation_id=conversation_id,
                lead_id=lead_id,
                source_agent=self.agent_type,
                target_agent="CampaignOptimization",
                context_data={
                    "lead_data": lead_data,
                    "triage_results": {
                        "category": triage_category,
                        "score": lead_score,
                        "priority": "low"
                    },
                    "recommended_actions": ["retargeting_campaign", "nurture_sequence"]
                },
                handoff_reason="Cold lead - requires re-targeting and nurturing",
                timestamp=datetime.now()
            )
        
        return None
    
    async def process_lead(self, lead_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a lead for triage (convenience method for demo compatibility)
        
        Args:
            lead_data: Lead information to process
            context: Additional context
            
        Returns:
            Dictionary with triage results
        """
        try:
            # Prepare context for internal triage method
            triage_context = {
                "lead_data": lead_data,
                "conversation_id": context.get("conversation_id", f"conv_{lead_data.get('lead_id', 'unknown')}") if context else f"conv_{lead_data.get('lead_id', 'unknown')}"
            }
            
            # Perform triage
            triage_action = await self._triage_lead(triage_context)
            
            # Check for handoff
            handoff_context = await self.should_handoff(triage_context)
            
            # Convert AgentAction to dictionary format expected by demo
            result = {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "lead_id": lead_data.get("lead_id", "unknown"),
                "triage_category": triage_action.action_result.get("triage_category", "unknown"),
                "lead_score": triage_action.action_result.get("lead_score", 0),
                "confidence_score": triage_action.action_result.get("confidence_score", 0.5),
                "handoff_recommendation": {
                    "should_handoff": handoff_context is not None,
                    "target_agent": handoff_context.target_agent if handoff_context else None,
                    "reason": handoff_context.handoff_reason if handoff_context else None
                },
                "processing_time": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "error": str(e),
                "lead_id": lead_data.get("lead_id", "unknown"),
                "status": "error"
            }
    
    async def handle_handoff(self, lead_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle lead handoff (triage agent typically doesn't receive handoffs)
        
        Args:
            lead_data: Lead information
            context: Handoff context
            
        Returns:
            Handoff response
        """
        return {
            "handoff_accepted": False,
            "reason": "Lead Triage Agent does not accept handoffs - it initiates the process",
            "suggested_action": "Process lead directly with process_lead method"
        }
    
    async def _triage_lead(self, context: Dict[str, Any]) -> AgentAction:
        """Perform lead triage and scoring"""
        lead_data = context.get("lead_data", {})
        
        # Calculate lead score
        lead_score = await self._calculate_lead_score(lead_data)
        
        # Determine triage category
        triage_category = self._determine_triage_category(lead_score)
        
        # Get historical context for similar leads
        similar_experiences = await self.get_similar_experiences({
            "source": lead_data.get("source"),
            "industry": lead_data.get("industry"),
            "company_size": lead_data.get("company_size")
        })
        
        # Update lead data with triage results
        triage_results = {
            "lead_score": lead_score,
            "triage_category": triage_category,
            "triage_timestamp": datetime.now().isoformat(),
            "triage_agent": self.agent_id,
            "confidence_score": await self._calculate_confidence(lead_data, similar_experiences),
            "scoring_breakdown": await self._get_scoring_breakdown(lead_data)
        }
        
        # Store results
        updated_context = {
            **context,
            "lead_data": {**lead_data, **triage_results}
        }
        
        # Log action
        action = AgentAction(
            action_id=f"triage_{lead_data.get('lead_id', 'unknown')}",
            agent_type=self.agent_type,
            action_type="triage",
            timestamp=datetime.now(),
            context=updated_context,
            result={
                "success": True,
                "triage_category": triage_category,
                "lead_score": lead_score,
                "next_action": "handoff_to_engagement" if triage_category != "Cold Lead" else "handoff_to_optimization"
            }
        )
        
        # Learn from this triage for future improvements
        await self.learn_from_interaction(
            interaction_data={
                "scenario": "lead_triage",
                "actions": ["score_calculation", "category_assignment"],
                "context": lead_data
            },
            outcome={
                "success": True,
                "score": lead_score / 100.0,  # Normalize to 0-1
                "notes": f"Lead triaged as {triage_category}"
            }
        )
        
        return action
    
    async def _calculate_lead_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate numeric lead score (0-100) based on various factors"""
        
        # Source quality scoring
        source_score = self._score_source_quality(lead_data.get("source", ""))
        
        # Company size scoring
        company_score = self._score_company_size(lead_data.get("company_size", ""))
        
        # Industry fit scoring
        industry_score = self._score_industry_fit(lead_data.get("industry", ""))
        
        # Engagement level scoring
        engagement_score = await self._score_engagement_level(lead_data)
        
        # Historical performance scoring
        historical_score = await self._score_historical_performance(lead_data)
        
        # Weighted total
        total_score = (
            source_score * self.scoring_weights["source_quality"] +
            company_score * self.scoring_weights["company_size"] +
            industry_score * self.scoring_weights["industry_fit"] +
            engagement_score * self.scoring_weights["engagement_level"] +
            historical_score * self.scoring_weights["historical_performance"]
        )
        
        return min(100, max(0, total_score))
    
    def _score_source_quality(self, source: str) -> float:
        """Score lead source quality (0-100)"""
        source_scores = {
            "organic_search": 90,
            "referral": 85,
            "content_marketing": 80,
            "social_media": 70,
            "paid_search": 65,
            "display_ads": 50,
            "cold_outreach": 40,
            "purchased_list": 20,
            "unknown": 30
        }
        return source_scores.get(source.lower(), 30)
    
    def _score_company_size(self, company_size: str) -> float:
        """Score based on company size (0-100)"""
        size_scores = {
            "enterprise": 95,
            "large": 85,
            "medium": 75,
            "small": 60,
            "startup": 45,
            "unknown": 50
        }
        return size_scores.get(company_size.lower(), 50)
    
    def _score_industry_fit(self, industry: str) -> float:
        """Score based on industry fit with our solution (0-100)"""
        # This would be customized based on your target industries
        industry_scores = {
            "technology": 90,
            "financial_services": 85,
            "healthcare": 80,
            "retail": 75,
            "manufacturing": 70,
            "education": 65,
            "government": 40,
            "non_profit": 30,
            "unknown": 50
        }
        return industry_scores.get(industry.lower(), 50)
    
    async def _score_engagement_level(self, lead_data: Dict[str, Any]) -> float:
        """Score based on engagement indicators (0-100)"""
        engagement_indicators = {
            "email_opens": lead_data.get("email_opens", 0),
            "website_visits": lead_data.get("website_visits", 0),
            "content_downloads": lead_data.get("content_downloads", 0),
            "demo_requests": lead_data.get("demo_requests", 0),
            "contact_form_fills": lead_data.get("contact_form_fills", 0)
        }
        
        # Calculate engagement score based on activity
        base_score = 0
        
        # Email engagement
        if engagement_indicators["email_opens"] > 5:
            base_score += 20
        elif engagement_indicators["email_opens"] > 0:
            base_score += 10
        
        # Website engagement
        if engagement_indicators["website_visits"] > 3:
            base_score += 25
        elif engagement_indicators["website_visits"] > 0:
            base_score += 15
        
        # Content engagement
        if engagement_indicators["content_downloads"] > 0:
            base_score += 20
        
        # High-intent actions
        if engagement_indicators["demo_requests"] > 0:
            base_score += 30
        
        if engagement_indicators["contact_form_fills"] > 0:
            base_score += 25
        
        return min(100, base_score)
    
    async def _score_historical_performance(self, lead_data: Dict[str, Any]) -> float:
        """Score based on historical performance of similar leads"""
        # Retrieve historical data for similar leads
        similar_leads_context = {
            "source": lead_data.get("source"),
            "industry": lead_data.get("industry"),
            "company_size": lead_data.get("company_size")
        }
        
        # Query historical conversion rates from memory
        historical_data = await self.memory_manager.get_historical_performance(
            context=similar_leads_context
        )
        
        if historical_data:
            conversion_rate = historical_data.get("conversion_rate", 0.1)
            return conversion_rate * 100  # Convert to 0-100 scale
        
        return 50  # Default score if no historical data
    
    def _determine_triage_category(self, lead_score: float) -> str:
        """Determine triage category based on score"""
        if lead_score >= self.thresholds["campaign_qualified"]:
            return "Campaign Qualified"
        elif lead_score >= self.thresholds["general_inquiry"]:
            return "General Inquiry"
        else:
            return "Cold Lead"
    
    async def _calculate_confidence(
        self, 
        lead_data: Dict[str, Any], 
        similar_experiences: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in triage decision (0-1)"""
        if not similar_experiences:
            return 0.5  # Medium confidence with no historical data
        
        # Higher confidence with more similar experiences
        experience_count = len(similar_experiences)
        
        # Calculate average outcome score of similar experiences
        avg_outcome = sum(exp.get("outcome_score", 0.5) for exp in similar_experiences) / experience_count
        
        # Confidence increases with more data and better outcomes
        confidence = min(0.95, 0.3 + (experience_count * 0.1) + (avg_outcome * 0.3))
        
        return confidence
    
    async def _get_scoring_breakdown(self, lead_data: Dict[str, Any]) -> Dict[str, float]:
        """Get detailed scoring breakdown for transparency"""
        return {
            "source_quality": self._score_source_quality(lead_data.get("source", "")),
            "company_size": self._score_company_size(lead_data.get("company_size", "")),
            "industry_fit": self._score_industry_fit(lead_data.get("industry", "")),
            "engagement_level": await self._score_engagement_level(lead_data),
            "historical_performance": await self._score_historical_performance(lead_data)
        }
    
    async def _get_recommended_actions(self, lead_data: Dict[str, Any]) -> List[str]:
        """Get recommended next actions based on lead profile"""
        actions = []
        
        triage_category = lead_data.get("triage_category")
        lead_score = lead_data.get("lead_score", 0)
        
        if triage_category == "Campaign Qualified":
            actions.extend([
                "immediate_personal_outreach",
                "schedule_demo",
                "send_case_studies",
                "assign_sales_rep"
            ])
        elif triage_category == "General Inquiry":
            actions.extend([
                "send_welcome_email",
                "educational_content_series",
                "schedule_discovery_call",
                "add_to_nurture_sequence"
            ])
        else:  # Cold Lead
            actions.extend([
                "add_to_retargeting_campaign",
                "long_term_nurture_sequence",
                "market_research_survey",
                "re_engage_after_3_months"
            ])
        
        return actions
    
    async def _re_evaluate_lead(self, context: Dict[str, Any]) -> AgentAction:
        """Re-evaluate existing lead with new data"""
        # Similar to triage but updates existing lead
        return await self._triage_lead(context)
    
    async def _bulk_triage(self, context: Dict[str, Any]) -> AgentAction:
        """Process multiple leads in batch"""
        leads_data = context.get("leads_data", [])
        results = []
        
        for lead_data in leads_data:
            lead_context = {"lead_data": lead_data}
            result = await self._triage_lead(lead_context)
            results.append(result.result)
        
        return AgentAction(
            action_id=f"bulk_triage_{len(leads_data)}",
            agent_type=self.agent_type,
            action_type="bulk_triage",
            timestamp=datetime.now(),
            context=context,
            result={
                "success": True,
                "processed_count": len(leads_data),
                "results": results
            }
        )
