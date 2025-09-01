"""
MCP (Model Context Protocol) Server

Provides secure data access to marketing databases and analytics for the multi-agent system.
Implements JSON-RPC 2.0 protocol for inter-agent communication.
"""

from typing import Dict, Any, List, Optional
import json
import asyncio
import logging
from datetime import datetime
import uuid

from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from transport.json_rpc_server import JSONRPCServer
from transport.websocket_manager import WebSocketManager
from memory_systems.memory_manager import MemoryManager
from api.auth import verify_token, get_current_agent
from api.models import MCPRequest, MCPResponse, ResourceAccess


# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


class MCPServer:
    """
    Model Context Protocol Server
    
    Provides secure, controlled access to:
    - Marketing databases (leads, campaigns, interactions)
    - Analytics data and metrics
    - Memory systems (short-term, long-term, episodic, semantic)
    - Agent communication infrastructure
    """
    
    def __init__(self):
        self.app = FastAPI(
            title="Marketing Multi-Agent MCP Server",
            description="Model Context Protocol server for marketing agent system",
            version="1.0.0"
        )
        
        # Core components
        self.rpc_server = JSONRPCServer()
        self.ws_manager = WebSocketManager()
        self.memory_manager = MemoryManager()
        
        # Resource access tracking
        self.resource_access_log: List[ResourceAccess] = []
        
        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()
        self._setup_rpc_methods()
    
    def _setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup HTTP endpoints"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        
        @self.app.post("/rpc")
        async def handle_rpc(
            request: MCPRequest,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """Handle JSON-RPC 2.0 requests over HTTP"""
            
            # Verify authentication
            agent_info = await verify_token(credentials.credentials)
            if not agent_info:
                raise HTTPException(status_code=401, detail="Invalid authentication")
            
            # Log resource access
            await self._log_resource_access(
                resource_uri="rpc://jsonrpc",
                scope="execute",
                operation=request.method,
                actor=agent_info.get("agent_id", "unknown"),
                success=True
            )
            
            # Process RPC request
            try:
                response = await self.rpc_server.handle_request(
                    method=request.method,
                    params=request.params,
                    request_id=request.id,
                    agent_context=agent_info
                )
                
                return MCPResponse(
                    jsonrpc="2.0",
                    result=response,
                    id=request.id
                )
                
            except Exception as e:
                logger.error(f"RPC Error: {e}")
                return MCPResponse(
                    jsonrpc="2.0",
                    error={
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    },
                    id=request.id
                )
        
        @self.app.websocket("/ws/{agent_id}")
        async def websocket_endpoint(websocket: WebSocket, agent_id: str):
            """WebSocket endpoint for real-time agent communication"""
            
            # Accept connection
            await websocket.accept()
            
            # Verify agent authentication (implement token verification)
            # For now, accept all connections with valid agent_id format
            
            # Register agent with WebSocket manager
            await self.ws_manager.connect_agent(agent_id, websocket)
            
            try:
                while True:
                    # Receive message from agent
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Log WebSocket activity
                    await self._log_resource_access(
                        resource_uri=f"ws://agent/{agent_id}",
                        scope="send_message",
                        operation="websocket_message",
                        actor=agent_id,
                        success=True
                    )
                    
                    # Process message based on type
                    if message.get("type") == "rpc":
                        # Handle RPC over WebSocket
                        response = await self.rpc_server.handle_request(
                            method=message.get("method"),
                            params=message.get("params"),
                            request_id=message.get("id"),
                            agent_context={"agent_id": agent_id}
                        )
                        
                        await websocket.send_text(json.dumps({
                            "type": "rpc_response",
                            "result": response,
                            "id": message.get("id")
                        }))
                    
                    elif message.get("type") == "broadcast":
                        # Broadcast message to other agents
                        await self.ws_manager.broadcast_to_agents(
                            message=message.get("data"),
                            sender=agent_id,
                            target_agents=message.get("targets")
                        )
            
            except Exception as e:
                logger.error(f"WebSocket error for agent {agent_id}: {e}")
            
            finally:
                # Disconnect agent
                await self.ws_manager.disconnect_agent(agent_id)
        
        @self.app.get("/agents/status")
        async def get_agents_status(
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """Get status of all connected agents"""
            
            agent_info = await verify_token(credentials.credentials)
            if not agent_info:
                raise HTTPException(status_code=401, detail="Invalid authentication")
            
            return await self.ws_manager.get_agents_status()
        
        @self.app.get("/resources/access-log")
        async def get_resource_access_log(
            credentials: HTTPAuthorizationCredentials = Depends(security),
            limit: int = 100
        ):
            """Get recent resource access logs"""
            
            agent_info = await verify_token(credentials.credentials)
            if not agent_info:
                raise HTTPException(status_code=401, detail="Invalid authentication")
            
            return {
                "access_log": self.resource_access_log[-limit:],
                "total_entries": len(self.resource_access_log)
            }
    
    def _setup_rpc_methods(self):
        """Register RPC methods with the JSON-RPC server"""
        
        # Database access methods
        self.rpc_server.register_method("db.leads.query", self._query_leads)
        self.rpc_server.register_method("db.campaigns.query", self._query_campaigns)
        self.rpc_server.register_method("db.interactions.query", self._query_interactions)
        self.rpc_server.register_method("db.conversions.query", self._query_conversions)
        
        # Memory system methods
        self.rpc_server.register_method("memory.short_term.get", self._get_short_term_memory)
        self.rpc_server.register_method("memory.short_term.store", self._store_short_term_memory)
        self.rpc_server.register_method("memory.long_term.get", self._get_long_term_memory)
        self.rpc_server.register_method("memory.long_term.store", self._store_long_term_memory)
        self.rpc_server.register_method("memory.episodic.search", self._search_episodic_memory)
        self.rpc_server.register_method("memory.semantic.query", self._query_semantic_memory)
        
        # Agent communication methods
        self.rpc_server.register_method("agent.handoff", self._handle_agent_handoff)
        self.rpc_server.register_method("agent.escalate", self._handle_escalation)
        self.rpc_server.register_method("agent.broadcast", self._handle_broadcast)
        
        # Analytics methods
        self.rpc_server.register_method("analytics.performance", self._get_performance_metrics)
        self.rpc_server.register_method("analytics.conversion_rates", self._get_conversion_rates)
        self.rpc_server.register_method("analytics.agent_metrics", self._get_agent_metrics)
    
    # Database access methods
    async def _query_leads(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Query leads database with filtering and pagination"""
        
        await self._log_resource_access(
            resource_uri="db://leads",
            scope="read",
            operation="SELECT",
            actor=agent_context.get("agent_id"),
            success=True
        )
        
        # Implement actual database query logic here
        # For now, return mock data structure
        return {
            "leads": [],
            "total_count": 0,
            "query_params": params
        }
    
    async def _query_campaigns(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Query campaigns database"""
        
        await self._log_resource_access(
            resource_uri="db://campaigns", 
            scope="read",
            operation="SELECT",
            actor=agent_context.get("agent_id"),
            success=True
        )
        
        return {
            "campaigns": [],
            "total_count": 0,
            "query_params": params
        }
    
    async def _query_interactions(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Query interactions database"""
        
        await self._log_resource_access(
            resource_uri="db://interactions",
            scope="read", 
            operation="SELECT",
            actor=agent_context.get("agent_id"),
            success=True
        )
        
        return {
            "interactions": [],
            "total_count": 0,
            "query_params": params
        }
    
    async def _query_conversions(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Query conversions database"""
        
        await self._log_resource_access(
            resource_uri="db://conversions",
            scope="read",
            operation="SELECT", 
            actor=agent_context.get("agent_id"),
            success=True
        )
        
        return {
            "conversions": [],
            "total_count": 0,
            "query_params": params
        }
    
    # Memory system methods
    async def _get_short_term_memory(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve short-term memory"""
        conversation_id = params.get("conversation_id")
        
        await self._log_resource_access(
            resource_uri="memory://short_term",
            scope="read",
            operation="GET",
            actor=agent_context.get("agent_id"),
            success=True
        )
        
        memory_data = await self.memory_manager.get_short_term(conversation_id)
        return {"memory_data": memory_data}
    
    async def _store_short_term_memory(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Store short-term memory"""
        
        await self._log_resource_access(
            resource_uri="memory://short_term",
            scope="write",
            operation="INSERT", 
            actor=agent_context.get("agent_id"),
            success=True
        )
        
        await self.memory_manager.store_short_term(
            conversation_id=params.get("conversation_id"),
            lead_id=params.get("lead_id"),
            context=params.get("context")
        )
        
        return {"success": True}
    
    async def _get_long_term_memory(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve long-term memory"""
        
        await self._log_resource_access(
            resource_uri="memory://long_term",
            scope="read",
            operation="GET",
            actor=agent_context.get("agent_id"),
            success=True
        )
        
        return {"memory_data": {}}
    
    async def _store_long_term_memory(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Store long-term memory"""
        
        await self._log_resource_access(
            resource_uri="memory://long_term",
            scope="write",
            operation="INSERT",
            actor=agent_context.get("agent_id"), 
            success=True
        )
        
        return {"success": True}
    
    async def _search_episodic_memory(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Search episodic memory for similar experiences"""
        
        await self._log_resource_access(
            resource_uri="memory://episodic",
            scope="search",
            operation="SEARCH",
            actor=agent_context.get("agent_id"),
            success=True
        )
        
        similar_experiences = await self.memory_manager.search_episodic_memory(
            query_context=params.get("context"),
            agent_type=params.get("agent_type")
        )
        
        return {"experiences": similar_experiences}
    
    async def _query_semantic_memory(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Query semantic knowledge graph"""
        
        await self._log_resource_access(
            resource_uri="kg://graph",
            scope="read",
            operation="QUERY",
            actor=agent_context.get("agent_id"),
            success=True
        )
        
        return {"graph_data": []}
    
    # Agent communication methods
    async def _handle_agent_handoff(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent-to-agent handoff"""
        
        target_agent = params.get("target_agent")
        
        # Send handoff message via WebSocket
        await self.ws_manager.send_to_agent(
            agent_id=target_agent,
            message={
                "type": "handoff",
                "data": params
            }
        )
        
        return {"success": True, "handoff_initiated": True}
    
    async def _handle_escalation(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle escalation to human manager"""
        
        # Store escalation in queue
        escalation_data = {
            "escalation_id": str(uuid.uuid4()),
            "agent_id": agent_context.get("agent_id"),
            "timestamp": datetime.now().isoformat(),
            "reason": params.get("reason"),
            "context": params.get("context"),
            "status": "pending"
        }
        
        # In production, this would go to a manager queue/dashboard
        logger.info(f"Escalation created: {escalation_data}")
        
        return {"success": True, "escalation_id": escalation_data["escalation_id"]}
    
    async def _handle_broadcast(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle broadcast message to multiple agents"""
        
        await self.ws_manager.broadcast_to_agents(
            message=params.get("message"),
            sender=agent_context.get("agent_id"),
            target_agents=params.get("target_agents")
        )
        
        return {"success": True, "broadcast_sent": True}
    
    # Analytics methods
    async def _get_performance_metrics(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get system performance metrics"""
        
        return {
            "metrics": {
                "total_leads_processed": 0,
                "average_response_time": 0,
                "conversion_rate": 0,
                "active_conversations": 0
            }
        }
    
    async def _get_conversion_rates(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversion rate analytics"""
        
        return {
            "conversion_rates": {
                "overall": 0,
                "by_source": {},
                "by_agent": {},
                "by_category": {}
            }
        }
    
    async def _get_agent_metrics(self, params: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get individual agent performance metrics"""
        
        return {
            "agent_metrics": {
                "actions_performed": 0,
                "handoffs_initiated": 0,
                "escalations_created": 0,
                "average_handling_time": 0
            }
        }
    
    async def _log_resource_access(
        self,
        resource_uri: str,
        scope: str,
        operation: str,
        actor: str,
        success: bool
    ):
        """Log resource access for audit and monitoring"""
        
        access_log = ResourceAccess(
            resource_uri=resource_uri,
            timestamp=datetime.now(),
            scope=scope,
            operation=operation,
            success=success,
            actor=actor
        )
        
        self.resource_access_log.append(access_log)
        
        # Keep only last 10000 entries to prevent memory issues
        if len(self.resource_access_log) > 10000:
            self.resource_access_log = self.resource_access_log[-5000:]
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the MCP server"""
        
        logger.info(f"Starting MCP Server on {host}:{port}")
        
        # Initialize memory manager
        await self.memory_manager.initialize()
        
        # Start server
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()


# Main entry point
if __name__ == "__main__":
    server = MCPServer()
    asyncio.run(server.start_server())
