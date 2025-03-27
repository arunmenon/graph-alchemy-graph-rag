"""
Query Decomposition Agent - Converts natural language questions into Neo4j Cypher queries.

This agent is responsible for:
1. Analyzing questions about the graph data
2. Breaking down complex questions into graph queries
3. Generating Cypher queries to retrieve relevant information
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

from agents.agent_base import Agent
from schema.manager import SchemaManager
from prompts.prompt_builder import PromptBuilder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QueryDecompositionAgent(Agent):
    """Agent that decomposes natural language questions into graph queries."""
    
    def __init__(self, system_prompt_path: str = None, schema_manager: SchemaManager = None):
        """
        Initialize the query decomposition agent.
        
        Args:
            system_prompt_path: Path to system prompt for the LLM
            schema_manager: Schema manager instance
        """
        super().__init__()
        # Default to standard prompts if none provided
        self.system_prompt_path = system_prompt_path or os.path.join('prompts', 'templates', 'query_decomposition_system_prompt.txt')
        
        # Create and load system prompt if it doesn't exist
        self._ensure_system_prompt_exists()
        
        # Load system prompt
        with open(self.system_prompt_path, 'r') as f:
            self.system_prompt = f.read()
            
        # Create or use schema manager
        self.schema_manager = schema_manager
        
        # Create prompt builder
        self.prompt_builder = PromptBuilder()
        
        # Initialize LLM client
        from scripts.client import get_llm_client
        self.llm_client = get_llm_client()
        
        # If no schema manager provided, create one with our LLM client
        if self.schema_manager is None:
            self.schema_manager = SchemaManager(llm_client=self.llm_client)
    
    def _ensure_system_prompt_exists(self):
        """Create default system prompt if it doesn't exist."""
        os.makedirs(os.path.dirname(self.system_prompt_path), exist_ok=True)
        
        # Create system prompt if it doesn't exist
        if not os.path.exists(self.system_prompt_path):
            system_prompt = """You are a query decomposition specialist focused on converting natural language questions into graph database queries.
Your task is to analyze a question about a taxonomy and break it down into specific graph queries that can retrieve the relevant information.
You will identify entities, relationships, and constraints in the question and translate them into appropriate Cypher queries for Neo4j."""
            
            with open(self.system_prompt_path, 'w') as f:
                f.write(system_prompt)
    
    def execute(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core execution method for the query decomposition agent.
        
        Args:
            data: Input data for this agent
            context: Shared workflow context
            
        Returns:
            Processed data with agent results
        """
        return self.process(data)
    
    def process(self, input_data: Dict) -> Dict:
        """
        Process the input question and decompose it into graph queries.
        
        Args:
            input_data: Dictionary containing the user's question
            
        Returns:
            Dictionary with decomposed queries
        """
        logger.info("Decomposing question into graph queries...")
        
        question = input_data.get('question', '')
        if not question:
            return {
                'query_plan': [],
                'error': 'No question provided'
            }
        
        # Get the current schema from the schema manager
        schema_text = self.schema_manager.get_formatted_schema()
        
        # Get example Q&A pairs
        examples = self.schema_manager.get_examples()
        
        # Build the prompt with schema and examples
        filled_prompt = self.prompt_builder.build_query_decomposition_prompt(
            question=question,
            schema=schema_text,
            examples=examples
        )
        
        # Call the LLM for query decomposition
        try:
            logger.info("Calling LLM for query decomposition...")
            llm_response = self.llm_client.chat.completions.create(
                model="gpt-4o",  # Use appropriate model
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": filled_prompt}
                ],
                temperature=0.2,  # Low temperature for more deterministic results
                response_format={"type": "json_object"}
            )
            
            # Extract and parse the response
            decomposition_result = json.loads(llm_response.choices[0].message.content)
            query_plan = decomposition_result.get('query_plan', [])
            thought_process = decomposition_result.get('thought_process', '')
            
            logger.info(f"Query decomposition complete. Generated {len(query_plan)} queries.")
            
            return {
                'query_plan': query_plan,
                'thought_process': thought_process,
                'original_question': question,
                'llm_decomposition': decomposition_result  # Include full LLM response for transparency
            }
            
        except Exception as e:
            logger.error(f"Error in query decomposition: {e}")
            return {
                'query_plan': [],
                'error': str(e),
                'original_question': question
            }