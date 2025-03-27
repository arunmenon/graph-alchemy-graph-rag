"""
Schema Manager Module - Manages schema and context information with a modular approach.

This module provides a lightweight schema manager that composes various components
for loading, caching, and providing schema information.
"""

import os
import logging
from typing import Dict, List, Any, Optional

from schema.core.schema_loader import SchemaLoaderInterface, Neo4jSchemaLoader
from schema.core.schema_cache import SchemaCacheInterface, FileSchemaCache
from examples.factory import ExampleGeneratorFactory
from examples.storage.example_repository import ExampleRepositoryInterface, FileExampleRepository
from graph_db.graph_strategy_factory import GraphDatabaseFactory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchemaManager:
    """Manages schema and context information with a modular approach."""
    
    def __init__(
        self,
        schema_loader: SchemaLoaderInterface = None,
        schema_cache: SchemaCacheInterface = None,
        example_repository: ExampleRepositoryInterface = None,
        cache_dir: str = None,
        cache_ttl: int = 3600,
        llm_client = None
    ):
        """
        Initialize the schema manager.
        
        Args:
            schema_loader: Loader for schema information
            schema_cache: Cache for schema information
            example_repository: Repository for example storage
            cache_dir: Directory for cache files
            cache_ttl: Time-to-live for cache entries
            llm_client: Client for LLM API calls
        """
        # Set up cache directory
        if cache_dir is None:
            cache_dir = os.path.join('schema', 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        # Create schema cache if not provided
        self.schema_cache = schema_cache or FileSchemaCache(
            cache_dir=cache_dir,
            ttl=cache_ttl
        )
        
        # Create schema loader if not provided
        self.schema_loader = schema_loader or Neo4jSchemaLoader(
            db_factory=GraphDatabaseFactory
        )
        
        # Create example repository if not provided
        example_storage_path = os.path.join(cache_dir, 'examples.json')
        self.example_repository = example_repository or FileExampleRepository(
            storage_path=example_storage_path,
            ttl=cache_ttl
        )
        
        # Store LLM client for example generation
        self.llm_client = llm_client
        
        # Initialize state
        self.schema = None
        self.rich_context = None
    
    def get_schema(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get the graph schema.
        
        Args:
            force_refresh: Whether to force a refresh
            
        Returns:
            Graph schema dictionary
        """
        # Check cache first
        if not force_refresh:
            cached_schema = self.schema_cache.get('schema')
            if cached_schema is not None:
                self.schema = cached_schema
                return self.schema
        
        # Load schema if not cached or force refresh
        self.schema = self.schema_loader.load_schema(force_refresh=force_refresh)
        
        # Cache the schema
        self.schema_cache.set('schema', self.schema)
        
        # If force refresh, also refresh the rich context and examples
        if force_refresh:
            self._load_rich_context(force_refresh=True)
            self._generate_examples(force_refresh=True)
        
        return self.schema
    
    def get_formatted_schema(self, force_refresh: bool = False) -> str:
        """
        Get the schema formatted for prompts.
        
        Args:
            force_refresh: Whether to force a refresh
            
        Returns:
            Formatted schema string
        """
        # Get schema first (this will use cache if available)
        self.get_schema(force_refresh=force_refresh)
        
        # Return formatted schema from loader
        return self.schema_loader.get_formatted_schema()
    
    def get_examples(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get example Q&A pairs.
        
        Args:
            force_refresh: Whether to force a refresh
            
        Returns:
            List of example Q&A pairs
        """
        # Try to get from repository first
        if not force_refresh:
            examples = self.example_repository.get_examples()
            if examples:
                return examples
        
        # Generate new examples if none cached or force refresh
        return self._generate_examples(force_refresh=force_refresh)
    
    def _load_rich_context(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Load rich context with examples.
        
        Args:
            force_refresh: Whether to force a refresh
            
        Returns:
            Rich context dictionary
        """
        # Check cache first
        if not force_refresh:
            cached_context = self.schema_cache.get('rich_context')
            if cached_context is not None:
                self.rich_context = cached_context
                return self.rich_context
        
        # Get schema first
        schema = self.get_schema(force_refresh=force_refresh)
        
        # Load rich context
        # This would typically include example data from the database
        # For now, we'll return a simplified version
        self.rich_context = {
            'node_examples': {},
            'relationship_examples': {},
            'common_queries': []
        }
        
        # Cache the rich context
        self.schema_cache.set('rich_context', self.rich_context)
        
        return self.rich_context
    
    def _generate_examples(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Generate example Q&A pairs.
        
        Args:
            force_refresh: Whether to force a refresh
            
        Returns:
            List of example Q&A pairs
        """
        # Check if we have a LLM client
        if not self.llm_client:
            logger.warning("No LLM client provided, cannot generate examples")
            return []
        
        # Get schema and rich context
        schema = self.get_schema(force_refresh=force_refresh)
        rich_context = self._load_rich_context(force_refresh=force_refresh)
        
        try:
            # Create a database connection for validation
            db_connector = GraphDatabaseFactory.create_graph_database_strategy()
            db_connector.connect()
            
            # Create a pattern example generator
            generator = ExampleGeneratorFactory.create_generator(
                generator_type='pattern',
                llm_client=self.llm_client
            )
            
            # Generate examples
            examples = generator.generate_examples(
                schema=schema,
                rich_context=rich_context,
                count=3  # Generate 3 examples
            )
            
            # Validate examples
            validated_examples = generator.validate_examples(
                examples=examples,
                db_connector=db_connector
            )
            
            # Close the database connection
            db_connector.close()
            
            # Store examples
            self.example_repository.store_examples(validated_examples)
            
            return validated_examples
            
        except Exception as e:
            logger.error(f"Error generating examples: {e}")
            return []