"""
WebSocket Manager Implementation

Manages WebSocket connections for real-time agent communication.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

try:
    from fastapi import WebSocket
except ImportError:
    WebSocket = None

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    WebSocket Manager for Real-time Agent Communication
    
    Features:
    - Agent connection management
    - Message broadcasting
    - Connection health monitoring
    - Message queuing
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_metadata: Dict[str, Dict[str, Any]] = {}
        self.message_queue: Dict[str, List[Dict[str, Any]]] = {}
        
    async def connect_agent(self, agent_id: str, websocket: WebSocket):
        """Register a new agent connection"""
        self.active_connections[agent_id] = websocket
        self.agent_metadata[agent_id] = {
            "connected_at": datetime.now(),
            "last_seen": datetime.now(),
            "message_count": 0
        }
        
        # Deliver any queued messages
        if agent_id in self.message_queue:
            for message in self.message_queue[agent_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error delivering queued message to {agent_id}: {e}")
            
            # Clear queue after delivery
            del self.message_queue[agent_id]
        
        logger.info(f"Agent {agent_id} connected via WebSocket")
    
    async def disconnect_agent(self, agent_id: str):
        """Unregister an agent connection"""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
        
        if agent_id in self.agent_metadata:
            del self.agent_metadata[agent_id]
        
        logger.info(f"Agent {agent_id} disconnected")
    
    async def send_to_agent(self, agent_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific agent"""
        if agent_id in self.active_connections:
            try:
                websocket = self.active_connections[agent_id]
                await websocket.send_text(json.dumps(message))
                
                # Update metadata
                self.agent_metadata[agent_id]["last_seen"] = datetime.now()
                self.agent_metadata[agent_id]["message_count"] += 1
                
                return True
                
            except Exception as e:
                logger.error(f"Error sending message to {agent_id}: {e}")
                # Remove broken connection
                await self.disconnect_agent(agent_id)
                return False
        else:
            # Queue message for later delivery
            if agent_id not in self.message_queue:
                self.message_queue[agent_id] = []
            
            self.message_queue[agent_id].append({
                **message,
                "queued_at": datetime.now().isoformat()
            })
            
            logger.info(f"Queued message for offline agent {agent_id}")
            return False
    
    async def broadcast_to_agents(
        self, 
        message: Dict[str, Any], 
        sender: str,
        target_agents: Optional[List[str]] = None
    ):
        """Broadcast message to multiple agents"""
        
        # Determine target agents
        if target_agents:
            targets = [aid for aid in target_agents if aid in self.active_connections]
        else:
            # Broadcast to all except sender
            targets = [aid for aid in self.active_connections.keys() if aid != sender]
        
        # Send to each target
        results = {}
        for agent_id in targets:
            success = await self.send_to_agent(agent_id, {
                "type": "broadcast",
                "sender": sender,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            results[agent_id] = success
        
        logger.info(f"Broadcast from {sender} to {len(targets)} agents")
        return results
    
    async def get_agents_status(self) -> Dict[str, Any]:
        """Get status of all connected agents"""
        status = {
            "total_connections": len(self.active_connections),
            "queued_messages": sum(len(queue) for queue in self.message_queue.values()),
            "agents": {}
        }
        
        for agent_id, metadata in self.agent_metadata.items():
            status["agents"][agent_id] = {
                "status": "connected" if agent_id in self.active_connections else "disconnected",
                "connected_at": metadata["connected_at"].isoformat(),
                "last_seen": metadata["last_seen"].isoformat(),
                "message_count": metadata["message_count"]
            }
        
        # Add queued message info
        for agent_id, queue in self.message_queue.items():
            if agent_id not in status["agents"]:
                status["agents"][agent_id] = {"status": "offline"}
            status["agents"][agent_id]["queued_messages"] = len(queue)
        
        return status
    
    async def cleanup_stale_connections(self, timeout_minutes: int = 30):
        """Clean up stale connections"""
        cutoff_time = datetime.now().timestamp() - (timeout_minutes * 60)
        stale_agents = []
        
        for agent_id, metadata in self.agent_metadata.items():
            if metadata["last_seen"].timestamp() < cutoff_time:
                stale_agents.append(agent_id)
        
        for agent_id in stale_agents:
            await self.disconnect_agent(agent_id)
            logger.info(f"Cleaned up stale connection for {agent_id}")
        
        return len(stale_agents)


class MockWebSocketManager:
    """Mock WebSocket manager for testing"""
    
    def __init__(self):
        self.agents = set()
        self.messages = []
    
    async def connect_agent(self, agent_id: str, websocket=None):
        self.agents.add(agent_id)
        logger.info(f"Mock: Agent {agent_id} connected")
    
    async def disconnect_agent(self, agent_id: str):
        self.agents.discard(agent_id)
        logger.info(f"Mock: Agent {agent_id} disconnected")
    
    async def send_to_agent(self, agent_id: str, message: Dict[str, Any]) -> bool:
        if agent_id in self.agents:
            self.messages.append({"to": agent_id, "message": message})
            logger.info(f"Mock: Message sent to {agent_id}")
            return True
        return False
    
    async def broadcast_to_agents(self, message: Dict[str, Any], sender: str, target_agents=None):
        targets = target_agents or list(self.agents)
        for agent_id in targets:
            if agent_id != sender:
                await self.send_to_agent(agent_id, message)
        return {agent_id: True for agent_id in targets if agent_id != sender}
    
    async def get_agents_status(self):
        return {
            "total_connections": len(self.agents),
            "agents": {agent_id: {"status": "connected"} for agent_id in self.agents}
        }
