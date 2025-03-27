#!/usr/bin/env python3
"""
Test script for Neo4j connection and schema loading.

This script verifies the Neo4j connection and loads the schema.
"""

import os
import sys
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from graph_db.neo4j_database import Neo4jDatabase
from schema.core.schema_loader import Neo4jSchemaLoader
from graph_db.graph_strategy_factory import GraphDatabaseFactory

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to test Neo4j connectivity and schema loading."""
    # Create a Neo4j database instance with direct credentials
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")
    
    logger.info(f"Connecting to Neo4j at {uri}...")
    db = Neo4jDatabase(uri=uri, user=user, password=password, database=database)
    
    try:
        # Connect to Neo4j
        if db.connect():
            logger.info("Successfully connected to Neo4j!")
            
            # Test a simple query
            query = "MATCH (n) RETURN labels(n) as labels, count(n) as count GROUP BY labels(n) LIMIT 5"
            logger.info(f"Executing query: {query}")
            results = db.execute_query(query)
            
            if results:
                logger.info("Query results:")
                for row in results:
                    logger.info(f"  - {row}")
            else:
                logger.info("No results returned")
            
            # Test loading schema
            logger.info("Creating schema loader...")
            schema_loader = Neo4jSchemaLoader(db_factory=GraphDatabaseFactory)
            
            logger.info("Loading schema...")
            schema = schema_loader.load_schema(force_refresh=True)
            
            logger.info("Schema loaded successfully")
            logger.info(f"Found {len(schema.get('node_types', {}))} node types")
            logger.info(f"Found {len(schema.get('relationship_types', {}))} relationship types")
            logger.info(f"Found {len(schema.get('relationships', []))} relationship patterns")
            
            # Print formatted schema
            formatted_schema = schema_loader.get_formatted_schema()
            logger.info("Formatted schema:")
            logger.info(formatted_schema)
            
            # Close the connection
            db.close()
            logger.info("Neo4j connection closed")
        else:
            logger.error("Failed to connect to Neo4j")
    except Exception as e:
        logger.error(f"Error: {e}")
    
if __name__ == "__main__":
    main()