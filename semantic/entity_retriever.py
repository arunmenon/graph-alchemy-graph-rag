"""
Semantic Entity Retriever Module - Implements hybrid search for entities.

This module provides the implementation of semantic search for entities in the graph database,
combining text-based and vector-based search approaches.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Union, Set
import time

from .embedding_provider import EmbeddingProvider, DummyEmbeddingProvider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticEntityRetriever:
    """Implements semantic search for entities in the graph database."""
    
    def __init__(self, graph_db, embedding_provider: Optional[EmbeddingProvider] = None):
        """
        Initialize the semantic entity retriever.
        
        Args:
            graph_db: Graph database connection
            embedding_provider: Provider for generating embeddings
        """
        self.graph_db = graph_db
        
        # Use provided embedding provider or create a dummy one
        self.embedding_provider = embedding_provider or DummyEmbeddingProvider()
        
        # Track stats for monitoring
        self.stats = {
            "total_searches": 0,
            "vector_searches": 0,
            "text_searches": 0,
            "hybrid_searches": 0,
            "total_time": 0
        }
    
    def search(self, query: str, entity_types: Optional[List[str]] = None, 
              threshold: float = 0.7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for entities matching the query.
        
        Args:
            query: Text query to search for
            entity_types: List of entity types to search within
            threshold: Minimum similarity threshold for vector search
            limit: Maximum number of results to return
            
        Returns:
            List of matching entities with scores
        """
        start_time = time.time()
        self.stats["total_searches"] += 1
        
        # Generate embedding for the query
        try:
            query_embedding = self.embedding_provider.encode(query)
            vector_search_available = True
            logger.info("Generated query embedding successfully")
        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}. Falling back to text search only.")
            vector_search_available = False
        
        # Build entity type filter
        entity_filter = ""
        if entity_types and len(entity_types) > 0:
            entity_filter = " WHERE " + " OR ".join([f"n:{entity_type}" for entity_type in entity_types])
        
        # Determine search strategy based on availability and query type
        if vector_search_available:
            # Use hybrid search
            self.stats["hybrid_searches"] += 1
            logger.info(f"Executing hybrid search for: {query}")
            results = self._execute_hybrid_search(query, query_embedding, entity_filter, threshold, limit)
        else:
            # Use text search as fallback
            self.stats["text_searches"] += 1
            logger.info(f"Executing text-only search for: {query}")
            results = self._execute_text_search(query, entity_filter, limit)
        
        # Track total time
        elapsed = time.time() - start_time
        self.stats["total_time"] += elapsed
        logger.info(f"Search completed in {elapsed:.2f}s, found {len(results)} results")
        
        return results
    
    def _execute_hybrid_search(self, text_query: str, query_embedding: List[float], 
                              entity_filter: str, threshold: float, limit: int) -> List[Dict[str, Any]]:
        """
        Execute a hybrid search combining vector and text approaches.
        
        Args:
            text_query: Original text query
            query_embedding: Vector embedding of the query
            entity_filter: Cypher WHERE clause for filtering entities
            threshold: Minimum similarity threshold
            limit: Maximum number of results
            
        Returns:
            List of matching entities with scores
        """
        # Check if vector index exists
        vector_index_exists = self._check_vector_index_exists()
        
        results = []
        
        # If vector index exists, try vector search first
        if vector_index_exists:
            vector_results = self._execute_vector_search(query_embedding, entity_filter, threshold, limit)
            results.extend(vector_results)
            
            # If we got enough results from vector search, return them
            if len(results) >= limit:
                return results[:limit]
        
        # Execute text search for remaining slots
        remaining_limit = limit - len(results)
        if remaining_limit > 0:
            text_results = self._execute_text_search(text_query, entity_filter, remaining_limit)
            
            # Filter out duplicates
            existing_ids = {r["id"] for r in results}
            filtered_text_results = [r for r in text_results if r["id"] not in existing_ids]
            
            # Add filtered text results
            results.extend(filtered_text_results)
        
        return results
    
    def _check_vector_index_exists(self) -> bool:
        """
        Check if vector index exists in the database.
        
        Returns:
            True if vector index exists, False otherwise
        """
        try:
            query = """
            SHOW INDEXES
            YIELD name, type, labelsOrTypes, properties
            WHERE type = 'VECTOR' 
            RETURN count(*) > 0 as has_vector_index
            """
            
            result = self.graph_db.execute_query(query)
            
            if result and len(result) > 0 and 'has_vector_index' in result[0]:
                return result[0]['has_vector_index']
            return False
        except Exception as e:
            logger.warning(f"Error checking vector index: {e}")
            return False
    
    def _execute_vector_search(self, query_embedding: List[float], entity_filter: str, 
                              threshold: float, limit: int) -> List[Dict[str, Any]]:
        """
        Execute vector similarity search.
        
        Args:
            query_embedding: Vector embedding of the query
            entity_filter: Cypher WHERE clause for filtering entities
            threshold: Minimum similarity threshold
            limit: Maximum number of results
            
        Returns:
            List of matching entities with scores
        """
        self.stats["vector_searches"] += 1
        
        try:
            # Convert embedding to JSON string for Cypher
            embedding_json = json.dumps(query_embedding)
            
            # Build the query with vector similarity
            query = f"""
            MATCH (n){entity_filter}
            WHERE n.embedding IS NOT NULL
            WITH n, gds.similarity.cosine(n.embedding, {embedding_json}) AS score
            WHERE score >= {threshold}
            RETURN id(n) AS id, labels(n) AS labels, properties(n) AS properties, score
            ORDER BY score DESC
            LIMIT {limit}
            """
            
            # Execute query
            result = self.graph_db.execute_query(query)
            
            # Format results
            return [self._format_result(r) for r in result]
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def _execute_text_search(self, text_query: str, entity_filter: str, limit: int) -> List[Dict[str, Any]]:
        """
        Execute text-based search.
        
        Args:
            text_query: Text query to search for
            entity_filter: Cypher WHERE clause for filtering entities
            limit: Maximum number of results
            
        Returns:
            List of matching entities with scores
        """
        self.stats["text_searches"] += 1
        
        # Prepare search terms
        search_terms = text_query.split()
        
        # Build the query with multiple search approaches
        if len(search_terms) > 0:
            # First try exact match on name or title
            exact_query = f"""
            MATCH (n){entity_filter}
            WHERE toLower(n.name) CONTAINS toLower('{text_query}') 
               OR toLower(n.title) CONTAINS toLower('{text_query}')
            RETURN id(n) AS id, labels(n) AS labels, properties(n) AS properties, 1.0 AS score
            LIMIT {limit}
            """
            
            # Then try partial matches on individual terms with descending weights
            term_query_parts = []
            for i, term in enumerate(search_terms[:3]):  # Limit to first 3 terms for performance
                weight = 0.9 - (i * 0.1)  # Decreasing weights: 0.9, 0.8, 0.7
                term_query_parts.append(f"""
                MATCH (n){entity_filter}
                WHERE any(prop IN keys(n) WHERE 
                    toLower(toString(n[prop])) CONTAINS toLower('{term}')
                )
                RETURN id(n) AS id, labels(n) AS labels, properties(n) AS properties, {weight} AS score
                """)
            
            term_query = " UNION ".join(term_query_parts)
            
            # Combine queries, remove duplicates, sort by score
            combined_query = f"""
            {exact_query}
            UNION
            {term_query}
            """
            
            deduplication_query = f"""
            WITH * FROM ({combined_query}) AS results
            WITH id, labels, properties, max(score) AS score
            ORDER BY score DESC
            LIMIT {limit}
            RETURN id, labels, properties, score
            """
            
            # Execute query
            try:
                result = self.graph_db.execute_query(deduplication_query)
                return [self._format_result(r) for r in result]
            except Exception as e:
                logger.error(f"Error in text search: {e}")
                
                # Try simpler fallback query if the complex one fails
                fallback_query = f"""
                MATCH (n){entity_filter}
                RETURN id(n) AS id, labels(n) AS labels, properties(n) AS properties, 0.5 AS score
                LIMIT {limit}
                """
                try:
                    result = self.graph_db.execute_query(fallback_query)
                    return [self._format_result(r) for r in result]
                except Exception as e2:
                    logger.error(f"Error in fallback text search: {e2}")
                    return []
        
        # If no search terms, return empty list
        return []
    
    def _format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format a result record into a standardized output format."""
        return {
            "id": str(result.get("id")),
            "labels": result.get("labels", []),
            "properties": result.get("properties", {}),
            "score": float(result.get("score", 0.0))
        }
    
    def create_vector_index(self, entity_label: str = "Entity", dimension: int = 384) -> bool:
        """
        Create a vector index in Neo4j for the specified entity label.
        
        Args:
            entity_label: Label of the entities to index
            dimension: Dimensionality of the embeddings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create the vector index
            query = f"""
            CREATE VECTOR INDEX entity_embeddings IF NOT EXISTS FOR (n:{entity_label}) ON (n.embedding)
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {dimension},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
            """
            
            self.graph_db.execute_query(query)
            logger.info(f"Created vector index for {entity_label} entities with dimension {dimension}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating vector index: {e}")
            return False
    
    def store_entity_embedding(self, entity_id: str, embedding: List[float]) -> bool:
        """
        Store an embedding for an entity.
        
        Args:
            entity_id: ID of the entity
            embedding: Embedding vector
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert embedding to JSON string for storage
            embedding_json = json.dumps(embedding)
            
            # Store the embedding
            query = f"""
            MATCH (n) WHERE id(n) = $entity_id
            SET n.embedding = $embedding
            RETURN id(n) as id
            """
            
            result = self.graph_db.execute_query(query, {
                "entity_id": int(entity_id),
                "embedding": embedding
            })
            
            success = result and len(result) > 0 and "id" in result[0]
            
            if success:
                logger.info(f"Stored embedding for entity {entity_id}")
            else:
                logger.warning(f"Failed to store embedding for entity {entity_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            return False
    
    def generate_embeddings_for_tier(self, tier_label: str, batch_size: int = 50, 
                                    property_name: str = "name", limit: int = 1000) -> Dict[str, Any]:
        """
        Generate and store embeddings for entities in a specific tier.
        
        Args:
            tier_label: Label of the tier to process
            batch_size: Number of entities to process at once
            property_name: Property to use for text representation
            limit: Maximum number of entities to process
            
        Returns:
            Dictionary with statistics about the generation process
        """
        start_time = time.time()
        
        try:
            # Get entities without embeddings
            query = f"""
            MATCH (n:{tier_label})
            WHERE n.{property_name} IS NOT NULL AND n.embedding IS NULL
            RETURN id(n) as id, n.{property_name} as text
            LIMIT {limit}
            """
            
            entities = self.graph_db.execute_query(query)
            
            if not entities:
                logger.info(f"No entities found for tier {tier_label} without embeddings")
                return {
                    "processed": 0,
                    "successful": 0,
                    "failed": 0,
                    "time": 0
                }
            
            logger.info(f"Generating embeddings for {len(entities)} {tier_label} entities")
            
            # Process in batches
            success_count = 0
            fail_count = 0
            
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i+batch_size]
                
                # Extract texts and IDs
                texts = [entity["text"] for entity in batch]
                ids = [entity["id"] for entity in batch]
                
                # Generate embeddings
                try:
                    embeddings = self.embedding_provider.batch_encode(texts, batch_size=batch_size)
                    
                    # Store embeddings
                    for j, (entity_id, embedding) in enumerate(zip(ids, embeddings)):
                        success = self.store_entity_embedding(entity_id, embedding)
                        if success:
                            success_count += 1
                        else:
                            fail_count += 1
                        
                    logger.info(f"Processed batch {i//batch_size + 1}/{(len(entities)-1)//batch_size + 1}")
                    
                except Exception as batch_error:
                    logger.error(f"Error processing batch: {batch_error}")
                    fail_count += len(batch)
            
            # Calculate statistics
            elapsed = time.time() - start_time
            
            stats = {
                "processed": len(entities),
                "successful": success_count,
                "failed": fail_count,
                "time": elapsed
            }
            
            logger.info(f"Embedding generation completed in {elapsed:.2f}s. "
                       f"Success: {success_count}, Failed: {fail_count}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return {
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "time": time.time() - start_time,
                "error": str(e)
            }