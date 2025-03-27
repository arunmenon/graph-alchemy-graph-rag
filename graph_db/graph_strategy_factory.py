"""
Graph Database Factory - Creates appropriate graph database implementation based on configuration.

This module provides a factory for creating graph database connections
using the Strategy pattern.
"""

import os
import logging
from typing import Dict, Any, Optional

# Configure logger first to avoid recursion
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Then import implementation classes
from .graph_interface import GraphDatabaseInterface
from .neo4j_database import Neo4jDatabase
from .tigergraph_database import TigerGraphDatabase

class GraphDatabaseFactory:
    """Factory for creating graph database strategy implementations."""
    
    _instance = None
    
    @staticmethod
    def create_graph_database_strategy(db_type: Optional[str] = None) -> GraphDatabaseInterface:
        """
        Create and return an appropriate graph database implementation.
        
        Args:
            db_type: Type of database to use ('neo4j', 'tigergraph', or None to use environment)
            
        Returns:
            GraphDatabaseInterface: Graph database implementation
        """
        # Determine database type from environment if not specified
        if not db_type:
            db_type = os.environ.get("GRAPH_DB_TYPE", "neo4j").lower()
        
        try:
            # Create the appropriate database implementation
            if db_type == "tigergraph":
                logger.info("Creating TigerGraph database implementation")
                return TigerGraphDatabase()
            else:
                # Default to Neo4j
                logger.info("Creating Neo4j database implementation")
                # Check if neo4j is available
                if hasattr(Neo4jDatabase, 'NEO4J_AVAILABLE') and not Neo4jDatabase.NEO4J_AVAILABLE:
                    logger.warning("Neo4j driver not available, creating mock implementation")
                    # Return a basic mock implementation if Neo4j not available
                    from .graph_interface import GraphDatabaseInterface
                    class MockDatabase(GraphDatabaseInterface):
                        def connect(self): 
                            logger.warning("Mock database does not support real connections")
                            return False
                        def close(self): return True
                        def execute_query(self, query, params=None): return []
                    return MockDatabase()
                else:
                    return Neo4jDatabase()
        except Exception as e:
            logger.error(f"Error creating database implementation: {e}")
            # Return a minimal implementation that doesn't throw errors
            from .graph_interface import GraphDatabaseInterface
            class ErrorDatabase(GraphDatabaseInterface):
                def connect(self): return False
                def close(self): return True
                def execute_query(self, query, params=None): return []
            return ErrorDatabase()