"""
Semantic Memory Implementation

Neo4j graph database implementation for domain knowledge relationships and concept associations.
Provides graph traversal queries and relationship exploration.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

try:
    import networkx as nx
except ImportError:
    nx = None

try:
    from neo4j import AsyncGraphDatabase
except ImportError:
    AsyncGraphDatabase = None

logger = logging.getLogger(__name__)


class SemanticMemory:
    """
    Neo4j-based semantic memory for domain knowledge relationships
    
    Features:
    - Graph-based knowledge representation
    - Relationship traversal and discovery
    - Concept association mapping
    - Domain knowledge storage
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.driver = None
        self.graph = None  # NetworkX fallback
        
    async def initialize(self):
        """Initialize Neo4j connection"""
        try:
            # Try to connect to Neo4j
            if AsyncGraphDatabase:
                uri = self.config.get("uri", "bolt://localhost:7687")
                user = self.config.get("user", "neo4j")
                password = self.config.get("password", "password")
                
                self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
                
                # Test connection
                async with self.driver.session() as session:
                    result = await session.run("RETURN 1 as test")
                    await result.single()
                
                logger.info("Semantic memory (Neo4j) initialized successfully")
                
            else:
                raise ImportError("Neo4j driver not available")
                
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e} - using NetworkX fallback")
            self.driver = None
            
            # Initialize NetworkX fallback
            if nx:
                self.graph = nx.DiGraph()
                await self._initialize_default_knowledge()
                logger.info("Semantic memory (NetworkX) initialized as fallback")
            else:
                logger.error("Neither Neo4j nor NetworkX available for semantic memory")
    
    async def _initialize_default_knowledge(self):
        """Initialize default marketing knowledge graph"""
        if not self.graph:
            return
        
        # Add basic marketing concepts and relationships
        concepts = [
            # Channels
            ("email_marketing", {"type": "channel", "category": "digital"}),
            ("social_media", {"type": "channel", "category": "digital"}),
            ("content_marketing", {"type": "channel", "category": "digital"}),
            ("paid_search", {"type": "channel", "category": "paid"}),
            ("organic_search", {"type": "channel", "category": "organic"}),
            
            # Strategies
            ("lead_nurturing", {"type": "strategy", "category": "engagement"}),
            ("retargeting", {"type": "strategy", "category": "optimization"}),
            ("personalization", {"type": "strategy", "category": "engagement"}),
            ("segmentation", {"type": "strategy", "category": "targeting"}),
            
            # Outcomes
            ("conversion", {"type": "outcome", "value": "high"}),
            ("engagement", {"type": "outcome", "value": "medium"}),
            ("awareness", {"type": "outcome", "value": "low"}),
            
            # Industries
            ("technology", {"type": "industry", "fit": "high"}),
            ("financial_services", {"type": "industry", "fit": "high"}),
            ("healthcare", {"type": "industry", "fit": "medium"}),
            ("retail", {"type": "industry", "fit": "medium"}),
        ]
        
        # Add nodes
        for concept, attributes in concepts:
            self.graph.add_node(concept, **attributes)
        
        # Add relationships
        relationships = [
            # Channel -> Strategy relationships
            ("email_marketing", "lead_nurturing", {"type": "enables", "strength": 0.9}),
            ("social_media", "engagement", {"type": "drives", "strength": 0.8}),
            ("content_marketing", "lead_nurturing", {"type": "supports", "strength": 0.8}),
            ("paid_search", "retargeting", {"type": "enables", "strength": 0.7}),
            
            # Strategy -> Outcome relationships
            ("lead_nurturing", "conversion", {"type": "leads_to", "strength": 0.8}),
            ("personalization", "engagement", {"type": "improves", "strength": 0.9}),
            ("segmentation", "conversion", {"type": "optimizes", "strength": 0.7}),
            ("retargeting", "conversion", {"type": "increases", "strength": 0.6}),
            
            # Industry -> Strategy relationships
            ("technology", "personalization", {"type": "prefers", "strength": 0.8}),
            ("financial_services", "content_marketing", {"type": "responds_to", "strength": 0.7}),
            ("healthcare", "email_marketing", {"type": "suitable_for", "strength": 0.6}),
        ]
        
        # Add edges
        for source, target, attributes in relationships:
            self.graph.add_edge(source, target, **attributes)
    
    async def store_triple(self, triple: Dict[str, Any]) -> bool:
        """Store knowledge triple (subject, predicate, object)"""
        try:
            subject = triple["subject"]
            predicate = triple["predicate"]
            obj = triple["object"]
            weight = triple.get("weight", 1.0)
            source = triple.get("source", "system")
            
            if self.driver:
                # Store in Neo4j
                async with self.driver.session() as session:
                    await session.run("""
                        MERGE (s:Concept {name: $subject})
                        MERGE (o:Concept {name: $object})
                        MERGE (s)-[r:RELATED {type: $predicate}]->(o)
                        SET r.weight = $weight, r.source = $source, r.created_at = datetime()
                    """, subject=subject, object=obj, predicate=predicate, weight=weight, source=source)
            
            elif self.graph:
                # Store in NetworkX
                if not self.graph.has_node(subject):
                    self.graph.add_node(subject, type="concept")
                if not self.graph.has_node(obj):
                    self.graph.add_node(obj, type="concept")
                
                self.graph.add_edge(subject, obj, 
                                  type=predicate, 
                                  weight=weight, 
                                  source=source,
                                  created_at=datetime.now().isoformat())
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing semantic triple: {e}")
            return False
    
    async def query_triples(
        self, 
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        object: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query knowledge triples"""
        try:
            triples = []
            
            if self.driver:
                # Query Neo4j
                query_parts = []
                params = {}
                
                if subject:
                    query_parts.append("s.name = $subject")
                    params["subject"] = subject
                if predicate:
                    query_parts.append("r.type = $predicate")
                    params["predicate"] = predicate
                if object:
                    query_parts.append("o.name = $object")
                    params["object"] = object
                
                where_clause = "WHERE " + " AND ".join(query_parts) if query_parts else ""
                
                query = f"""
                    MATCH (s:Concept)-[r:RELATED]->(o:Concept)
                    {where_clause}
                    RETURN s.name as subject, r.type as predicate, o.name as object, 
                           r.weight as weight, r.source as source
                """
                
                async with self.driver.session() as session:
                    result = await session.run(query, **params)
                    async for record in result:
                        triples.append({
                            "subject": record["subject"],
                            "predicate": record["predicate"],
                            "object": record["object"],
                            "weight": record["weight"],
                            "source": record["source"]
                        })
            
            elif self.graph:
                # Query NetworkX
                for source_node, target_node, edge_data in self.graph.edges(data=True):
                    # Apply filters
                    if subject and source_node != subject:
                        continue
                    if object and target_node != object:
                        continue
                    if predicate and edge_data.get("type") != predicate:
                        continue
                    
                    triples.append({
                        "subject": source_node,
                        "predicate": edge_data.get("type", "related_to"),
                        "object": target_node,
                        "weight": edge_data.get("weight", 1.0),
                        "source": edge_data.get("source", "system")
                    })
            
            return triples
            
        except Exception as e:
            logger.error(f"Error querying semantic triples: {e}")
            return []
    
    async def get_related_concepts(
        self, 
        concept: str, 
        relationship_types: Optional[List[str]] = None,
        depth: int = 2
    ) -> List[Dict[str, Any]]:
        """Get concepts related to given concept"""
        try:
            related = []
            
            if self.driver:
                # Query Neo4j with variable depth
                type_filter = ""
                if relationship_types:
                    type_filter = f"WHERE r.type IN {relationship_types}"
                
                query = f"""
                    MATCH (start:Concept {{name: $concept}})-[r:RELATED*1..{depth}]->(related:Concept)
                    {type_filter}
                    RETURN related.name as concept, 
                           [rel in r | rel.type] as path_types,
                           [rel in r | rel.weight] as path_weights
                """
                
                async with self.driver.session() as session:
                    result = await session.run(query, concept=concept)
                    async for record in result:
                        related.append({
                            "concept": record["concept"],
                            "path_types": record["path_types"],
                            "path_weights": record["path_weights"],
                            "distance": len(record["path_types"])
                        })
            
            elif self.graph:
                # Use NetworkX traversal
                if concept not in self.graph:
                    return []
                
                # BFS traversal up to specified depth
                visited = set()
                queue = [(concept, 0, [])]  # (node, depth, path)
                
                while queue:
                    current, curr_depth, path = queue.pop(0)
                    
                    if current in visited or curr_depth >= depth:
                        continue
                    
                    visited.add(current)
                    
                    # Get neighbors
                    for neighbor in self.graph.neighbors(current):
                        if neighbor not in visited:
                            edge_data = self.graph.get_edge_data(current, neighbor)
                            edge_type = edge_data.get("type", "related_to")
                            
                            # Apply relationship type filter
                            if relationship_types and edge_type not in relationship_types:
                                continue
                            
                            new_path = path + [edge_type]
                            
                            if curr_depth + 1 < depth:
                                queue.append((neighbor, curr_depth + 1, new_path))
                            
                            if neighbor != concept:  # Don't include the starting concept
                                related.append({
                                    "concept": neighbor,
                                    "path_types": new_path,
                                    "distance": curr_depth + 1,
                                    "relationship": edge_type
                                })
            
            return related
            
        except Exception as e:
            logger.error(f"Error getting related concepts: {e}")
            return []
    
    async def get_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find shortest path between two concepts"""
        try:
            if self.driver:
                # Use Neo4j shortest path
                query = """
                    MATCH path = shortestPath((s:Concept {name: $source})-[*]-(t:Concept {name: $target}))
                    RETURN [node in nodes(path) | node.name] as path
                """
                
                async with self.driver.session() as session:
                    result = await session.run(query, source=source, target=target)
                    record = await result.single()
                    return record["path"] if record else None
            
            elif self.graph:
                # Use NetworkX shortest path
                if self.graph.has_node(source) and self.graph.has_node(target):
                    try:
                        path = nx.shortest_path(self.graph, source, target)
                        return path
                    except nx.NetworkXNoPath:
                        return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding shortest path: {e}")
            return None
    
    async def get_status(self) -> Dict[str, Any]:
        """Get semantic memory status"""
        try:
            if self.driver:
                async with self.driver.session() as session:
                    # Count nodes and relationships
                    result = await session.run("MATCH (n:Concept) RETURN count(n) as node_count")
                    node_count = (await result.single())["node_count"]
                    
                    result = await session.run("MATCH ()-[r:RELATED]->() RETURN count(r) as rel_count")
                    rel_count = (await result.single())["rel_count"]
                    
                    return {
                        "type": "neo4j",
                        "status": "connected",
                        "concept_count": node_count,
                        "relationship_count": rel_count
                    }
            
            elif self.graph:
                return {
                    "type": "networkx",
                    "status": "active",
                    "concept_count": self.graph.number_of_nodes(),
                    "relationship_count": self.graph.number_of_edges()
                }
            
            else:
                return {
                    "type": "none",
                    "status": "unavailable"
                }
                
        except Exception as e:
            return {
                "type": "unknown",
                "status": "error",
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup connections"""
        if self.driver:
            await self.driver.close()
