"""
Schema Loader Module - Interfaces and implementations for loading schema from graph databases.

This module provides the base interface and concrete implementations for schema loading,
with a focus on clean separation of concerns and extensibility.
"""

import abc
import logging
import os
from typing import Dict, Any, Optional

# Configure module level logger to prevent recursion
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchemaLoaderInterface(abc.ABC):
    """Interface for loading schema data from a graph database."""
    
    @abc.abstractmethod
    def load_schema(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Load the schema from the graph database.
        
        Args:
            force_refresh: Whether to force a refresh of the schema
            
        Returns:
            Dictionary containing schema information
        """
        pass
    
    @abc.abstractmethod
    def get_formatted_schema(self) -> str:
        """
        Get the schema formatted for prompts.
        
        Returns:
            Formatted schema string for inclusion in prompts
        """
        pass

class Neo4jSchemaLoader(SchemaLoaderInterface):
    """Implementation for loading schema from Neo4j databases."""
    
    def __init__(self, db_factory):
        """
        Initialize the Neo4j schema loader.
        
        Args:
            db_factory: Factory to create database connections
        """
        self.db_factory = db_factory
        self.schema = None
        self.formatted_schema = None
        self._db = None
        self._connection_attempt = False
    
    def load_schema(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Load the schema from the Neo4j database.
        
        Args:
            force_refresh: Whether to force a refresh of the schema
            
        Returns:
            Dictionary containing schema information
        """
        # Return cached schema if available and refresh not forced
        if self.schema is not None and not force_refresh:
            return self.schema
        
        # Avoid recursive connection failures
        if self._connection_attempt:
            logger.warning("Already attempting to connect to database, returning empty schema")
            return self._get_empty_schema("Connection already in progress")
            
        self._connection_attempt = True
        
        try:
            # Create database connection if not already connected
            if not self._db:
                self._db = self.db_factory.create_graph_database_strategy()
                
            # Connect to the database
            connected = self._db.connect()
            if not connected:
                logger.error("Failed to connect to database")
                self._connection_attempt = False
                return self._get_empty_schema("Failed to connect to database")
            
            # Query for node labels and their properties
            node_query = """
            CALL db.schema.nodeTypeProperties() 
            YIELD nodeType, propertyName
            RETURN nodeType AS label, collect(propertyName) AS properties
            """
            node_results = self._db.execute_query(node_query)
            
            # Query for relationship types and their properties
            rel_query = """
            CALL db.schema.relTypeProperties()
            YIELD relType, propertyName
            RETURN relType AS type, collect(propertyName) AS properties
            """
            rel_results = self._db.execute_query(rel_query)
            
            # Query for actual relationship connections from schema visualization
            connections_query = """
            CALL db.schema.visualization() 
            YIELD nodes, relationships
            UNWIND relationships AS rel
            RETURN 
                head(nodes) AS source_label,
                rel.type AS relationship,
                last(nodes) AS target_label
            LIMIT 100
            """
            connections_results = self._db.execute_query(connections_query)
            
            # Format the results
            node_types = {}
            for node in node_results:
                label = node.get('label')
                if label:
                    node_types[label] = node.get('properties', [])
            
            rel_types = {}
            for rel in rel_results:
                type_name = rel.get('type')
                if type_name:
                    rel_types[type_name] = rel.get('properties', [])
            
            # Get relationship patterns
            relationships = []
            relationship_map = {}
            for conn in connections_results:
                source = conn.get('source_label')
                rel = conn.get('relationship')
                target = conn.get('target_label')
                if source and rel and target:
                    rel_pattern = f"({source})-[:{rel}]->({target})"
                    relationships.append(rel_pattern)
                    
                    # Build a map for relationship patterns
                    if source not in relationship_map:
                        relationship_map[source] = {}
                    if rel not in relationship_map[source]:
                        relationship_map[source][rel] = []
                    relationship_map[source][rel].append(target)
            
            # Count node instances (with error handling)
            node_counts = {}
            for node_type in list(node_types.keys())[:5]:  # Limit to first 5 to avoid excessive queries
                try:
                    # Remove backticks and colons to ensure valid Cypher
                    clean_type = node_type.replace('`', '').replace(':', '')
                    count_query = f"MATCH (n:{clean_type}) RETURN count(n) as count"
                    count_result = self._db.execute_query(count_query)
                    if count_result and len(count_result) > 0:
                        node_counts[node_type] = count_result[0].get('count', 0)
                except Exception as e:
                    logger.warning(f"Error counting {node_type} nodes: {e}")
                    node_counts[node_type] = 0
            
            # Close the database connection
            self._db.close()
            self._db = None
            
            # Save the schema
            self.schema = {
                'node_types': node_types,
                'relationship_types': rel_types,
                'relationships': relationships,
                'relationship_map': relationship_map,
                'node_counts': node_counts
            }
            
            # Format the schema for prompts
            self.formatted_schema = self._format_schema_for_prompt(self.schema)
            
            # Reset connection flag
            self._connection_attempt = False
            
            return self.schema
        
        except Exception as e:
            logger.error(f"Error retrieving graph schema: {e}")
            # Reset connection state
            if self._db:
                try:
                    self._db.close()
                except:
                    pass
                self._db = None
            self._connection_attempt = False
            
            return self._get_empty_schema(str(e))
    
    def _get_empty_schema(self, error_message: str = "") -> Dict[str, Any]:
        """Create an empty schema with optional error message"""
        self.schema = {
            'node_types': {},
            'relationship_types': {},
            'relationships': [],
            'relationship_map': {},
            'node_counts': {},
            'error': error_message
        }
        self.formatted_schema = f"Error retrieving schema: {error_message}"
        return self.schema
    
    def get_formatted_schema(self) -> str:
        """
        Get the schema formatted for prompts.
        
        Returns:
            Formatted schema string for inclusion in prompts
        """
        if self.formatted_schema is None:
            self.load_schema()
            
        return self.formatted_schema
    
    def _format_schema_for_prompt(self, schema: Dict[str, Any]) -> str:
        """
        Format the schema for use in prompts.
        
        Args:
            schema: The schema to format
            
        Returns:
            Formatted schema string
        """
        formatted = ["TAXONOMY SCHEMA:"]
        
        # Format node types and their properties
        formatted.append("Node Types:")
        for label, properties in schema.get('node_types', {}).items():
            count = schema.get('node_counts', {}).get(label, 0)
            formatted.append(f"- {label} (Count: {count})")
            if properties:
                formatted.append(f"  - Properties: {', '.join(properties)}")
        
        # Format relationship types and their properties
        formatted.append("\nRelationship Types:")
        for rel_type, properties in schema.get('relationship_types', {}).items():
            formatted.append(f"- {rel_type}")
            if properties:
                formatted.append(f"  - Properties: {', '.join(properties)}")
        
        # Format relationship patterns
        formatted.append("\nRelationship Patterns:")
        for rel in schema.get('relationships', []):
            formatted.append(f"- {rel}")
        
        return "\n".join(formatted)