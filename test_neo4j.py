#!/usr/bin/env python3
"""
Simple test script for Neo4j connection.
"""

import os
import logging
from neo4j import GraphDatabase

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_neo4j_connection():
    """Test basic Neo4j connection"""
    # Default connection parameters
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "Rathum12!")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")
    
    try:
        logger.info(f"Connecting to Neo4j at {uri} with user {user}...")
        
        # Create driver
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test connection with a simple query
        with driver.session(database=database) as session:
            logger.info("Connection successful, executing test query...")
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            record = result.single()
            if record:
                count = record["node_count"]
                logger.info(f"Query executed successfully. Total nodes: {count}")
            else:
                logger.warning("Query returned no results")
        
        # Close driver
        driver.close()
        logger.info("Neo4j connection test completed successfully")
        
    except Exception as e:
        logger.error(f"Error connecting to Neo4j: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_neo4j_connection()