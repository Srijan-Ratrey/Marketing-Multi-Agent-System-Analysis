# ADR-002: Adaptive Memory System Design

## Status
**ACCEPTED** - 2025-01-01

## Context

The marketing multi-agent system requires sophisticated memory capabilities to learn and adapt from customer interactions. The system must store and retrieve different types of information with varying persistence requirements, access patterns, and use cases.

## Decision

We will implement a **4-tier adaptive memory architecture** with specialized storage systems optimized for different memory types and access patterns.

### Memory System Architecture

#### 1. Short-term Memory (Redis)
- **Purpose**: Active conversation contexts and session data
- **Technology**: Redis with TTL-based expiration
- **Access Pattern**: High-frequency read/write, low latency required
- **Data Structure**: JSON documents with conversation metadata
- **TTL Strategy**: 1-24 hours based on conversation activity
- **Capacity**: ~10,000 active conversations

**Example Data Structure**:
```json
{
  "conversation_id": "conv_123",
  "lead_id": "lead_456", 
  "context": {
    "current_intent": "demo_request",
    "interaction_count": 3,
    "last_message": "interested in pricing",
    "agent_notes": "high engagement level"
  },
  "expires_at": "2025-01-02T10:30:00Z"
}
```

#### 2. Long-term Memory (PostgreSQL)
- **Purpose**: Customer profiles, preferences, and interaction history
- **Technology**: PostgreSQL with JSONB for flexible schemas
- **Access Pattern**: Medium-frequency access, complex queries
- **Data Structure**: Relational tables with JSON fields for preferences
- **Persistence**: Permanent with backup strategies
- **Capacity**: Millions of customer records

**Schema Design**:
```sql
CREATE TABLE customer_profiles (
    lead_id VARCHAR(255) PRIMARY KEY,
    preferences JSONB,
    interaction_history JSONB[],
    rfm_score DECIMAL(3,3),
    created_at TIMESTAMP,
    last_updated TIMESTAMP
);

CREATE INDEX idx_rfm_score ON customer_profiles (rfm_score DESC);
CREATE INDEX idx_preferences ON customer_profiles USING GIN (preferences);
```

#### 3. Episodic Memory (ChromaDB Vector Database)
- **Purpose**: Successful interaction patterns for learning
- **Technology**: ChromaDB with sentence-transformers embeddings
- **Access Pattern**: Similarity search, infrequent writes
- **Data Structure**: Vector embeddings of successful episodes
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Similarity Threshold**: 0.7 for pattern matching

**Episode Structure**:
```json
{
  "episode_id": "ep_789",
  "scenario": "high_value_lead_nurturing",
  "context_embedding": [0.1, 0.2, ...], // 384-dimensional vector
  "action_sequence": [
    {"action": "send_personalized_email", "timing": "immediate"},
    {"action": "follow_up_call", "timing": "+2_days"},
    {"action": "demo_scheduling", "timing": "+5_days"}
  ],
  "outcome_score": 0.95,
  "metadata": {
    "industry": "technology",
    "company_size": "medium",
    "conversion_value": 15000
  }
}
```

#### 4. Semantic Memory (Neo4j Graph Database)
- **Purpose**: Domain knowledge relationships and concept associations
- **Technology**: Neo4j graph database
- **Access Pattern**: Graph traversal queries, relationship exploration
- **Data Structure**: Nodes (concepts) and edges (relationships)
- **Query Language**: Cypher for graph pattern matching
- **Relationship Types**: "RELATED_TO", "LEADS_TO", "IMPROVES", "REQUIRES"

**Graph Schema**:
```cypher
// Nodes
(:Concept {name: "email_marketing", category: "channel"})
(:Strategy {name: "nurture_sequence", effectiveness: 0.8})
(:Outcome {name: "demo_booked", value: "high"})

// Relationships
(:Concept)-[:ENABLES]->(:Strategy)
(:Strategy)-[:LEADS_TO]->(:Outcome)
(:Concept)-[:RELATED_TO {strength: 0.9}]->(:Concept)
```

### Memory Consolidation Strategy

#### Automatic Consolidation Rules
1. **Short → Long-term**: After 5+ interactions in a conversation
2. **Successful Patterns → Episodic**: Outcome score ≥ 0.8
3. **Frequent Patterns → Semantic**: Relationship strength ≥ 0.7

#### Consolidation Process
```python
async def consolidate_memory():
    # Move high-interaction conversations to long-term
    active_conversations = await short_term.get_high_activity()
    for conv in active_conversations:
        await consolidate_to_long_term(conv)
    
    # Extract successful patterns for episodic learning
    successful_outcomes = await get_recent_successes()
    for outcome in successful_outcomes:
        await store_episodic_pattern(outcome)
    
    # Update semantic relationships
    await update_concept_relationships()
```

## Alternatives Considered

### 1. Single Database Approach
**Rejected**: Different memory types have fundamentally different access patterns and optimization requirements.

### 2. All-Vector Database Solution
**Rejected**: While vector databases excel at similarity search, they're not optimal for structured queries and relationship traversal.

### 3. Traditional Cache + SQL Only
**Rejected**: Lacks the sophisticated learning capabilities required for adaptive behavior.

### 4. NoSQL Document Store Only
**Rejected**: Insufficient for graph relationships and vector similarity search.

## Consequences

### Positive
- **Optimized Performance**: Each memory type uses storage optimized for its access patterns
- **Scalability**: Different memory systems can scale independently
- **Rich Learning**: Vector embeddings and graph relationships enable sophisticated pattern recognition
- **Data Consistency**: Clear ownership and consolidation rules prevent conflicts
- **Query Flexibility**: Multiple query interfaces for different use cases

### Negative
- **Operational Complexity**: Four different database systems to maintain
- **Data Synchronization**: Requires careful design to maintain consistency
- **Infrastructure Costs**: Multiple specialized databases increase hosting costs
- **Development Overhead**: Different query languages and APIs to master

### Performance Characteristics

| Memory Type | Read Latency | Write Latency | Query Complexity | Capacity |
|-------------|--------------|---------------|------------------|----------|
| Short-term  | <1ms        | <1ms          | Simple K-V       | 10K records |
| Long-term   | <10ms       | <50ms         | Complex SQL      | Millions |
| Episodic    | <100ms      | <500ms        | Vector similarity| 100K episodes |
| Semantic    | <50ms       | <100ms        | Graph traversal  | 10K concepts |

### Security Considerations
- **Encryption**: All memory systems use encryption at rest and in transit
- **Access Control**: Role-based access with agent authentication
- **Data Retention**: Configurable retention policies for each memory type
- **Audit Logging**: All memory access operations are logged

### Monitoring and Health Checks
- **Connection Health**: Monitor database connections and response times
- **Memory Usage**: Track storage utilization and performance metrics
- **Consolidation Health**: Monitor consolidation job success rates
- **Query Performance**: Track slow queries and optimization opportunities

## Implementation Plan

### Phase 1: Core Infrastructure
- Set up Redis cluster for short-term memory
- Configure PostgreSQL with optimized schemas
- Initialize ChromaDB collection with embeddings
- Set up Neo4j with initial concept graph

### Phase 2: Memory Interfaces
- Implement unified memory manager interface
- Create type-specific memory adapters
- Add consolidation job scheduling
- Implement health check endpoints

### Phase 3: Learning Integration
- Connect episodic memory to agent decision-making
- Implement semantic relationship queries
- Add memory-based recommendation system
- Create memory analytics dashboard

### Phase 4: Optimization
- Implement query optimization and caching
- Add memory system monitoring
- Optimize consolidation algorithms
- Performance tuning and load testing

## Configuration

### Memory System Configuration
```yaml
memory_systems:
  short_term:
    type: redis
    host: redis-cluster.local
    port: 6379
    ttl_default: 3600  # 1 hour
    max_memory: "2gb"
  
  long_term:
    type: postgresql
    host: postgres.local
    database: marketing_memory
    pool_size: 20
    
  episodic:
    type: chromadb
    model: "sentence-transformers/all-MiniLM-L6-v2"
    collection: "marketing_episodes"
    similarity_threshold: 0.7
    
  semantic:
    type: neo4j
    uri: "bolt://neo4j.local:7687"
    database: "marketing_knowledge"
```

## Success Metrics
- **Memory Retrieval Speed**: <10ms for 95% of short-term queries
- **Consolidation Success Rate**: >99% of eligible conversations consolidated
- **Pattern Recognition Accuracy**: >85% similarity in episodic matching
- **Knowledge Graph Coverage**: >90% of marketing concepts mapped

## References
- [Redis Memory Optimization Guide](https://redis.io/docs/manual/memory-optimization/)
- [PostgreSQL JSONB Performance](https://www.postgresql.org/docs/current/datatype-json.html)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Neo4j Graph Data Modeling](https://neo4j.com/developer/graph-data-modeling/)

## Approval
- **Data Architecture Team**: Approved
- **Security Team**: Approved with encryption requirements
- **Performance Team**: Approved with monitoring plan
- **ML Team**: Approved with learning integration plan
