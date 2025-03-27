"""
Prompt Builder Module - Dynamically builds prompts with examples.

This module provides functionality for building prompts with dynamically
generated examples based on the schema and available data.
"""

import os
import logging
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PromptBuilder:
    """Builds prompts with dynamically generated examples."""
    
    def __init__(self, templates_dir: str = None):
        """
        Initialize the prompt builder.
        
        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = templates_dir or os.path.join('prompts', 'templates')
        
        # Create templates directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Initialize template cache
        self.template_cache = {}
        
        # Pre-load common templates
        self._load_template('query_decomposition_prompt.txt')
    
    def _load_template(self, template_name: str) -> str:
        """
        Load a template from disk and cache it in memory.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Template string
        """
        # If already in cache, return it
        if template_name in self.template_cache:
            return self.template_cache[template_name]
        
        # Construct the template path
        template_path = os.path.join(self.templates_dir, template_name)
        
        # Check if the template exists, create default if not
        if not os.path.exists(template_path):
            if template_name == 'query_decomposition_prompt.txt':
                self._create_default_query_decomposition_template(template_path)
            else:
                logger.warning(f"No default implementation for template {template_name}")
                self.template_cache[template_name] = ""
                return ""
        
        # Load the template
        try:
            with open(template_path, 'r') as f:
                template = f.read()
                
            # Cache the template
            self.template_cache[template_name] = template
            return template
            
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            self.template_cache[template_name] = ""
            return ""
    
    def build_query_decomposition_prompt(self, question: str, schema: str, examples: List[Dict[str, Any]] = None) -> str:
        """
        Build a query decomposition prompt with the given question, schema, and examples.
        
        Args:
            question: The user's question
            schema: Formatted schema string
            examples: Optional list of example Q&A pairs
            
        Returns:
            Complete prompt string
        """
        # Get the template from cache
        template = self._load_template('query_decomposition_prompt.txt')
        
        # Format examples if provided
        examples_text = ""
        if examples and len(examples) > 0:
            examples_text = self._format_examples(examples)
        
        # Replace placeholders
        prompt = template.replace("{{question}}", question)
        prompt = prompt.replace("{{schema}}", schema)
        prompt = prompt.replace("{{examples}}", examples_text)
        
        return prompt
    
    def _format_examples(self, examples: List[Dict[str, Any]]) -> str:
        """
        Format examples for inclusion in the prompt.
        
        Args:
            examples: List of example Q&A pairs
            
        Returns:
            Formatted examples string
        """
        formatted = ["EXAMPLES:"]
        
        for i, example in enumerate(examples, 1):
            question = example.get('question', '')
            query_plan = example.get('query_plan', [])
            thought_process = example.get('thought_process', '')
            
            formatted.append(f"\nExample {i}:")
            formatted.append(f"Question: {question}")
            
            # Format the query plan
            if query_plan:
                formatted.append("\nQuery Plan:")
                for j, query in enumerate(query_plan, 1):
                    purpose = query.get('purpose', '')
                    cypher = query.get('cypher', '')
                    formatted.append(f"  {j}. {purpose}")
                    formatted.append(f"     ```cypher")
                    formatted.append(f"     {cypher}")
                    formatted.append(f"     ```")
            
            # Add thought process if available
            if thought_process:
                formatted.append(f"\nReasoning: {thought_process}")
            
            formatted.append("\n---")
        
        return "\n".join(formatted)
    
    def _create_default_query_decomposition_template(self, template_path: str) -> None:
        """
        Create the default query decomposition template.
        
        Args:
            template_path: Path to create the template at
        """
        template = """Analyze the following question about a product taxonomy and decompose it into Neo4j Cypher queries.

QUESTION:
{{question}}

{{schema}}

{{examples}}

Step 1: Identify the key entities and relationships in the question.
Step 2: Look at the provided schema and examples to understand the data structure.
Step 3: Review the common queries and example questions for similar patterns you can adapt.
Step 4: Formulate one or more Cypher queries to retrieve the relevant information.
Step 5: Ensure your queries are efficient and focused on the specific question asked.

IMPORTANT GUIDELINES:
- Use the actual node labels and relationship types from the schema
- Reference the node examples to understand what properties are available
- Look at the relationship examples to understand how entities connect
- Adapt the examples and common queries where possible instead of creating queries from scratch
- Focus on retrieving only the data needed to answer the question
- Include properties in your query that will be helpful for the final answer

Return a JSON object with the following structure:
```json
{
  "query_plan": [
    {
      "purpose": "Description of what this query retrieves",
      "cypher": "The Cypher query"
    },
    ...
  ],
  "thought_process": "Explanation of your reasoning and how these queries will help answer the question"
}
```"""
        
        # Write the template
        with open(template_path, 'w') as f:
            f.write(template)
        
        # Also cache it in memory
        self.template_cache['query_decomposition_prompt.txt'] = template