"""
Neo4j Database Implementation - Implementation of the graph database interface for Neo4j.

This module provides a Neo4j implementation of the GraphDatabaseInterface.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from .graph_interface import GraphDatabaseInterface

# Configure module logger before imports to prevent recursion issues
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import neo4j with detailed error reporting
try:
    import sys
    import os
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python path: {sys.path}")
    
    # Try to find neo4j in the virtual environment
    if os.path.exists("venv/lib/python3.13/site-packages/neo4j"):
        logger.info("Neo4j found in venv, adding to path")
        sys.path.append(os.path.abspath("venv/lib/python3.13/site-packages"))
    
    # Try import again    
    import neo4j
    logger.info(f"Neo4j driver version: {neo4j.__version__}")
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
    logger.info("Neo4j driver successfully imported")
except ImportError as e:
    NEO4J_AVAILABLE = False
    logger.warning(f"Neo4j Python driver not available: {e}. Please install with 'pip install neo4j'")
    
    # Create mock GraphDatabase for implementation
    class MockGraphDatabase:
        @staticmethod
        def driver(*args, **kwargs):
            class MockDriver:
                def session(self, *args, **kwargs):
                    class MockSession:
                        def run(self, *args, **kwargs):
                            class MockResult:
                                def single(self):
                                    return {"test": 1}
                                def data(self):
                                    return [{"name": "Asset"}, {"name": "ProductLoss"}]
                            return MockResult()
                        def __enter__(self):
                            return self
                        def __exit__(self, *args):
                            pass
                    return MockSession()
                def close(self):
                    pass
            return MockDriver()
    
    # Use mock if real driver not available
    if 'GraphDatabase' not in locals():
        GraphDatabase = MockGraphDatabase

class Neo4jDatabase(GraphDatabaseInterface):
    """Neo4j implementation of the GraphDatabaseInterface."""

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None, database: Optional[str] = None):
        """
        Initialize the Neo4j database connection parameters.

        Args:
            uri: Neo4j URI (e.g. "neo4j://localhost:7687")
            user: Neo4j username
            password: Neo4j password
            database: Neo4j database name
        """
        # Use environment variables if not provided
        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.environ.get("NEO4J_USER", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD", "password")
        self.database = database or os.environ.get("NEO4J_DATABASE", "neo4j")
        self.driver = None

    def connect(self) -> bool:
        """
        Connect to the Neo4j database.

        Returns:
            bool: True if connection successful, False otherwise
        """
        if not NEO4J_AVAILABLE:
            logger.error("Neo4j Python driver not installed. Please install with 'pip install neo4j'")
            return False
            
        try:
            logger.info(f"Connecting to Neo4j at {self.uri}...")
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            
            # Test the connection
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                result.single()
                
            logger.info("Neo4j connection successful")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Neo4j: {e}")
            return False

    def close(self) -> bool:
        """
        Close the connection to the Neo4j database.

        Returns:
            bool: True if close successful, False otherwise
        """
        try:
            if self.driver:
                self.driver.close()
                self.driver = None
                logger.info("Neo4j connection closed")
            return True
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {e}")
            return False

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query against the Neo4j database.

        Args:
            query: Cypher query string
            params: Optional parameters for the query

        Returns:
            List[Dict[str, Any]]: Results from the query
        """
        if not self.driver:
            logger.error("Not connected to Neo4j. Call connect() first.")
            return []
            
        # Only log the first 100 chars to prevent excessive logging
        query_preview = query[:100] + "..." if len(query) > 100 else query
        logger.info(f"Executing query: {query_preview}")
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters=params or {})
                records = list(result)
                logger.info(f"Query executed successfully, returned {len(records)} records")
                return [record.data() for record in records]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            # Log the failed query to a separate file for review
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                failed_query_log = f"failed_query_{timestamp}.log"
                with open(failed_query_log, "w") as log_file:
                    log_file.write(f"Failed query:\n{query}\nError: {str(e)}\n\n")
            except Exception as log_err:
                # Don't let logging errors cause cascading failures
                logger.error(f"Failed to log query error: {log_err}")
            return []

    def create_node(self, label: str, properties: Dict[str, Any]) -> Optional[str]:
        """
        Create a node in Neo4j.

        Args:
            label: The label for the node
            properties: The properties for the node

        Returns:
            Optional[str]: The ID of the created node, or None if creation failed
        """
        if not self.driver:
            logger.error("Not connected to Neo4j. Call connect() first.")
            return None
            
        try:
            cypher = f"CREATE (n:{label} $props) RETURN id(n) as node_id"
            result = self.execute_query(cypher, {"props": properties})
            if result and result[0].get('node_id') is not None:
                return str(result[0]['node_id'])
            return None
        except Exception as e:
            logger.error(f"Error creating node: {e}")
            return None

    def create_relationship(self, start_node_id: str, end_node_id: str, 
                           rel_type: str, properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a relationship between two nodes.

        Args:
            start_node_id: The ID of the starting node
            end_node_id: The ID of the ending node
            rel_type: The type of relationship
            properties: Optional properties for the relationship

        Returns:
            bool: True if relationship created successfully, False otherwise
        """
        if not self.driver:
            logger.error("Not connected to Neo4j. Call connect() first.")
            return False
            
        try:
            cypher = f"""
            MATCH (a), (b) 
            WHERE id(a) = $start_id AND id(b) = $end_id
            CREATE (a)-[r:{rel_type} $props]->(b)
            RETURN id(r) as rel_id
            """
            result = self.execute_query(cypher, {
                "start_id": int(start_node_id),
                "end_id": int(end_node_id),
                "props": properties or {}
            })
            return bool(result and result[0].get('rel_id') is not None)
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            return False

    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by its ID.

        Args:
            node_id: The ID of the node to get

        Returns:
            Optional[Dict[str, Any]]: The node properties or None if not found
        """
        if not self.driver:
            logger.error("Not connected to Neo4j. Call connect() first.")
            return None
            
        try:
            result = self.execute_query(
                "MATCH (n) WHERE id(n) = $node_id RETURN n",
                {"node_id": int(node_id)}
            )
            if result and 'n' in result[0]:
                node = result[0]['n']
                return {
                    "id": node_id,
                    "labels": list(node.labels),
                    "properties": dict(node)
                }
            return None
        except Exception as e:
            logger.error(f"Error getting node: {e}")
            return None
        
    def get_nodes_by_label(self, label: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get nodes by label.

        Args:
            label: The label to search for
            limit: Maximum number of nodes to return

        Returns:
            List[Dict[str, Any]]: List of nodes with their properties
        """
        if not self.driver:
            logger.error("Not connected to Neo4j. Call connect() first.")
            return []
            
        try:
            # Ensure label doesn't contain any Cypher injection
            safe_label = label.replace('`', '').replace(':', '')
            result = self.execute_query(
                f"MATCH (n:{safe_label}) RETURN id(n) as id, n LIMIT $limit",
                {"limit": limit}
            )
            
            nodes = []
            for record in result:
                node = record['n']
                nodes.append({
                    "id": str(record['id']),
                    "labels": list(node.labels),
                    "properties": dict(node)
                })
            return nodes
        except Exception as e:
            logger.error(f"Error getting nodes by label: {e}")
            return []

    def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """
        Update a node's properties.

        Args:
            node_id: The ID of the node to update
            properties: The properties to update

        Returns:
            bool: True if update successful, False otherwise
        """
        if not self.driver:
            logger.error("Not connected to Neo4j. Call connect() first.")
            return False
            
        try:
            result = self.execute_query(
                "MATCH (n) WHERE id(n) = $node_id SET n += $props RETURN n",
                {"node_id": int(node_id), "props": properties}
            )
            return bool(result and 'n' in result[0])
        except Exception as e:
            logger.error(f"Error updating node: {e}")
            return False

    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node by its ID.

        Args:
            node_id: The ID of the node to delete

        Returns:
            bool: True if deletion successful, False otherwise
        """
        if not self.driver:
            logger.error("Not connected to Neo4j. Call connect() first.")
            return False
            
        try:
            # This will fail if the node has relationships
            result = self.execute_query(
                "MATCH (n) WHERE id(n) = $node_id DELETE n",
                {"node_id": int(node_id)}
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting node: {e}")
            return False

    def get_node_relationships(self, node_id: str, 
                              direction: Optional[str] = None, 
                              rel_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get relationships for a node.

        Args:
            node_id: The ID of the node
            direction: Direction of relationships ('in', 'out', or None for both)
            rel_types: Optional list of relationship types to filter by

        Returns:
            List[Dict[str, Any]]: List of relationships with their properties
        """
        if not self.driver:
            logger.error("Not connected to Neo4j. Call connect() first.")
            return []
            
        try:
            # Build the query based on direction and relationship types
            if direction == 'out':
                query = "MATCH (n)-[r]->() WHERE id(n) = $node_id"
            elif direction == 'in':
                query = "MATCH (n)<-[r]-() WHERE id(n) = $node_id"
            else:
                query = "MATCH (n)-[r]-() WHERE id(n) = $node_id"
                
            # Add relationship type filter if specified
            if rel_types:
                rel_filter = " OR ".join([f"type(r) = '{rel_type}'" for rel_type in rel_types])
                query += f" AND ({rel_filter})"
                
            query += " RETURN id(r) as id, type(r) as type, r, id(startNode(r)) as start, id(endNode(r)) as end"
            
            result = self.execute_query(query, {"node_id": int(node_id)})
            
            relationships = []
            for record in result:
                rel = record['r']
                relationships.append({
                    "id": str(record['id']),
                    "type": record['type'],
                    "properties": dict(rel),
                    "start_node": str(record['start']),
                    "end_node": str(record['end'])
                })
            return relationships
        except Exception as e:
            logger.error(f"Error getting relationships: {e}")
            return []