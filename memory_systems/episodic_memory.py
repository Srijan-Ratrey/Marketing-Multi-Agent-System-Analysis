"""
Episodic Memory Implementation

Vector database implementation for storing and retrieving successful interaction patterns.
Uses sentence transformers for semantic similarity matching.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import chromadb
except ImportError:
    chromadb = None

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """
    Vector database-based episodic memory for successful interaction patterns
    
    Features:
    - Semantic similarity search using embeddings
    - Storage of successful interaction episodes
    - Pattern matching for similar scenarios
    - Learning from past experiences
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        
    async def initialize(self):
        """Initialize vector database and embedding model"""
        try:
            # Initialize embedding model
            if SentenceTransformer:
                model_name = self.config.get("model_name", "all-MiniLM-L6-v2")
                self.embedding_model = SentenceTransformer(model_name)
                logger.info(f"Loaded embedding model: {model_name}")
            else:
                logger.warning("sentence-transformers not available - using mock embeddings")
            
            # Initialize ChromaDB
            if chromadb:
                self.chroma_client = chromadb.Client()
                collection_name = self.config.get("collection_name", "episodic_memory")
                
                try:
                    self.collection = self.chroma_client.get_collection(collection_name)
                except Exception:
                    # Create collection if it doesn't exist
                    self.collection = self.chroma_client.create_collection(collection_name)
                
                logger.info("ChromaDB collection initialized")
            else:
                logger.warning("ChromaDB not available - using in-memory fallback")
                self.memory_store = []
            
        except Exception as e:
            logger.warning(f"Episodic memory initialization error: {e} - using fallback")
            self.embedding_model = None
            self.chroma_client = None
            self.memory_store = []
    
    def _create_embedding(self, text: str) -> List[float]:
        """Create embedding vector from text"""
        if self.embedding_model:
            return self.embedding_model.encode(text).tolist()
        else:
            # Mock embedding for fallback
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            # Convert hash to pseudo-embedding
            hash_int = int(hash_obj.hexdigest(), 16)
            # Create 384-dimensional mock embedding
            mock_embedding = [(hash_int >> i) % 256 / 255.0 - 0.5 for i in range(384)]
            return mock_embedding
    
    def _episode_to_text(self, episode: Dict[str, Any]) -> str:
        """Convert episode to searchable text"""
        text_parts = []
        
        # Add scenario
        if "scenario" in episode:
            text_parts.append(f"scenario: {episode['scenario']}")
        
        # Add context
        context = episode.get("context", {})
        for key, value in context.items():
            text_parts.append(f"{key}: {value}")
        
        # Add action sequence
        actions = episode.get("action_sequence", [])
        if actions:
            action_text = " ".join([str(action) for action in actions])
            text_parts.append(f"actions: {action_text}")
        
        return " | ".join(text_parts)
    
    async def store(self, episode_id: str, episode: Dict[str, Any]) -> bool:
        """Store successful episode for learning"""
        try:
            # Convert episode to searchable text
            episode_text = self._episode_to_text(episode)
            
            # Create embedding
            embedding = self._create_embedding(episode_text)
            
            if self.collection:
                # Store in ChromaDB
                self.collection.add(
                    ids=[episode_id],
                    embeddings=[embedding],
                    documents=[episode_text],
                    metadatas=[{
                        "scenario": episode.get("scenario", ""),
                        "agent_type": episode.get("agent_type", ""),
                        "outcome_score": episode.get("outcome_score", 0.0),
                        "timestamp": episode.get("timestamp", datetime.now().isoformat()),
                        "episode_data": json.dumps(episode, default=str)
                    }]
                )
            else:
                # Store in memory fallback
                self.memory_store.append({
                    "id": episode_id,
                    "embedding": embedding,
                    "text": episode_text,
                    "metadata": episode
                })
            
            logger.info(f"Stored episodic memory: {episode_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing episodic memory: {e}")
            return False
    
    async def search_similar(
        self, 
        query_text: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar episodes"""
        try:
            # Create query embedding
            query_embedding = self._create_embedding(query_text)
            
            if self.collection:
                # Search in ChromaDB
                where_clause = {}
                if filters:
                    for key, value in filters.items():
                        if key in ["scenario", "agent_type"]:
                            where_clause[key] = value
                
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where=where_clause if where_clause else None
                )
                
                # Parse results
                similar_episodes = []
                if results and results["metadatas"]:
                    for i, metadata in enumerate(results["metadatas"][0]):
                        episode_data = json.loads(metadata.get("episode_data", "{}"))
                        episode_data["similarity_score"] = 1.0 - (results["distances"][0][i] if results["distances"] else 0.0)
                        similar_episodes.append(episode_data)
                
                return similar_episodes
            
            else:
                # Search in memory fallback
                def cosine_similarity(a, b):
                    dot_product = sum(x * y for x, y in zip(a, b))
                    magnitude_a = sum(x * x for x in a) ** 0.5
                    magnitude_b = sum(x * x for x in b) ** 0.5
                    if magnitude_a == 0 or magnitude_b == 0:
                        return 0
                    return dot_product / (magnitude_a * magnitude_b)
                
                # Calculate similarities
                similarities = []
                for stored in self.memory_store:
                    similarity = cosine_similarity(query_embedding, stored["embedding"])
                    
                    # Apply filters
                    if filters:
                        metadata = stored["metadata"]
                        if not all(metadata.get(k) == v for k, v in filters.items() if k in metadata):
                            continue
                    
                    similarities.append({
                        **stored["metadata"],
                        "similarity_score": similarity
                    })
                
                # Sort by similarity and return top results
                similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
                return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Error searching episodic memory: {e}")
            return []
    
    async def get_recent_successes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent successful episodes for learning"""
        try:
            if self.collection:
                # Query ChromaDB for recent high-scoring episodes
                results = self.collection.query(
                    query_embeddings=[self._create_embedding("successful interaction")],
                    n_results=limit,
                    where={"outcome_score": {"$gte": 0.7}}  # High success threshold
                )
                
                episodes = []
                if results and results["metadatas"]:
                    for metadata in results["metadatas"][0]:
                        episode_data = json.loads(metadata.get("episode_data", "{}"))
                        episodes.append(episode_data)
                
                return episodes
            else:
                # Filter memory store for successful episodes
                successful = [
                    stored["metadata"] for stored in self.memory_store
                    if stored["metadata"].get("outcome_score", 0) >= 0.7
                ]
                
                # Sort by timestamp (recent first)
                successful.sort(
                    key=lambda x: x.get("timestamp", ""), 
                    reverse=True
                )
                
                return successful[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent successes: {e}")
            return []
    
    async def get_status(self) -> Dict[str, Any]:
        """Get episodic memory status"""
        try:
            if self.collection:
                count = self.collection.count()
                return {
                    "type": "chromadb",
                    "status": "connected",
                    "episode_count": count,
                    "embedding_model": self.config.get("model_name", "all-MiniLM-L6-v2")
                }
            else:
                return {
                    "type": "in_memory",
                    "status": "active",
                    "episode_count": len(getattr(self, 'memory_store', [])),
                    "embedding_model": "mock"
                }
                
        except Exception as e:
            return {
                "type": "unknown",
                "status": "error",
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        # ChromaDB client doesn't need explicit cleanup
        # Embedding model is handled by garbage collection
        pass
