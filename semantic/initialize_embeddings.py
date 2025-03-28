"""
Initialize Embeddings Script - Sets up vector indices and generates embeddings for Tier 1 entities.

This script performs the initial setup required for semantic search functionality:
1. Creates vector indices in Neo4j
2. Classifies entity types into tiers
3. Generates embeddings for Tier 1 (highest priority) entities
"""

import os
import sys
import logging
import time
import argparse
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('embedding_initialization.log')
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from semantic.embedding_provider import SentenceTransformerProvider, DummyEmbeddingProvider
from semantic.entity_retriever import SemanticEntityRetriever
from semantic.tier_classification import TierClassifier
from graph_db.graph_strategy_factory import GraphDatabaseFactory

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Initialize vector embeddings for semantic search")
    
    parser.add_argument(
        "--model", 
        default="BAAI/bge-small-en-v1.5",
        help="Model name for sentence transformer (default: BAAI/bge-small-en-v1.5)"
    )
    
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=50,
        help="Batch size for embedding generation (default: 50)"
    )
    
    parser.add_argument(
        "--limit", 
        type=int, 
        default=1000,
        help="Maximum number of entities to process per tier (default: 1000)"
    )
    
    parser.add_argument(
        "--tiers", 
        type=int, 
        nargs="+", 
        default=[1],
        help="Tiers to process (default: 1)"
    )
    
    parser.add_argument(
        "--device", 
        default=None,
        help="Device to use for embedding model (default: auto-detect)"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Analyze without generating embeddings"
    )
    
    parser.add_argument(
        "--dummy", 
        action="store_true",
        help="Use dummy embedding provider (for testing)"
    )
    
    return parser.parse_args()

def main():
    """Main function to initialize embeddings."""
    args = parse_arguments()
    
    start_time = time.time()
    logger.info("Starting embedding initialization")
    logger.info(f"Arguments: {args}")
    
    # Connect to database
    graph_db = GraphDatabaseFactory.create_graph_database_strategy()
    if not graph_db.connect():
        logger.error("Failed to connect to graph database")
        return
    
    # Create embedding provider
    try:
        if args.dummy:
            logger.warning("Using dummy embedding provider (random vectors)")
            embedding_provider = DummyEmbeddingProvider()
        else:
            logger.info(f"Initializing embedding model: {args.model}")
            embedding_provider = SentenceTransformerProvider(
                model_name=args.model,
                device=args.device
            )
    except Exception as e:
        logger.error(f"Failed to initialize embedding provider: {e}")
        graph_db.close()
        return
    
    # Create entity retriever
    entity_retriever = SemanticEntityRetriever(graph_db, embedding_provider)
    
    # Create tier classifier
    tier_classifier = TierClassifier(graph_db)
    
    # Analyze schema and classify entity types
    logger.info("Analyzing schema and classifying entity types")
    tier_mappings = tier_classifier.analyze_schema()
    
    # Create vector indices
    if not args.dry_run:
        logger.info("Creating vector indices in Neo4j")
        dimension = 384  # Default dimension for BAAI/bge-small-en-v1.5
        
        # Create index for each entity type in Tier 1
        for entity_type in tier_mappings[1]:
            logger.info(f"Creating vector index for {entity_type}")
            entity_retriever.create_vector_index(entity_type, dimension)
    
    # Generate embeddings for requested tiers
    total_processed = 0
    total_success = 0
    total_fail = 0
    
    for tier in args.tiers:
        if tier not in tier_mappings or not tier_mappings[tier]:
            logger.warning(f"No entity types in Tier {tier}")
            continue
        
        logger.info(f"Processing Tier {tier}: {', '.join(tier_mappings[tier])}")
        
        for entity_type in tier_mappings[tier]:
            logger.info(f"Generating embeddings for {entity_type}")
            
            if args.dry_run:
                logger.info(f"[DRY RUN] Would process {entity_type}")
                continue
            
            # Generate embeddings
            stats = entity_retriever.generate_embeddings_for_tier(
                entity_type,
                batch_size=args.batch_size,
                limit=args.limit
            )
            
            # Update totals
            total_processed += stats.get("processed", 0)
            total_success += stats.get("successful", 0)
            total_fail += stats.get("failed", 0)
            
            logger.info(f"Processed {entity_type}: {stats}")
    
    # Log summary
    elapsed = time.time() - start_time
    logger.info(f"Embedding initialization completed in {elapsed:.2f}s")
    logger.info(f"Total processed: {total_processed}")
    logger.info(f"Total success: {total_success}")
    logger.info(f"Total fail: {total_fail}")
    
    # Close database connection
    graph_db.close()

if __name__ == "__main__":
    main()