"""
Authentication and Authorization Module

Handles agent authentication and token verification for the MCP server.
"""

import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Demo secret key - in production, use secure key management
SECRET_KEY = "marketing_agents_demo_key_2025"
ALGORITHM = "HS256"

# Demo agent credentials
DEMO_AGENTS = {
    "lead_triage_001": {
        "agent_type": "LeadTriage",
        "permissions": ["db.leads", "memory.short_term", "agent.handoff"]
    },
    "engagement_001": {
        "agent_type": "Engagement", 
        "permissions": ["db.interactions", "memory.long_term", "agent.handoff"]
    },
    "campaign_opt_001": {
        "agent_type": "CampaignOptimization",
        "permissions": ["db.campaigns", "analytics", "agent.escalate"]
    },
    "demo_user": {
        "agent_type": "User",
        "permissions": ["*"]  # Admin access for demo
    }
}


def create_demo_token(agent_id: str) -> str:
    """Create a demo JWT token for testing"""
    if agent_id not in DEMO_AGENTS:
        raise ValueError(f"Unknown agent: {agent_id}")
    
    agent_info = DEMO_AGENTS[agent_id]
    payload = {
        "agent_id": agent_id,
        "agent_type": agent_info["agent_type"],
        "permissions": agent_info["permissions"],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


async def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return agent info"""
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Validate token structure
        required_fields = ["agent_id", "agent_type", "permissions"]
        if not all(field in payload for field in required_fields):
            logger.warning("Invalid token structure")
            return None
        
        # Check if agent still exists
        agent_id = payload["agent_id"]
        if agent_id not in DEMO_AGENTS:
            logger.warning(f"Token for unknown agent: {agent_id}")
            return None
        
        return {
            "agent_id": payload["agent_id"],
            "agent_type": payload["agent_type"],
            "permissions": payload["permissions"]
        }
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


async def get_current_agent(token: str) -> Optional[Dict[str, Any]]:
    """Get current agent info from token (alias for verify_token)"""
    return await verify_token(token)


def check_permission(agent_info: Dict[str, Any], required_permission: str) -> bool:
    """Check if agent has required permission"""
    permissions = agent_info.get("permissions", [])
    
    # Admin access
    if "*" in permissions:
        return True
    
    # Exact permission match
    if required_permission in permissions:
        return True
    
    # Wildcard permission match (e.g., "db.*" covers "db.leads")
    for permission in permissions:
        if permission.endswith("*"):
            prefix = permission[:-1]
            if required_permission.startswith(prefix):
                return True
    
    return False


def get_demo_tokens() -> Dict[str, str]:
    """Get demo tokens for all agents"""
    return {agent_id: create_demo_token(agent_id) for agent_id in DEMO_AGENTS.keys()}


# Simple API key authentication as fallback
def generate_api_key(agent_id: str) -> str:
    """Generate simple API key for demo"""
    data = f"{agent_id}:{SECRET_KEY}:{datetime.now().date()}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


async def verify_api_key(api_key: str, agent_id: str) -> bool:
    """Verify API key"""
    expected_key = generate_api_key(agent_id)
    return api_key == expected_key
