"""
Short-term Memory Implementation

Redis-based implementation for current conversation contexts and session data.
Provides high-speed access with TTL-based expiration.
"""

import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """
    Redis-based short-term memory for active conversation contexts
    
    Features:
    - High-speed read/write operations
    - TTL-based automatic expiration
    - JSON serialization for complex data
    - Connection pooling for performance
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        self.connection_pool = None
        
    async def initialize(self):
        """Initialize Redis connection"""
        if redis is None:
            logger.warning("Redis not available - using in-memory fallback")
            self.memory_store = {}
            return
        
        try:
            # Create connection pool
            self.connection_pool = redis.ConnectionPool(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 6379),
                db=self.config.get("db", 0),
                decode_responses=True,
                max_connections=20
            )
            
            # Create Redis client
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Short-term memory (Redis) initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - using in-memory fallback")
            self.redis_client = None
            self.memory_store = {}
    
    async def store(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store data with optional TTL"""
        try:
            serialized_data = json.dumps(data, default=str)
            
            if self.redis_client:
                # Use Redis
                if ttl:
                    await self.redis_client.setex(key, ttl, serialized_data)
                else:
                    await self.redis_client.set(key, serialized_data)
            else:
                # Use in-memory fallback
                expiry = datetime.now() + timedelta(seconds=ttl) if ttl else None
                self.memory_store[key] = {
                    "data": serialized_data,
                    "expires_at": expiry
                }
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing short-term memory: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data by key"""
        try:
            if self.redis_client:
                # Use Redis
                data = await self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                # Use in-memory fallback
                entry = self.memory_store.get(key)
                if entry:
                    # Check expiry
                    if entry["expires_at"] and datetime.now() > entry["expires_at"]:
                        del self.memory_store[key]
                        return None
                    return json.loads(entry["data"])
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving short-term memory: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete data by key"""
        try:
            if self.redis_client:
                result = await self.redis_client.delete(key)
                return result > 0
            else:
                if key in self.memory_store:
                    del self.memory_store[key]
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting short-term memory: {e}")
            return False
    
    async def cleanup_expired(self):
        """Clean up expired entries (for in-memory fallback)"""
        if not self.redis_client:
            current_time = datetime.now()
            expired_keys = [
                key for key, entry in self.memory_store.items()
                if entry["expires_at"] and current_time > entry["expires_at"]
            ]
            
            for key in expired_keys:
                del self.memory_store[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired short-term memory entries")
    
    async def get_all_active(self) -> Dict[str, Dict[str, Any]]:
        """Get all active conversations (for consolidation)"""
        active_memories = {}
        
        try:
            if self.redis_client:
                # Get all keys from Redis
                keys = await self.redis_client.keys("*")
                for key in keys:
                    data = await self.get(key)
                    if data:
                        active_memories[key] = data
            else:
                # Use in-memory store
                current_time = datetime.now()
                for key, entry in self.memory_store.items():
                    if not entry["expires_at"] or current_time <= entry["expires_at"]:
                        active_memories[key] = json.loads(entry["data"])
            
            return active_memories
            
        except Exception as e:
            logger.error(f"Error getting active memories: {e}")
            return {}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get memory system status"""
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                return {
                    "type": "redis",
                    "status": "connected",
                    "memory_usage": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0)
                }
            except Exception as e:
                return {
                    "type": "redis",
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
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
