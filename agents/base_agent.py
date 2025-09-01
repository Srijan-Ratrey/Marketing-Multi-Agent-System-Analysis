"""
Base Agent Class

Abstract base class for all marketing agents providing common functionality
for memory access, communication, and handoff protocols.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import json
import asyncio
from dataclasses import dataclass, asdict

from memory_systems.memory_manager import MemoryManager
from transport.json_rpc_client import JSONRPCClient


@dataclass
class AgentAction:
    """Represents an action taken by an agent"""
    action_id: str
    agent_type: str
    action_type: str
    timestamp: datetime
    context: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    handoff_target: Optional[str] = None


@dataclass
class HandoffContext:
    """Context preserved during agent handoffs"""
    conversation_id: str
    lead_id: str
    source_agent: str
    target_agent: str
    context_data: Dict[str, Any]
    handoff_reason: str
    timestamp: datetime


class BaseAgent(ABC):
    """
    Abstract base class for all marketing agents
    
    Provides common functionality for:
    - Memory access and management
    - Inter-agent communication via JSON-RPC
    - Handoff protocols
    - Action logging and context preservation
    """
    
    def __init__(
        self, 
        agent_id: str,
        agent_type: str,
        memory_manager: MemoryManager,
        rpc_client: JSONRPCClient
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.memory_manager = memory_manager
        self.rpc_client = rpc_client
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        
    @abstractmethod
    async def process_action(
        self, 
        action_type: str, 
        context: Dict[str, Any]
    ) -> AgentAction:
        """
        Process a specific action based on agent type
        
        Args:
            action_type: Type of action to perform
            context: Context data for the action
            
        Returns:
            AgentAction with results
        """
        pass
    
    @abstractmethod
    async def should_handoff(
        self, 
        context: Dict[str, Any]
    ) -> Optional[HandoffContext]:
        """
        Determine if current task should be handed off to another agent
        
        Args:
            context: Current conversation context
            
        Returns:
            HandoffContext if handoff needed, None otherwise
        """
        pass
    
    async def start_conversation(
        self, 
        lead_id: str, 
        initial_context: Dict[str, Any]
    ) -> str:
        """Start a new conversation with a lead"""
        conversation_id = str(uuid.uuid4())
        
        # Store in short-term memory
        await self.memory_manager.store_short_term(
            conversation_id=conversation_id,
            lead_id=lead_id,
            context=initial_context
        )
        
        # Track active conversation
        self.active_conversations[conversation_id] = {
            "lead_id": lead_id,
            "started_at": datetime.now(),
            "context": initial_context
        }
        
        return conversation_id
    
    async def update_conversation_context(
        self, 
        conversation_id: str, 
        updates: Dict[str, Any]
    ) -> None:
        """Update conversation context in memory"""
        if conversation_id in self.active_conversations:
            self.active_conversations[conversation_id]["context"].update(updates)
            
            # Update short-term memory
            await self.memory_manager.update_short_term(
                conversation_id=conversation_id,
                context_updates=updates
            )
    
    async def handoff_to_agent(
        self, 
        target_agent_type: str,
        handoff_context: HandoffContext
    ) -> bool:
        """
        Hand off conversation to another agent
        
        Args:
            target_agent_type: Type of agent to hand off to
            handoff_context: Context to preserve during handoff
            
        Returns:
            True if handoff successful, False otherwise
        """
        try:
            # Store handoff context in memory
            await self.memory_manager.store_handoff_context(handoff_context)
            
            # Notify target agent via JSON-RPC
            handoff_data = asdict(handoff_context)
            
            response = await self.rpc_client.call(
                method=f"{target_agent_type}.receive_handoff",
                params=handoff_data
            )
            
            if response.get("success"):
                # Remove from active conversations
                if handoff_context.conversation_id in self.active_conversations:
                    del self.active_conversations[handoff_context.conversation_id]
                
                # Log successful handoff
                await self._log_action(
                    action_type="handoff",
                    context={
                        "target_agent": target_agent_type,
                        "conversation_id": handoff_context.conversation_id,
                        "handoff_reason": handoff_context.handoff_reason
                    },
                    result={"success": True}
                )
                
                return True
            
            return False
            
        except Exception as e:
            # Log failed handoff
            await self._log_action(
                action_type="handoff_failed",
                context={
                    "target_agent": target_agent_type,
                    "conversation_id": handoff_context.conversation_id,
                    "error": str(e)
                },
                result={"success": False, "error": str(e)}
            )
            return False
    
    async def receive_handoff(self, handoff_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receive a handoff from another agent
        
        Args:
            handoff_data: Handoff context data
            
        Returns:
            Response indicating success/failure
        """
        try:
            handoff_context = HandoffContext(**handoff_data)
            
            # Add to active conversations
            self.active_conversations[handoff_context.conversation_id] = {
                "lead_id": handoff_context.lead_id,
                "started_at": datetime.now(),
                "context": handoff_context.context_data,
                "received_from": handoff_context.source_agent
            }
            
            # Log handoff received
            await self._log_action(
                action_type="handoff_received",
                context={
                    "source_agent": handoff_context.source_agent,
                    "conversation_id": handoff_context.conversation_id
                },
                result={"success": True}
            )
            
            return {"success": True, "message": "Handoff received successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def escalate_to_manager(
        self, 
        conversation_id: str, 
        escalation_reason: str,
        context: Dict[str, Any]
    ) -> bool:
        """Escalate complex decisions to human managers"""
        try:
            # Store escalation in memory
            escalation_data = {
                "conversation_id": conversation_id,
                "agent_type": self.agent_type,
                "escalation_reason": escalation_reason,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "status": "pending"
            }
            
            # Send to manager queue via JSON-RPC
            response = await self.rpc_client.call(
                method="manager.receive_escalation",
                params=escalation_data
            )
            
            # Log escalation
            await self._log_action(
                action_type="escalate",
                context={
                    "conversation_id": conversation_id,
                    "escalation_reason": escalation_reason
                },
                result={"success": response.get("success", False)}
            )
            
            return response.get("success", False)
            
        except Exception as e:
            await self._log_action(
                action_type="escalation_failed",
                context={
                    "conversation_id": conversation_id,
                    "error": str(e)
                },
                result={"success": False, "error": str(e)}
            )
            return False
    
    async def learn_from_interaction(
        self, 
        interaction_data: Dict[str, Any],
        outcome: Dict[str, Any]
    ) -> None:
        """
        Learn from successful interactions and store in episodic memory
        
        Args:
            interaction_data: Details of the interaction
            outcome: Result/outcome of the interaction
        """
        # Only store successful interactions for learning
        if outcome.get("success", False):
            episode = {
                "agent_type": self.agent_type,
                "scenario": interaction_data.get("scenario", "unknown"),
                "action_sequence": interaction_data.get("actions", []),
                "outcome_score": outcome.get("score", 0.0),
                "context": interaction_data.get("context", {}),
                "timestamp": datetime.now().isoformat(),
                "notes": outcome.get("notes", "")
            }
            
            await self.memory_manager.store_episodic_memory(episode)
    
    async def get_similar_experiences(
        self, 
        current_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve similar past experiences from episodic memory"""
        return await self.memory_manager.search_episodic_memory(
            query_context=current_context,
            agent_type=self.agent_type
        )
    
    async def _log_action(
        self, 
        action_type: str, 
        context: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log agent action for analysis and debugging"""
        action = AgentAction(
            action_id=str(uuid.uuid4()),
            agent_type=self.agent_type,
            action_type=action_type,
            timestamp=datetime.now(),
            context=context,
            result=result
        )
        
        # Store in long-term memory for analysis
        await self.memory_manager.log_agent_action(action)
    
    async def get_conversation_context(
        self, 
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve full conversation context from memory"""
        # Try short-term memory first
        context = await self.memory_manager.get_short_term(conversation_id)
        
        if not context and conversation_id in self.active_conversations:
            # Fallback to local memory
            context = self.active_conversations[conversation_id]["context"]
        
        return context
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Return basic agent information"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "active_conversations": len(self.active_conversations),
            "status": "active"
        }
