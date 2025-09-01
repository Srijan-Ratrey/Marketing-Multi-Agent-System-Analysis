"""
Long-term Memory Implementation

PostgreSQL-based implementation for customer profiles, preferences, and interaction history.
Provides persistent storage with complex query capabilities.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

try:
    import asyncpg
except ImportError:
    asyncpg = None

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    PostgreSQL-based long-term memory for customer profiles and history
    
    Features:
    - Persistent storage with ACID properties
    - Complex queries and analytics
    - JSONB support for flexible schemas
    - Connection pooling for performance
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection_pool = None
        
    async def initialize(self):
        """Initialize PostgreSQL connection pool"""
        if asyncpg is None:
            logger.warning("asyncpg not available - using in-memory fallback")
            self.memory_store = {}
            return
        
        try:
            # Create connection pool
            self.connection_pool = await asyncpg.create_pool(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 5432),
                database=self.config.get("database", "marketing_agents"),
                user=self.config.get("user", "postgres"),
                password=self.config.get("password", "password"),
                min_size=5,
                max_size=20
            )
            
            # Create tables if they don't exist
            await self._create_tables()
            
            logger.info("Long-term memory (PostgreSQL) initialized successfully")
            
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e} - using in-memory fallback")
            self.connection_pool = None
            self.memory_store = {}
    
    async def _create_tables(self):
        """Create necessary tables"""
        if not self.connection_pool:
            return
        
        async with self.connection_pool.acquire() as conn:
            # Customer profiles table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS customer_profiles (
                    lead_id VARCHAR(255) PRIMARY KEY,
                    preferences JSONB DEFAULT '{}',
                    interaction_history JSONB DEFAULT '[]',
                    rfm_score DECIMAL(3,3) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Agent actions log
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_actions_log (
                    action_id VARCHAR(255) PRIMARY KEY,
                    agent_type VARCHAR(100),
                    action_type VARCHAR(100),
                    timestamp TIMESTAMP,
                    context JSONB,
                    result JSONB,
                    handoff_target VARCHAR(100)
                )
            """)
            
            # Handoff context log
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS handoff_context_log (
                    conversation_id VARCHAR(255),
                    lead_id VARCHAR(255),
                    source_agent VARCHAR(100),
                    target_agent VARCHAR(100),
                    context_data JSONB,
                    handoff_reason TEXT,
                    timestamp TIMESTAMP
                )
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_customer_rfm ON customer_profiles (rfm_score DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_customer_preferences ON customer_profiles USING GIN (preferences)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_agent ON agent_actions_log (agent_type, action_type)")
    
    async def store(self, lead_id: str, data: Dict[str, Any]) -> bool:
        """Store customer profile data"""
        try:
            if self.connection_pool:
                async with self.connection_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO customer_profiles (lead_id, preferences, interaction_history, rfm_score, last_updated)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (lead_id) DO UPDATE SET
                            preferences = $2,
                            interaction_history = $3,
                            rfm_score = $4,
                            last_updated = $5
                    """, 
                    lead_id,
                    json.dumps(data.get("preferences", {})),
                    json.dumps(data.get("interaction_history", [])),
                    data.get("rfm_score", 0.0),
                    datetime.now()
                    )
            else:
                # In-memory fallback
                self.memory_store[lead_id] = data
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing long-term memory: {e}")
            return False
    
    async def get(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve customer profile data"""
        try:
            if self.connection_pool:
                async with self.connection_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM customer_profiles WHERE lead_id = $1",
                        lead_id
                    )
                    
                    if row:
                        return {
                            "lead_id": row["lead_id"],
                            "preferences": json.loads(row["preferences"]) if row["preferences"] else {},
                            "interaction_history": json.loads(row["interaction_history"]) if row["interaction_history"] else [],
                            "rfm_score": float(row["rfm_score"]) if row["rfm_score"] else 0.0,
                            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                            "last_updated": row["last_updated"].isoformat() if row["last_updated"] else None
                        }
            else:
                # In-memory fallback
                return self.memory_store.get(lead_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving long-term memory: {e}")
            return None
    
    async def get_performance_data(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get historical performance data for similar contexts"""
        try:
            # Mock implementation - in production would query actual performance data
            return {
                "conversion_rate": 0.15,
                "average_deal_size": 12500,
                "time_to_conversion": 14  # days
            }
            
        except Exception as e:
            logger.error(f"Error retrieving performance data: {e}")
            return None
    
    async def log_action(self, action_data: Dict[str, Any]) -> bool:
        """Log agent action for analysis"""
        try:
            if self.connection_pool:
                async with self.connection_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO agent_actions_log 
                        (action_id, agent_type, action_type, timestamp, context, result, handoff_target)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    action_data.get("action_id"),
                    action_data.get("agent_type"),
                    action_data.get("action_type"),
                    datetime.fromisoformat(action_data.get("timestamp")) if action_data.get("timestamp") else datetime.now(),
                    json.dumps(action_data.get("context", {})),
                    json.dumps(action_data.get("result", {})),
                    action_data.get("handoff_target")
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging action: {e}")
            return False
    
    async def store_handoff(self, handoff_data: Dict[str, Any]) -> bool:
        """Store handoff context for analysis"""
        try:
            if self.connection_pool:
                async with self.connection_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO handoff_context_log 
                        (conversation_id, lead_id, source_agent, target_agent, context_data, handoff_reason, timestamp)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    handoff_data.get("conversation_id"),
                    handoff_data.get("lead_id"),
                    handoff_data.get("source_agent"),
                    handoff_data.get("target_agent"),
                    json.dumps(handoff_data.get("context_data", {})),
                    handoff_data.get("handoff_reason"),
                    datetime.fromisoformat(handoff_data.get("timestamp")) if handoff_data.get("timestamp") else datetime.now()
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing handoff: {e}")
            return False
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get analytics from long-term memory"""
        try:
            if self.connection_pool:
                async with self.connection_pool.acquire() as conn:
                    # Get customer count
                    customer_count = await conn.fetchval("SELECT COUNT(*) FROM customer_profiles")
                    
                    # Get action count
                    action_count = await conn.fetchval("SELECT COUNT(*) FROM agent_actions_log")
                    
                    # Get handoff count
                    handoff_count = await conn.fetchval("SELECT COUNT(*) FROM handoff_context_log")
                    
                    return {
                        "total_customers": customer_count or 0,
                        "total_actions": action_count or 0,
                        "total_handoffs": handoff_count or 0
                    }
            else:
                return {
                    "total_customers": len(self.memory_store),
                    "total_actions": 0,
                    "total_handoffs": 0
                }
                
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get memory system status"""
        if self.connection_pool:
            try:
                async with self.connection_pool.acquire() as conn:
                    # Test connection
                    result = await conn.fetchval("SELECT 1")
                    
                    analytics = await self.get_analytics()
                    
                    return {
                        "type": "postgresql",
                        "status": "connected",
                        "connection_test": "passed" if result == 1 else "failed",
                        **analytics
                    }
            except Exception as e:
                return {
                    "type": "postgresql",
                    "status": "error",
                    "error": str(e)
                }
        else:
            return {
                "type": "in_memory",
                "status": "active",
                "entries": len(getattr(self, 'memory_store', {}))
            }
    
    async def cleanup(self):
        """Cleanup connections"""
        if self.connection_pool:
            await self.connection_pool.close()
