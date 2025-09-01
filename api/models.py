"""
API Models

Pydantic models for request/response validation and OpenAPI documentation.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AgentType(str, Enum):
    """Supported agent types"""
    LEAD_TRIAGE = "LeadTriage"
    ENGAGEMENT = "Engagement"
    CAMPAIGN_OPTIMIZATION = "CampaignOptimization"


class ActionType(str, Enum):
    """Supported action types"""
    TRIAGE = "triage"
    OUTREACH = "outreach"
    NURTURE = "nurture"
    OPTIMIZE = "optimize"
    HANDOFF = "handoff"
    ESCALATE = "escalate"


class TriageCategory(str, Enum):
    """Lead triage categories"""
    CAMPAIGN_QUALIFIED = "Campaign Qualified"
    GENERAL_INQUIRY = "General Inquiry"
    COLD_LEAD = "Cold Lead"


class LeadStatus(str, Enum):
    """Lead status values"""
    NEW = "New"
    OPEN = "Open"
    QUALIFIED = "Qualified"
    UNQUALIFIED = "Unqualified"
    CONVERTED = "Converted"


# Base models
class BaseRequest(BaseModel):
    """Base request model"""
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    request_id: Optional[str] = None


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    timestamp: datetime = Field(default_factory=datetime.now)
    message: Optional[str] = None


# MCP Protocol models
class MCPRequest(BaseModel):
    """JSON-RPC 2.0 request model"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    method: str = Field(..., description="Method name to call")
    params: Optional[Dict[str, Any]] = Field(default={}, description="Method parameters")
    id: Optional[Union[str, int]] = Field(default=None, description="Request ID")


class MCPResponse(BaseModel):
    """JSON-RPC 2.0 response model"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Method result")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error information")
    id: Optional[Union[str, int]] = Field(default=None, description="Request ID")


# Agent models
class LeadData(BaseModel):
    """Lead information model"""
    lead_id: str = Field(..., description="Unique lead identifier")
    email: Optional[str] = Field(None, description="Lead email address")
    phone: Optional[str] = Field(None, description="Lead phone number")
    company_size: Optional[str] = Field(None, description="Company size category")
    industry: Optional[str] = Field(None, description="Industry sector")
    source: Optional[str] = Field(None, description="Lead acquisition source")
    campaign_id: Optional[str] = Field(None, description="Associated campaign ID")
    created_at: Optional[datetime] = Field(None, description="Lead creation timestamp")
    last_active_at: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    # Triage results
    lead_score: Optional[float] = Field(None, ge=0, le=100, description="Lead score (0-100)")
    triage_category: Optional[TriageCategory] = Field(None, description="Triage category")
    lead_status: Optional[LeadStatus] = Field(None, description="Current lead status")
    
    # Engagement data
    email_opens: Optional[int] = Field(default=0, description="Number of email opens")
    website_visits: Optional[int] = Field(default=0, description="Number of website visits")
    content_downloads: Optional[int] = Field(default=0, description="Content download count")
    demo_requests: Optional[int] = Field(default=0, description="Demo request count")
    contact_form_fills: Optional[int] = Field(default=0, description="Contact form submissions")


class AgentActionRequest(BaseModel):
    """Request to execute an agent action"""
    agent_type: AgentType = Field(..., description="Type of agent to execute action")
    action_type: ActionType = Field(..., description="Type of action to perform")
    context: Dict[str, Any] = Field(..., description="Action context data")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")


class AgentActionResponse(BaseResponse):
    """Response from agent action execution"""
    action_id: str = Field(..., description="Unique action identifier")
    agent_type: AgentType = Field(..., description="Agent that executed the action")
    action_type: ActionType = Field(..., description="Type of action performed")
    result: Optional[Dict[str, Any]] = Field(None, description="Action execution result")
    handoff_needed: bool = Field(default=False, description="Whether handoff is required")
    handoff_target: Optional[AgentType] = Field(None, description="Target agent for handoff")


class HandoffRequest(BaseModel):
    """Request to hand off conversation to another agent"""
    conversation_id: str = Field(..., description="Conversation to hand off")
    lead_id: str = Field(..., description="Lead associated with conversation")
    source_agent: AgentType = Field(..., description="Agent initiating handoff")
    target_agent: AgentType = Field(..., description="Agent receiving handoff")
    handoff_reason: str = Field(..., description="Reason for handoff")
    context_data: Dict[str, Any] = Field(..., description="Context to preserve")


class HandoffResponse(BaseResponse):
    """Response from handoff operation"""
    handoff_id: str = Field(..., description="Unique handoff identifier")
    handoff_accepted: bool = Field(..., description="Whether handoff was accepted")


class EscalationRequest(BaseModel):
    """Request to escalate to human manager"""
    conversation_id: str = Field(..., description="Conversation to escalate")
    agent_type: AgentType = Field(..., description="Agent requesting escalation")
    escalation_reason: str = Field(..., description="Reason for escalation")
    context: Dict[str, Any] = Field(..., description="Escalation context")
    priority: str = Field(default="medium", description="Escalation priority")


class EscalationResponse(BaseResponse):
    """Response from escalation request"""
    escalation_id: str = Field(..., description="Unique escalation identifier")
    estimated_response_time: Optional[str] = Field(None, description="Estimated manager response time")


# Memory models
class MemoryStoreRequest(BaseModel):
    """Request to store data in memory system"""
    memory_type: str = Field(..., description="Type of memory (short_term, long_term, episodic, semantic)")
    key: str = Field(..., description="Memory key/identifier")
    data: Dict[str, Any] = Field(..., description="Data to store")
    ttl: Optional[int] = Field(None, description="Time to live in seconds (short-term only)")


class MemoryRetrieveRequest(BaseModel):
    """Request to retrieve data from memory system"""
    memory_type: str = Field(..., description="Type of memory to query")
    key: Optional[str] = Field(None, description="Specific key to retrieve")
    query: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class MemoryResponse(BaseResponse):
    """Response from memory operation"""
    data: Optional[Dict[str, Any]] = Field(None, description="Retrieved memory data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Memory metadata")


# Analytics models
class PerformanceMetrics(BaseModel):
    """System performance metrics"""
    total_leads_processed: int = Field(..., description="Total leads processed")
    average_response_time: float = Field(..., description="Average response time in milliseconds")
    conversion_rate: float = Field(..., description="Overall conversion rate")
    active_conversations: int = Field(..., description="Number of active conversations")
    handoff_success_rate: float = Field(..., description="Percentage of successful handoffs")
    escalation_rate: float = Field(..., description="Percentage of escalated conversations")


class AgentMetrics(BaseModel):
    """Individual agent performance metrics"""
    agent_type: AgentType = Field(..., description="Type of agent")
    actions_performed: int = Field(..., description="Total actions performed")
    handoffs_initiated: int = Field(..., description="Number of handoffs initiated")
    handoffs_received: int = Field(..., description="Number of handoffs received")
    escalations_created: int = Field(..., description="Number of escalations created")
    average_handling_time: float = Field(..., description="Average handling time in seconds")
    success_rate: float = Field(..., description="Action success rate")


class ConversionAnalytics(BaseModel):
    """Conversion rate analytics"""
    overall_rate: float = Field(..., description="Overall conversion rate")
    by_source: Dict[str, float] = Field(..., description="Conversion rates by lead source")
    by_agent: Dict[str, float] = Field(..., description="Conversion rates by agent")
    by_category: Dict[str, float] = Field(..., description="Conversion rates by triage category")
    by_campaign: Dict[str, float] = Field(..., description="Conversion rates by campaign")


# Database query models
class DatabaseQuery(BaseModel):
    """Database query request"""
    table: str = Field(..., description="Table/collection to query")
    filters: Optional[Dict[str, Any]] = Field(default={}, description="Query filters")
    fields: Optional[List[str]] = Field(default=None, description="Fields to return")
    limit: Optional[int] = Field(default=100, description="Maximum results to return")
    offset: Optional[int] = Field(default=0, description="Results offset for pagination")
    sort: Optional[Dict[str, str]] = Field(default=None, description="Sort configuration")


class DatabaseResponse(BaseResponse):
    """Database query response"""
    data: List[Dict[str, Any]] = Field(..., description="Query results")
    total_count: int = Field(..., description="Total matching records")
    query_time: float = Field(..., description="Query execution time in seconds")


# Resource access models
class ResourceAccess(BaseModel):
    """Resource access log entry"""
    resource_uri: str = Field(..., description="URI of accessed resource")
    timestamp: datetime = Field(..., description="Access timestamp")
    scope: str = Field(..., description="Access scope (read, write, execute)")
    operation: str = Field(..., description="Operation performed")
    success: bool = Field(..., description="Whether operation succeeded")
    actor: str = Field(..., description="Actor performing the operation")


# WebSocket models
class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    sender: Optional[str] = Field(None, description="Message sender")
    targets: Optional[List[str]] = Field(None, description="Target agents for message")


class AgentStatus(BaseModel):
    """Agent connection status"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: AgentType = Field(..., description="Type of agent")
    status: str = Field(..., description="Connection status (connected, disconnected)")
    last_seen: datetime = Field(..., description="Last activity timestamp")
    active_conversations: int = Field(..., description="Number of active conversations")


# Configuration models
class SystemConfig(BaseModel):
    """System configuration"""
    memory_settings: Dict[str, Any] = Field(..., description="Memory system configuration")
    agent_settings: Dict[str, Any] = Field(..., description="Agent configuration")
    security_settings: Dict[str, Any] = Field(..., description="Security configuration")
    monitoring_settings: Dict[str, Any] = Field(..., description="Monitoring configuration")


class HealthCheck(BaseModel):
    """System health check response"""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    version: str = Field(..., description="System version")
    components: Dict[str, str] = Field(..., description="Component health status")
    uptime: float = Field(..., description="System uptime in seconds")
    memory_usage: Dict[str, float] = Field(..., description="Memory usage statistics")


# Error models
class ErrorDetail(BaseModel):
    """Detailed error information"""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Associated request ID")


class ValidationError(BaseModel):
    """Validation error details"""
    field: str = Field(..., description="Field with validation error")
    message: str = Field(..., description="Validation error message")
    invalid_value: Optional[Any] = Field(None, description="Invalid value provided")
