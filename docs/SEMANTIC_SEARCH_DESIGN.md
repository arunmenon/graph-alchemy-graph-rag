# Semantic Search Implementation Design

## Overview

This document outlines the implementation design for adding semantic search capabilities to the Graph RAG system. The design prioritizes performance, accuracy, and incremental deployment.

## Key Components

### 1. Embedding Model Selection

We will use lightweight, high-performing embedding models:

- **Primary Model**: BAAI/bge-small-en-v1.5 (33M parameters)
  - 384 dimensions
  - MTEB Score: 62.9
  - Optimized for text similarity and retrieval tasks

- **Alternative Options**:
  - sentence-transformers/all-MiniLM-L6-v2 (22M parameters)
  - intfloat/e5-small-v2 (33M parameters)

### 2. Embedding Storage Strategy

Rather than embedding all nodes upfront, we will implement a phased approach:

1. **Priority Tier System**:
   - Tier 1: Key entity types (Tables, Primary Concepts)
   - Tier 2: Secondary entities with high connectivity
   - Tier 3: All remaining entities

2. **Progressive Processing**:
   - Begin with Tier 1 entities for immediate value
   - Process remaining tiers in background tasks
   - Track embedding coverage with metrics

3. **On-Demand Generation**:
   - Generate embeddings for frequently accessed entities
   - Cache search term embeddings for common queries

### 3. Neo4j Vector Index Configuration

```cypher
CREATE VECTOR INDEX entity_embeddings FOR (n:Entity) ON (n.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 384,
  `vector.similarity_function`: 'cosine'
}}
```

### 4. Hybrid Search Implementation

The search flow combines multiple approaches:

1. **Initial Text Search** (fast, broad coverage)
   - Leverages Neo4j's built-in text capabilities
   - Uses CONTAINS, exact matching, and fuzzy matching

2. **Semantic Vector Search** (high relevance)
   - For entities with embeddings
   - Configurable similarity threshold

3. **Relationship-Based Enhancement**
   - Explores graph connections from initial results
   - Applies weighting based on relationship types

### 5. Entity Retrieval Classes

```python
class SemanticEntityRetriever:
    def __init__(self, graph_db, embedding_provider):
        self.graph_db = graph_db
        self.embedding_provider = embedding_provider
        
    def search(self, query, entity_types=None, threshold=0.7, limit=10):
        # Generate embedding
        query_embedding = self.embedding_provider.encode(query)
        
        # Build and execute search
        results = self._execute_hybrid_search(
            query, 
            query_embedding,
            entity_types,
            threshold,
            limit
        )
        
        return results
        
    def _execute_hybrid_search(self, text_query, vector_query, entity_types, threshold, limit):
        # Implementation details...
```

## Processing Workflow

### 1. Embedding Generation Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐     ┌───────────────┐
│ Extract Node │────▶│ Prepare Text │────▶│ Batch Encoding │────▶│ Store in Neo4j│
│  Properties  │     │ Representation│     │                │     │               │
└─────────────┘     └──────────────┘     └────────────────┘     └───────────────┘
```

### 2. Search Execution Flow

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐     ┌───────────────┐
│ Process User│────▶│Execute Hybrid│────▶│ Traverse Graph │────▶│ Rank & Return │
│   Query     │     │    Search    │     │ Relationships  │     │    Results    │
└─────────────┘     └──────────────┘     └────────────────┘     └───────────────┘
```

## Performance Considerations

### 1. Batch Processing

- Process embeddings in batches of 50-100 nodes
- Implement rate limiting for external embedding APIs
- Use background workers for processing

### 2. Caching Strategy

- Cache query embeddings for 24 hours
- Implement LRU cache for frequent entities
- Store embeddings directly in Neo4j for query-time retrieval

### 3. Resource Requirements

| Resource | Requirement |
|----------|-------------|
| Memory   | 2-4GB for embedding model |
| Storage  | ~400 bytes per node (384 dim × 4 bytes + overhead) |
| CPU      | 4+ cores recommended for parallel processing |
| GPU      | Optional, can speed up embedding generation 5-10x |

## Implementation Roadmap

### Phase 1: Core Implementation

1. Set up embedding infrastructure
2. Implement Tier 1 entity embedding generation
3. Create vector indices in Neo4j
4. Develop basic hybrid search

### Phase 2: Enhancements

1. Add background processing for remaining tiers
2. Implement relationship-based result enhancement
3. Add caching layers for performance
4. Create monitoring and metrics

### Phase 3: Advanced Features

1. Implement entity disambiguation
2. Add multi-hop semantic search
3. Develop query-specific embedding tuning
4. Create user feedback loops for improvement

## Conclusion

This semantic search implementation will significantly enhance the Graph RAG system's ability to understand user queries and find relevant information. The design prioritizes an incremental approach that delivers immediate value while building toward comprehensive coverage.