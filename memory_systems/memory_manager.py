"""
Memory Manager

Manages the four-tier adaptive memory architecture:
1. Short-term memory: Current conversation contexts (Redis)
2. Long-term memory: Customer history and preferences (PostgreSQL)
3. Episodic memory: Successful problem-resolution patterns (Vector DB)
4. Semantic memory: Domain knowledge graphs (Neo4j)
"""

from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime, timedelta
import logging
import uuid

# Database connections
import redis.asyncio as redis
import asyncpg
import networkx as nx
from sentence_transformers import SentenceTransformer

from .short_term_memory import ShortTermMemory
from .long_term_memory import LongTermMemory  
from .episodic_memory import EpisodicMemory
from .semantic_memory import SemanticMemory


logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central coordinator for all memory systems
    
    Provides unified interface for agents to:
    - Store and retrieve conversation context
    - Access customer history and preferences
    - Learn from successful interaction patterns
    - Query domain knowledge graphs
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        
        # Memory subsystems
        self.short_term = ShortTermMemory(self.config.get("redis", {}))
        self.long_term = LongTermMemory(self.config.get("postgres", {}))
        self.episodic = EpisodicMemory(self.config.get("vector_db", {}))
        self.semantic = SemanticMemory(self.config.get("neo4j", {}))
        
        # Memory consolidation settings
        self.consolidation_settings = {
            "short_to_long_threshold": 5,  # Interactions before consolidation
            "episodic_success_threshold": 0.8,  # Outcome score threshold
            "semantic_relationship_threshold": 0.7  # Similarity threshold
        }
        
        self.initialized = False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for memory systems"""
        return {
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "decode_responses": True
            },
            "postgres": {
                "host": "localhost",
                "port": 5432,
                "database": "marketing_agents",
                "user": "postgres",
                "password": "password"
            },
            "vector_db": {
                "model_name": "all-MiniLM-L6-v2",
                "dimension": 384,
                "collection_name": "episodic_memory"
            },
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "password": "password"
            }
        }
    
    async def initialize(self):
        """Initialize all memory subsystems"""
        if self.initialized:
            return
        
        logger.info("Initializing memory manager...")
        
        try:
            # Initialize each memory subsystem
            await self.short_term.initialize()
            await self.long_term.initialize()
            await self.episodic.initialize()
            await self.semantic.initialize()
            
            self.initialized = True
            logger.info("Memory manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory manager: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup memory connections"""
        await self.short_term.cleanup()
        await self.long_term.cleanup()
        await self.episodic.cleanup()
        await self.semantic.cleanup()
    
    # Short-term memory methods
    async def store_short_term(
        self, 
        conversation_id: str,
        lead_id: str, 
        context: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Store conversation context in short-term memory"""
        
        memory_data = {
            "conversation_id": conversation_id,
            "lead_id": lead_id,
            "context": context,
            "last_updated": datetime.now().isoformat(),
            "interaction_count": 1
        }
        
        # Get existing data to increment interaction count
        existing = await self.short_term.get(conversation_id)
        if existing:
            memory_data["interaction_count"] = existing.get("interaction_count", 0) + 1
        
        success = await self.short_term.store(
            key=conversation_id,
            data=memory_data,
            ttl=ttl or 3600  # 1 hour default TTL
        )
        
        # Check if consolidation is needed
        if memory_data["interaction_count"] >= self.consolidation_settings["short_to_long_threshold"]:
            await self._consolidate_to_long_term(conversation_id, memory_data)
        
        return success
    
    async def get_short_term(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conversation context from short-term memory"""
        return await self.short_term.get(conversation_id)
    
    async def update_short_term(
        self, 
        conversation_id: str, 
        context_updates: Dict[str, Any]
    ) -> bool:
        """Update existing short-term memory context"""
        
        existing = await self.get_short_term(conversation_id)
        if not existing:
            return False
        
        # Merge updates
        existing["context"].update(context_updates)
        existing["last_updated"] = datetime.now().isoformat()
        existing["interaction_count"] = existing.get("interaction_count", 0) + 1
        
        return await self.short_term.store(conversation_id, existing)
    
    # Long-term memory methods
    async def store_long_term(
        self,
        lead_id: str,
        preferences: Dict[str, Any],
        interaction_history: List[Dict[str, Any]]
    ) -> bool:
        """Store customer preferences and history in long-term memory"""
        
        memory_data = {
            "lead_id": lead_id,
            "preferences": preferences,
            "interaction_history": interaction_history,
            "last_updated": datetime.now().isoformat(),
            "rfm_score": await self._calculate_rfm_score(lead_id, interaction_history)
        }
        
        return await self.long_term.store(lead_id, memory_data)
    
    async def get_long_term(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve customer data from long-term memory"""
        return await self.long_term.get(lead_id)
    
    async def get_historical_performance(
        self, 
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get historical performance data for similar contexts"""
        return await self.long_term.get_performance_data(context)
    
    # Episodic memory methods
    async def store_episodic_memory(self, episode: Dict[str, Any]) -> bool:
        """Store successful interaction pattern in episodic memory"""
        
        # Only store if outcome meets success threshold
        outcome_score = episode.get("outcome_score", 0.0)
        if outcome_score < self.consolidation_settings["episodic_success_threshold"]:
            return False
        
        episode_id = str(uuid.uuid4())
        episode["episode_id"] = episode_id
        episode["stored_at"] = datetime.now().isoformat()
        
        return await self.episodic.store(episode_id, episode)
    
    async def search_episodic_memory(
        self, 
        query_context: Dict[str, Any],
        agent_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar successful experiences"""
        
        # Create search query from context
        query_text = self._context_to_search_text(query_context)
        
        filters = {}
        if agent_type:
            filters["agent_type"] = agent_type
        
        return await self.episodic.search_similar(
            query_text=query_text,
            filters=filters,
            limit=limit
        )
    
    # Semantic memory methods
    async def store_knowledge_triple(
        self, 
        subject: str, 
        predicate: str, 
        obj: str,
        weight: float = 1.0,
        source: str = "system"
    ) -> bool:
        """Store knowledge relationship in semantic memory"""
        
        triple = {
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "weight": weight,
            "source": source,
            "created_at": datetime.now().isoformat()
        }
        
        return await self.semantic.store_triple(triple)
    
    async def query_semantic_memory(
        self, 
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query semantic knowledge graph"""
        
        return await self.semantic.query_triples(
            subject=subject,
            predicate=predicate,
            object=obj
        )
    
    async def get_related_concepts(
        self, 
        concept: str, 
        relationship_types: Optional[List[str]] = None,
        depth: int = 2
    ) -> List[Dict[str, Any]]:
        """Get concepts related to given concept"""
        
        return await self.semantic.get_related_concepts(
            concept=concept,
            relationship_types=relationship_types,
            depth=depth
        )
    
    # Agent action logging
    async def log_agent_action(self, action) -> bool:
        """Log agent action for analysis"""
        
        action_data = {
            "action_id": action.action_id,
            "agent_type": action.agent_type,
            "action_type": action.action_type,
            "timestamp": action.timestamp.isoformat(),
            "context": action.context,
            "result": action.result,
            "handoff_target": action.handoff_target
        }
        
        return await self.long_term.log_action(action_data)
    
    async def store_handoff_context(self, handoff_context) -> bool:
        """Store handoff context for analysis and debugging"""
        
        handoff_data = {
            "conversation_id": handoff_context.conversation_id,
            "lead_id": handoff_context.lead_id,
            "source_agent": handoff_context.source_agent,
            "target_agent": handoff_context.target_agent,
            "context_data": handoff_context.context_data,
            "handoff_reason": handoff_context.handoff_reason,
            "timestamp": handoff_context.timestamp.isoformat()
        }
        
        return await self.long_term.store_handoff(handoff_data)
    
    # Memory consolidation methods
    async def _consolidate_to_long_term(
        self, 
        conversation_id: str, 
        short_term_data: Dict[str, Any]
    ) -> bool:
        """Consolidate frequently accessed short-term memory to long-term"""
        
        lead_id = short_term_data.get("lead_id")
        if not lead_id:
            return False
        
        # Get existing long-term data
        existing_long_term = await self.get_long_term(lead_id)
        
        # Extract preferences and patterns from short-term interactions
        preferences = self._extract_preferences(short_term_data["context"])
        
        # Create or update interaction history
        interaction_record = {
            "conversation_id": conversation_id,
            "interaction_count": short_term_data.get("interaction_count", 1),
            "context_summary": self._summarize_context(short_term_data["context"]),
            "timestamp": short_term_data.get("last_updated")
        }
        
        if existing_long_term:
            # Update existing long-term memory
            existing_long_term["preferences"].update(preferences)
            existing_long_term["interaction_history"].append(interaction_record)
            
            await self.store_long_term(
                lead_id=lead_id,
                preferences=existing_long_term["preferences"],
                interaction_history=existing_long_term["interaction_history"]
            )
        else:
            # Create new long-term memory
            await self.store_long_term(
                lead_id=lead_id,
                preferences=preferences,
                interaction_history=[interaction_record]
            )
        
        logger.info(f"Consolidated conversation {conversation_id} to long-term memory")
        return True
    
    async def run_memory_consolidation(self):
        """Background task for memory consolidation and cleanup"""
        
        while True:
            try:
                # Clean up expired short-term memory
                await self.short_term.cleanup_expired()
                
                # Consolidate high-frequency interactions
                await self._consolidate_frequent_interactions()
                
                # Update semantic relationships
                await self._update_semantic_relationships()
                
                # Sleep for consolidation interval
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Memory consolidation error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    async def _consolidate_frequent_interactions(self):
        """Identify and consolidate frequently accessed short-term memories"""
        
        # Get all active short-term memories
        active_memories = await self.short_term.get_all_active()
        
        for conversation_id, data in active_memories.items():
            interaction_count = data.get("interaction_count", 0)
            
            if interaction_count >= self.consolidation_settings["short_to_long_threshold"]:
                await self._consolidate_to_long_term(conversation_id, data)
    
    async def _update_semantic_relationships(self):
        """Update semantic relationships based on interaction patterns"""
        
        # Get recent successful interactions
        recent_successes = await self.episodic.get_recent_successes(limit=100)
        
        for episode in recent_successes:
            # Extract concepts and relationships
            concepts = self._extract_concepts(episode)
            
            # Store relationships in semantic memory
            for concept_pair in concepts:
                await self.store_knowledge_triple(
                    subject=concept_pair["subject"],
                    predicate="related_to",
                    obj=concept_pair["object"],
                    weight=episode.get("outcome_score", 0.5),
                    source="episodic_learning"
                )
    
    # Helper methods
    async def _calculate_rfm_score(
        self, 
        lead_id: str, 
        interaction_history: List[Dict[str, Any]]
    ) -> float:
        """Calculate Recency, Frequency, Monetary score for lead"""
        
        if not interaction_history:
            return 0.0
        
        # Recency (0-1): How recent was last interaction
        last_interaction = max(
            interaction_history, 
            key=lambda x: x.get("timestamp", "")
        )
        
        last_timestamp = datetime.fromisoformat(
            last_interaction.get("timestamp", datetime.now().isoformat())
        )
        days_since = (datetime.now() - last_timestamp).days
        recency_score = max(0, 1 - (days_since / 30))  # Decay over 30 days
        
        # Frequency (0-1): Number of interactions normalized
        frequency_score = min(1.0, len(interaction_history) / 10)
        
        # Monetary (0-1): Value-based scoring (if conversion data available)
        monetary_score = 0.5  # Default mid-score
        
        # Combined RFM score
        rfm_score = (recency_score + frequency_score + monetary_score) / 3
        
        return round(rfm_score, 3)
    
    def _extract_preferences(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract customer preferences from interaction context"""
        
        preferences = {}
        
        # Communication preferences
        if "preferred_channel" in context:
            preferences["communication_channel"] = context["preferred_channel"]
        
        if "contact_time" in context:
            preferences["contact_time"] = context["contact_time"]
        
        # Content preferences
        if "interests" in context:
            preferences["interests"] = context["interests"]
        
        if "communication_style" in context:
            preferences["communication_style"] = context["communication_style"]
        
        # Product preferences
        if "product_interests" in context:
            preferences["product_interests"] = context["product_interests"]
        
        return preferences
    
    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Create a summary of interaction context"""
        
        summary_parts = []
        
        if "lead_source" in context:
            summary_parts.append(f"Source: {context['lead_source']}")
        
        if "interaction_type" in context:
            summary_parts.append(f"Type: {context['interaction_type']}")
        
        if "outcome" in context:
            summary_parts.append(f"Outcome: {context['outcome']}")
        
        return " | ".join(summary_parts) if summary_parts else "General interaction"
    
    def _context_to_search_text(self, context: Dict[str, Any]) -> str:
        """Convert context dictionary to searchable text"""
        
        text_parts = []
        
        for key, value in context.items():
            if isinstance(value, str):
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, (list, dict)):
                text_parts.append(f"{key}: {json.dumps(value)}")
            else:
                text_parts.append(f"{key}: {str(value)}")
        
        return " ".join(text_parts)
    
    def _extract_concepts(self, episode: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract concept relationships from successful episodes"""
        
        concepts = []
        
        # Extract from scenario and context
        scenario = episode.get("scenario", "")
        context = episode.get("context", {})
        
        # Simple concept extraction (in production, use NLP)
        if "lead_source" in context and "outcome" in context:
            concepts.append({
                "subject": context["lead_source"],
                "object": context["outcome"]
            })
        
        if scenario and "action_sequence" in episode:
            for action in episode.get("action_sequence", []):
                concepts.append({
                    "subject": scenario,
                    "object": action
                })
        
        return concepts
    
    # Health check methods
    async def get_memory_status(self) -> Dict[str, Any]:
        """Get status of all memory subsystems"""
        
        return {
            "short_term": await self.short_term.get_status(),
            "long_term": await self.long_term.get_status(),
            "episodic": await self.episodic.get_status(),
            "semantic": await self.semantic.get_status(),
            "consolidation_settings": self.consolidation_settings,
            "initialized": self.initialized
        }
