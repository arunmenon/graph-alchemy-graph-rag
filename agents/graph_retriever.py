"""
Graph Retriever Agent - Executes queries against the graph database and retrieves results.

This agent is responsible for:
1. Connecting to the graph database
2. Executing Cypher queries
3. Processing and formatting the results
4. Validating and fixing queries before execution
5. Performing semantic search for relevant entities
"""

import logging
from typing import Dict, List, Any, Optional, Union

from agents.agent_base import Agent
from graph_db.graph_strategy_factory import GraphDatabaseFactory
from agents.query_validator import QueryValidator

# Conditionally import semantic search components
try:
    from semantic.embedding_provider import SentenceTransformerProvider, DummyEmbeddingProvider
    from semantic.entity_retriever import SemanticEntityRetriever
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GraphRetrieverAgent(Agent):
    """Agent that retrieves relevant information from the graph database."""
    
    def __init__(self, enable_semantic_search: bool = True):
        """
        Initialize the graph retriever agent.
        
        Args:
            enable_semantic_search: Whether to enable semantic search capabilities
        """
        super().__init__()
        self.graph_db = None
        self.query_validator = QueryValidator()
        self.semantic_entity_retriever = None
        self.enable_semantic_search = enable_semantic_search and SEMANTIC_SEARCH_AVAILABLE
        
        if self.enable_semantic_search:
            logger.info("Semantic search capabilities are enabled")
        else:
            if enable_semantic_search and not SEMANTIC_SEARCH_AVAILABLE:
                logger.warning("Semantic search capabilities are not available (missing dependencies)")
            else:
                logger.info("Semantic search capabilities are disabled")
    
    def connect_to_database(self):
        """Connect to the Neo4j database."""
        logger.info("Connecting to graph database...")
        self.graph_db = GraphDatabaseFactory.create_graph_database_strategy()
        
        # Connect to the database
        connected = self.graph_db.connect()
        
        if connected:
            logger.info("Connected to graph database")
            
            # Initialize semantic entity retriever if enabled
            if self.enable_semantic_search and self.semantic_entity_retriever is None:
                try:
                    # Try to use SentenceTransformerProvider, fall back to DummyEmbeddingProvider if it fails
                    try:
                        embedding_provider = SentenceTransformerProvider()
                        logger.info("Using SentenceTransformerProvider for semantic search")
                    except Exception as e:
                        logger.warning(f"Failed to initialize SentenceTransformerProvider: {e}")
                        logger.warning("Falling back to DummyEmbeddingProvider")
                        embedding_provider = DummyEmbeddingProvider()
                    
                    # Create semantic entity retriever
                    self.semantic_entity_retriever = SemanticEntityRetriever(self.graph_db, embedding_provider)
                    logger.info("Semantic entity retriever initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize semantic search: {e}")
                    self.enable_semantic_search = False
        else:
            logger.error("Failed to connect to graph database")
            
        return connected
    
    def close_database(self):
        """Close the database connection."""
        if self.graph_db:
            self.graph_db.close()
            logger.info("Closed database connection")
            self.graph_db = None
    
    def execute(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core execution method for the graph retriever agent.
        
        Args:
            data: Input data for this agent
            context: Shared workflow context
            
        Returns:
            Processed data with agent results
        """
        return self.process(data)
    
    def process(self, input_data: Dict) -> Dict:
        """
        Process the decomposed queries and retrieve information from the graph.
        
        Args:
            input_data: Dictionary containing query plan and original question
            
        Returns:
            Dictionary with retrieved graph context
        """
        logger.info("Retrieving information from graph database...")
        
        query_plan = input_data.get('query_plan', [])
        original_question = input_data.get('original_question', '')
        
        if not query_plan:
            return {
                'retrieved_context': [],
                'error': 'No queries to execute',
                'original_question': original_question
            }
        
        try:
            # Connect to the database
            self.connect_to_database()
            
            # Check if we should try semantic search
            semantic_results = []
            if self.enable_semantic_search and self.semantic_entity_retriever:
                # Perform semantic search with the original question
                semantic_results = self.perform_semantic_search(original_question)
            
            # Execute each query in the plan
            retrieved_context = []
            for query_item in query_plan:
                purpose = query_item.get('purpose', 'Unknown purpose')
                cypher = query_item.get('cypher', '')
                
                if not cypher:
                    logger.warning(f"Empty Cypher query for purpose: {purpose}")
                    continue
                
                logger.info(f"Executing query for: {purpose}")
                
                try:
                    # Validate and fix the query before execution using the validator
                    # Note: Method is validate_and_fix in the QueryValidator class
                    fixed_cypher, is_valid, validation_message = self.query_validator.validate_and_fix(cypher)
                    
                    # If query validation failed and couldn't be fixed
                    if not is_valid:
                        logger.warning(f"Query validation failed: {validation_message}")
                        logger.warning(f"Using fallback query instead of: {cypher}")
                        # Use a safe fallback query that's related to the purpose
                        if "table" in purpose.lower():
                            # Query for tables when asking about tables
                            fixed_cypher = "MATCH (n:Table) RETURN n LIMIT 25"
                        else:
                            # Generic fallback query with higher limit
                            fixed_cypher = "MATCH (n) RETURN n LIMIT 25"
                    elif validation_message:
                        logger.warning(f"Query validation message: {validation_message}")
                    
                    logger.info(f"Executing Cypher query: {fixed_cypher}")
                    # Execute the query (original or fixed version)
                    result = self.graph_db.execute_query(fixed_cypher)
                    
                    # Format the result
                    formatted_result = {
                        'purpose': purpose,
                        'original_cypher': cypher,
                        'executed_cypher': fixed_cypher if fixed_cypher != cypher else cypher,
                        'was_modified': fixed_cypher != cypher,
                        'validation_message': validation_message,
                        'result': result,
                        'result_count': len(result) if result else 0
                    }
                    
                    retrieved_context.append(formatted_result)
                    
                except Exception as query_error:
                    logger.error(f"Error executing query: {query_error}")
                    retrieved_context.append({
                        'purpose': purpose,
                        'original_cypher': cypher,
                        'error': str(query_error),
                        'result': [],
                        'result_count': 0
                    })
            
            # Add semantic search results if available
            if semantic_results:
                retrieved_context.append({
                    'purpose': 'Semantic entity search',
                    'original_cypher': f"SEMANTIC SEARCH: {original_question}",
                    'executed_cypher': "Used vector similarity search",
                    'was_modified': False,
                    'validation_message': '',
                    'result': semantic_results,
                    'result_count': len(semantic_results),
                    'is_semantic_search': True
                })
            
            # Close the database connection
            self.close_database()
            
            return {
                'retrieved_context': retrieved_context,
                'original_question': original_question,
                'thought_process': input_data.get('thought_process', ''),
                'semantic_search_enabled': self.enable_semantic_search
            }
            
        except Exception as e:
            logger.error(f"Error in graph retrieval: {e}")
            self.close_database()  # Ensure connection is closed even on error
            
            return {
                'retrieved_context': [],
                'error': str(e),
                'original_question': original_question
            }
    
    def perform_semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform semantic search for relevant entities.
        
        Args:
            query: The text query to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching entities with similarity scores
        """
        if not self.semantic_entity_retriever:
            logger.warning("Semantic entity retriever not initialized")
            return []
        
        try:
            logger.info(f"Performing semantic search for: {query}")
            
            # Execute the semantic search
            results = self.semantic_entity_retriever.search(query, limit=limit)
            
            logger.info(f"Semantic search returned {len(results)} results")
            
            return results
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []