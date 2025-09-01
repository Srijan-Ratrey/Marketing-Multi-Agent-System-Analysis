"""
Engagement Agent Implementation

The Engagement Agent handles lead nurturing, communication optimization,
and relationship building based on lead behavior and preferences.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class EngagementAgent(BaseAgent):
    """
    Engagement Agent for Lead Nurturing and Communication Optimization
    
    Responsibilities:
    - Personalize communication strategies
    - Track engagement patterns
    - Optimize messaging timing and content
    - Nurture leads through the sales funnel
    - Handle follow-up sequences
    """
    
    def __init__(self, agent_id: str, memory_manager: Any, mcp_client: Any):
        super().__init__(agent_id, "Engagement", memory_manager, mcp_client)
        
        # Engagement strategies and configurations
        self.communication_channels = {
            "email": {"weight": 0.4, "response_rate": 0.25},
            "phone": {"weight": 0.3, "response_rate": 0.35},
            "sms": {"weight": 0.2, "response_rate": 0.15},
            "social": {"weight": 0.1, "response_rate": 0.08}
        }
        
        self.engagement_templates = {
            "welcome": {
                "subject": "Welcome to {company_name}!",
                "timing": "immediate",
                "priority": "high"
            },
            "follow_up": {
                "subject": "Following up on your interest",
                "timing": "24_hours",
                "priority": "medium"
            },
            "educational": {
                "subject": "Insights for {industry} professionals",
                "timing": "weekly",
                "priority": "low"
            },
            "promotional": {
                "subject": "Special offer just for you",
                "timing": "monthly",
                "priority": "medium"
            }
        }
        
        self.optimal_timing = {
            "email": {"hour": 10, "day": "Tuesday"},
            "phone": {"hour": 14, "day": "Wednesday"},
            "sms": {"hour": 12, "day": "Thursday"}
        }
        
    async def process_lead(self, lead_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a lead for engagement optimization
        
        Args:
            lead_data: Lead information and preferences
            context: Additional context from previous agents
            
        Returns:
            Engagement strategy and next actions
        """
        lead_id = lead_data.get("lead_id", "unknown")
        
        try:
            # Log agent action
            await self._log_action("engagement_processing", lead_id, {
                "lead_score": lead_data.get("lead_score", 0),
                "triage_category": context.get("triage_category") if context else None
            })
            
            # Analyze lead engagement history
            engagement_history = await self._analyze_engagement_history(lead_id)
            
            # Determine optimal communication strategy
            communication_strategy = await self._optimize_communication_strategy(
                lead_data, engagement_history, context
            )
            
            # Create personalized engagement plan
            engagement_plan = await self._create_engagement_plan(
                lead_data, communication_strategy, context
            )
            
            # Schedule follow-up actions
            follow_up_schedule = await self._schedule_follow_ups(
                lead_data, engagement_plan
            )
            
            # Store engagement context in memory
            await self._store_engagement_context(lead_id, {
                "strategy": communication_strategy,
                "plan": engagement_plan,
                "schedule": follow_up_schedule,
                "processed_at": datetime.now().isoformat()
            })
            
            # Determine if handoff is needed
            handoff_decision = await self._evaluate_handoff_need(
                lead_data, engagement_plan, context
            )
            
            result = {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "lead_id": lead_id,
                "engagement_strategy": communication_strategy,
                "engagement_plan": engagement_plan,
                "follow_up_schedule": follow_up_schedule,
                "handoff_recommendation": handoff_decision,
                "processing_time": datetime.now().isoformat(),
                "confidence_score": engagement_plan.get("confidence", 0.75)
            }
            
            logger.info(f"Engagement processing completed for lead {lead_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing lead {lead_id}: {e}")
            return {
                "agent_id": self.agent_id,
                "error": str(e),
                "lead_id": lead_id,
                "status": "error"
            }
    
    async def handle_handoff(self, lead_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle lead handoff from Lead Triage Agent
        
        Args:
            lead_data: Lead information
            context: Context from previous agent
            
        Returns:
            Handoff acknowledgment and initial actions
        """
        lead_id = lead_data.get("lead_id", "unknown")
        
        try:
            # Acknowledge handoff
            await self._log_action("handoff_received", lead_id, {
                "from_agent": context.get("from_agent"),
                "triage_category": context.get("triage_category"),
                "lead_score": context.get("lead_score")
            })
            
            # Process the handed-off lead
            engagement_result = await self.process_lead(lead_data, context)
            
            # Send confirmation back
            handoff_response = {
                "handoff_accepted": True,
                "receiving_agent": self.agent_id,
                "lead_id": lead_id,
                "initial_actions": engagement_result.get("engagement_plan", {}),
                "estimated_response_time": "2-4 hours",
                "priority_level": self._determine_priority(lead_data, context)
            }
            
            logger.info(f"Successfully handled handoff for lead {lead_id}")
            return handoff_response
            
        except Exception as e:
            logger.error(f"Error handling handoff for lead {lead_id}: {e}")
            return {
                "handoff_accepted": False,
                "error": str(e),
                "lead_id": lead_id
            }
    
    async def _analyze_engagement_history(self, lead_id: str) -> Dict[str, Any]:
        """Analyze historical engagement patterns for the lead"""
        try:
            # Retrieve engagement history from long-term memory
            history = await self._retrieve_memory(
                lead_id, "long_term", f"engagement_history_{lead_id}"
            )
            
            if not history:
                # Create baseline engagement profile
                return {
                    "total_interactions": 0,
                    "preferred_channel": "email",
                    "response_rate": 0.0,
                    "engagement_score": 0.5,
                    "last_contact": None,
                    "optimal_timing": self.optimal_timing["email"]
                }
            
            # Analyze patterns
            analysis = {
                "total_interactions": len(history.get("interactions", [])),
                "preferred_channel": self._identify_preferred_channel(history),
                "response_rate": self._calculate_response_rate(history),
                "engagement_score": self._calculate_engagement_score(history),
                "last_contact": history.get("last_contact"),
                "optimal_timing": self._find_optimal_timing(history)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing engagement history: {e}")
            return {"error": str(e), "default_strategy": True}
    
    async def _optimize_communication_strategy(
        self, 
        lead_data: Dict[str, Any], 
        engagement_history: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Optimize communication strategy based on lead profile and history"""
        
        # Base strategy on triage category
        triage_category = context.get("triage_category", "medium") if context else "medium"
        lead_score = lead_data.get("lead_score", 50)
        
        # Determine communication urgency
        urgency = "high" if lead_score > 80 else "medium" if lead_score > 50 else "low"
        
        # Select optimal channel
        preferred_channel = engagement_history.get("preferred_channel", "email")
        if engagement_history.get("response_rate", 0) < 0.1:
            # Low response rate - try different channel
            channels = list(self.communication_channels.keys())
            preferred_channel = random.choice([c for c in channels if c != preferred_channel])
        
        # Determine message type based on category
        message_types = {
            "hot": ["welcome", "follow_up"],
            "warm": ["educational", "follow_up"],
            "cold": ["educational"],
            "nurture": ["educational", "promotional"]
        }
        
        strategy = {
            "primary_channel": preferred_channel,
            "backup_channel": "phone" if preferred_channel != "phone" else "email",
            "message_types": message_types.get(triage_category, ["educational"]),
            "urgency": urgency,
            "frequency": self._determine_frequency(urgency, engagement_history),
            "personalization_level": "high" if lead_score > 70 else "medium",
            "timing": engagement_history.get("optimal_timing", self.optimal_timing[preferred_channel])
        }
        
        return strategy
    
    async def _create_engagement_plan(
        self, 
        lead_data: Dict[str, Any], 
        strategy: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create detailed engagement plan"""
        
        lead_id = lead_data.get("lead_id", "unknown")
        company = lead_data.get("company", "Unknown Company")
        industry = lead_data.get("industry", "General")
        
        # Create sequence of engagement actions
        actions = []
        
        # Immediate welcome/acknowledgment
        if strategy["urgency"] == "high":
            actions.append({
                "type": "immediate_contact",
                "channel": strategy["primary_channel"],
                "message_type": "welcome",
                "timing": "within_1_hour",
                "priority": "high",
                "personalized_content": f"Thank you for your interest, {lead_data.get('name', 'there')}!"
            })
        
        # Follow-up sequence
        for i, msg_type in enumerate(strategy["message_types"]):
            delay_hours = (i + 1) * 24 if strategy["urgency"] == "low" else (i + 1) * 4
            
            actions.append({
                "type": "scheduled_follow_up",
                "channel": strategy["primary_channel"],
                "message_type": msg_type,
                "timing": f"in_{delay_hours}_hours",
                "priority": strategy["urgency"],
                "content_focus": self._get_content_focus(msg_type, industry)
            })
        
        # Backup channel attempt if no response
        actions.append({
            "type": "backup_contact",
            "channel": strategy["backup_channel"],
            "message_type": "follow_up",
            "timing": "if_no_response_48_hours",
            "priority": "medium",
            "trigger": "no_engagement"
        })
        
        plan = {
            "lead_id": lead_id,
            "total_actions": len(actions),
            "actions": actions,
            "expected_duration": "7_days",
            "success_metrics": {
                "response_rate_target": 0.3,
                "engagement_score_target": 0.7,
                "conversion_probability": self._estimate_conversion_probability(lead_data, strategy)
            },
            "confidence": 0.75 + (lead_data.get("lead_score", 50) / 200)  # Higher score = higher confidence
        }
        
        return plan
    
    async def _schedule_follow_ups(
        self, 
        lead_data: Dict[str, Any], 
        engagement_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Schedule follow-up actions"""
        
        schedule = {
            "lead_id": lead_data.get("lead_id"),
            "scheduled_actions": [],
            "next_action_time": None,
            "total_scheduled": 0
        }
        
        base_time = datetime.now()
        
        for action in engagement_plan.get("actions", []):
            # Parse timing
            timing = action.get("timing", "in_24_hours")
            
            if "within_1_hour" in timing:
                scheduled_time = base_time + timedelta(hours=1)
            elif "in_" in timing and "_hours" in timing:
                hours = int(timing.split("_")[1])
                scheduled_time = base_time + timedelta(hours=hours)
            elif "if_no_response" in timing:
                hours = int(timing.split("_")[-2])
                scheduled_time = base_time + timedelta(hours=hours)
            else:
                scheduled_time = base_time + timedelta(hours=24)
            
            scheduled_action = {
                **action,
                "scheduled_time": scheduled_time.isoformat(),
                "status": "scheduled"
            }
            
            schedule["scheduled_actions"].append(scheduled_action)
        
        if schedule["scheduled_actions"]:
            schedule["next_action_time"] = schedule["scheduled_actions"][0]["scheduled_time"]
            schedule["total_scheduled"] = len(schedule["scheduled_actions"])
        
        return schedule
    
    async def _evaluate_handoff_need(
        self, 
        lead_data: Dict[str, Any], 
        engagement_plan: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate if lead should be handed off to Campaign Optimization Agent"""
        
        lead_score = lead_data.get("lead_score", 50)
        conversion_probability = engagement_plan["success_metrics"]["conversion_probability"]
        
        # High-value leads with good conversion probability go to Campaign Optimization
        should_handoff = (
            lead_score > 75 and 
            conversion_probability > 0.6 and
            engagement_plan.get("confidence", 0) > 0.8
        )
        
        return {
            "should_handoff": should_handoff,
            "target_agent": "campaign_optimization" if should_handoff else None,
            "reason": "high_conversion_potential" if should_handoff else "continue_nurturing",
            "confidence": 0.85 if should_handoff else 0.65,
            "estimated_timing": "after_initial_engagement" if should_handoff else None
        }
    
    async def _store_engagement_context(self, lead_id: str, context: Dict[str, Any]):
        """Store engagement context in memory"""
        try:
            # Store in long-term memory for future reference
            await self._store_memory(lead_id, "long_term", {
                "type": "engagement_context",
                "lead_id": lead_id,
                "context": context,
                "agent": self.agent_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # Store current state in short-term memory
            await self._store_memory(lead_id, "short_term", {
                "current_strategy": context.get("strategy"),
                "next_action": context.get("schedule", {}).get("next_action_time"),
                "agent": self.agent_id
            })
            
        except Exception as e:
            logger.error(f"Error storing engagement context: {e}")
    
    def _identify_preferred_channel(self, history: Dict[str, Any]) -> str:
        """Identify preferred communication channel from history"""
        channel_responses = {}
        
        for interaction in history.get("interactions", []):
            channel = interaction.get("channel", "email")
            responded = interaction.get("responded", False)
            
            if channel not in channel_responses:
                channel_responses[channel] = {"total": 0, "responses": 0}
            
            channel_responses[channel]["total"] += 1
            if responded:
                channel_responses[channel]["responses"] += 1
        
        # Calculate response rates and return best channel
        best_channel = "email"  # default
        best_rate = 0
        
        for channel, stats in channel_responses.items():
            if stats["total"] > 0:
                rate = stats["responses"] / stats["total"]
                if rate > best_rate:
                    best_rate = rate
                    best_channel = channel
        
        return best_channel
    
    def _calculate_response_rate(self, history: Dict[str, Any]) -> float:
        """Calculate overall response rate"""
        interactions = history.get("interactions", [])
        if not interactions:
            return 0.0
        
        responses = sum(1 for i in interactions if i.get("responded", False))
        return responses / len(interactions)
    
    def _calculate_engagement_score(self, history: Dict[str, Any]) -> float:
        """Calculate engagement score based on history"""
        if not history.get("interactions"):
            return 0.5  # neutral
        
        response_rate = self._calculate_response_rate(history)
        recency_factor = self._calculate_recency_factor(history)
        frequency_factor = len(history["interactions"]) / 10  # normalize
        
        score = (response_rate * 0.5) + (recency_factor * 0.3) + (min(frequency_factor, 1.0) * 0.2)
        return min(score, 1.0)
    
    def _calculate_recency_factor(self, history: Dict[str, Any]) -> float:
        """Calculate recency factor for engagement scoring"""
        last_contact = history.get("last_contact")
        if not last_contact:
            return 0.0
        
        try:
            last_date = datetime.fromisoformat(last_contact.replace('Z', '+00:00'))
            days_since = (datetime.now() - last_date.replace(tzinfo=None)).days
            
            # More recent = higher score
            if days_since <= 7:
                return 1.0
            elif days_since <= 30:
                return 0.7
            elif days_since <= 90:
                return 0.4
            else:
                return 0.1
        except:
            return 0.0
    
    def _find_optimal_timing(self, history: Dict[str, Any]) -> Dict[str, Any]:
        """Find optimal timing based on response patterns"""
        # Analyze when responses occurred
        response_hours = []
        response_days = []
        
        for interaction in history.get("interactions", []):
            if interaction.get("responded", False):
                timestamp = interaction.get("timestamp")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        response_hours.append(dt.hour)
                        response_days.append(dt.strftime('%A'))
                    except:
                        continue
        
        # Find most common hour and day
        if response_hours:
            optimal_hour = max(set(response_hours), key=response_hours.count)
        else:
            optimal_hour = 10  # default
        
        if response_days:
            optimal_day = max(set(response_days), key=response_days.count)
        else:
            optimal_day = "Tuesday"  # default
        
        return {"hour": optimal_hour, "day": optimal_day}
    
    def _determine_frequency(self, urgency: str, engagement_history: Dict[str, Any]) -> str:
        """Determine contact frequency based on urgency and history"""
        response_rate = engagement_history.get("response_rate", 0.0)
        
        if urgency == "high":
            return "daily" if response_rate > 0.3 else "every_2_days"
        elif urgency == "medium":
            return "weekly" if response_rate > 0.2 else "bi_weekly"
        else:
            return "monthly"
    
    def _get_content_focus(self, message_type: str, industry: str) -> str:
        """Get content focus for message type and industry"""
        content_map = {
            "welcome": f"Introduction to our {industry} solutions",
            "follow_up": f"Addressing {industry} challenges",
            "educational": f"Best practices in {industry}",
            "promotional": f"Special offers for {industry} professionals"
        }
        
        return content_map.get(message_type, "General business solutions")
    
    def _estimate_conversion_probability(
        self, 
        lead_data: Dict[str, Any], 
        strategy: Dict[str, Any]
    ) -> float:
        """Estimate conversion probability based on lead and strategy"""
        base_probability = lead_data.get("lead_score", 50) / 100
        
        # Adjust based on strategy effectiveness
        channel_weight = self.communication_channels.get(
            strategy["primary_channel"], {}
        ).get("response_rate", 0.2)
        
        urgency_multiplier = {
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8
        }.get(strategy["urgency"], 1.0)
        
        probability = base_probability * channel_weight * urgency_multiplier
        return min(probability, 0.95)  # Cap at 95%
    
    def _determine_priority(self, lead_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Determine priority level for handoff"""
        lead_score = lead_data.get("lead_score", 50)
        triage_category = context.get("triage_category", "medium")
        
        if lead_score > 80 or triage_category == "hot":
            return "high"
        elif lead_score > 60 or triage_category == "warm":
            return "medium"
        else:
            return "low"
    
    # Required abstract methods from BaseAgent
    async def process_action(self, action_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a generic action (delegates to process_lead for leads)"""
        if action_data.get("action_type") == "process_lead":
            return await self.process_lead(action_data.get("lead_data", {}), context)
        else:
            return {"error": "Unknown action type", "action_type": action_data.get("action_type")}
    
    async def should_handoff(self, lead_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> bool:
        """Determine if lead should be handed off to another agent"""
        handoff_decision = await self._evaluate_handoff_need(lead_data, {}, context)
        return handoff_decision.get("should_handoff", False)
