"""
JSON-RPC 2.0 Server Implementation

Handles JSON-RPC method registration and request processing for the MCP server.
"""

import json
import asyncio
from typing import Dict, Any, Callable, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class JSONRPCServer:
    """
    JSON-RPC 2.0 Server Implementation
    
    Features:
    - Method registration and routing
    - Request validation and processing
    - Error handling and responses
    - Async method support
    """
    
    def __init__(self):
        self.methods: Dict[str, Callable] = {}
        self.request_count = 0
        
    def register_method(self, method_name: str, handler: Callable):
        """Register a method handler"""
        self.methods[method_name] = handler
        logger.info(f"Registered JSON-RPC method: {method_name}")
    
    async def handle_request(
        self, 
        method: str, 
        params: Optional[Dict[str, Any]] = None, 
        request_id: Optional[str] = None,
        agent_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle a JSON-RPC request"""
        
        self.request_count += 1
        start_time = datetime.now()
        
        try:
            # Validate method exists
            if method not in self.methods:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": "Method not found",
                        "data": f"Method '{method}' is not registered"
                    },
                    "id": request_id
                }
            
            # Get method handler
            handler = self.methods[method]
            
            # Prepare parameters
            call_params = params or {}
            
            # Add agent context if handler supports it
            if agent_context:
                import inspect
                sig = inspect.signature(handler)
                if 'agent_context' in sig.parameters:
                    call_params['agent_context'] = agent_context
            
            # Call method handler
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**call_params)
            else:
                result = handler(**call_params)
            
            # Log successful request
            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"JSON-RPC {method} completed in {duration:.2f}ms")
            
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
            
        except TypeError as e:
            # Parameter validation error
            logger.error(f"Invalid parameters for {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "Invalid params",
                    "data": str(e)
                },
                "id": request_id
            }
            
        except Exception as e:
            # Internal error
            logger.error(f"Error executing {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                },
                "id": request_id
            }
    
    def get_method_list(self) -> list:
        """Get list of registered methods"""
        return list(self.methods.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            "registered_methods": len(self.methods),
            "total_requests": self.request_count,
            "methods": list(self.methods.keys())
        }
