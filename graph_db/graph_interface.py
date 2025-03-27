"""
Graph Database Interface - Abstract interface for graph database interactions.

This module defines the GraphDatabaseInterface that all graph database
implementations should inherit from.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union


class GraphDatabaseInterface(ABC):
    """Abstract interface for graph database interactions."""

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the graph database.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def close(self) -> bool:
        """
        Close the connection to the graph database.

        Returns:
            bool: True if close successful, False otherwise
        """
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a query against the graph database.

        Args:
            query: The query string to execute
            params: Optional parameters for the query

        Returns:
            List[Dict[str, Any]]: Results from the query
        """
        pass

    @abstractmethod
    def create_node(self, label: str, properties: Dict[str, Any]) -> Optional[str]:
        """
        Create a node in the graph database.

        Args:
            label: The label for the node
            properties: The properties for the node

        Returns:
            Optional[str]: The ID of the created node, or None if creation failed
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by its ID.

        Args:
            node_id: The ID of the node to get

        Returns:
            Optional[Dict[str, Any]]: The node properties or None if not found
        """
        pass
        
    @abstractmethod
    def get_nodes_by_label(self, label: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get nodes by label.

        Args:
            label: The label to search for
            limit: Maximum number of nodes to return

        Returns:
            List[Dict[str, Any]]: List of nodes with their properties
        """
        pass

    @abstractmethod
    def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """
        Update a node's properties.

        Args:
            node_id: The ID of the node to update
            properties: The properties to update

        Returns:
            bool: True if update successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node by its ID.

        Args:
            node_id: The ID of the node to delete

        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass

    @abstractmethod
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
        pass