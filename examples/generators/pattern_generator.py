"""
Pattern Generator Module - Generates examples based on graph relationship patterns.

This module implements a concrete strategy for generating question-answer examples
based on relationship patterns identified in the graph schema.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from .base_generator import BaseExampleGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PatternExampleGenerator(BaseExampleGenerator):
    """Generates examples based on relationship patterns in the graph."""
    
    def _identify_key_patterns(self, schema: Dict[str, Any], rich_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify key relationship patterns for examples.
        
        Args:
            schema: The graph schema
            rich_context: Additional context
            
        Returns:
            List of key patterns to use for examples
        """
        key_patterns = []
        
        # Look for relationships in the schema
        for relationship in schema.get('relationships', []):
            # Basic pattern extraction
            parts = relationship.replace('(', '').replace(')', '').split('-[')
            if len(parts) == 2:
                source = parts[0].strip()
                rel_target = parts[1].split(']')
                if len(rel_target) == 2:
                    rel = rel_target[0].replace(':', '')
                    target = rel_target[1].replace('->', '').strip()
                    
                    # Check if this relationship has examples in rich_context
                    rel_key = f"{source}-{rel}->{target}"
                    has_examples = rel_key in rich_context.get('relationship_examples', {})
                    
                    # Check node counts to prioritize patterns with data
                    source_count = schema.get('node_counts', {}).get(source, 0)
                    target_count = schema.get('node_counts', {}).get(target, 0)
                    
                    # Calculate priority based on examples and counts
                    priority = 10
                    if has_examples:
                        priority -= 5
                    if source_count > 10 and target_count > 10:
                        priority -= 3
                    
                    key_patterns.append({
                        'source_type': source,
                        'relationship_type': rel,
                        'target_type': target,
                        'has_examples': has_examples,
                        'priority': priority
                    })
        
        # Sort by priority (lower is better)
        key_patterns.sort(key=lambda x: x.get('priority', 999))
        
        return key_patterns
    
    def _generate_examples_for_pattern(self, pattern: Dict[str, Any], schema: Dict[str, Any], rich_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate examples for a specific pattern.
        
        Args:
            pattern: The pattern to generate examples for
            schema: The graph schema
            rich_context: Additional context
            
        Returns:
            List of examples for this pattern
        """
        # Check if we have an LLM client
        if not self.llm_client:
            logger.warning("No LLM client provided, cannot generate examples")
            return []
            
        examples = []
        
        # Extract pattern information
        source_type = pattern.get('source_type')
        relationship_type = pattern.get('relationship_type')
        target_type = pattern.get('target_type')
        
        # Skip if missing required information
        if not all([source_type, relationship_type, target_type]):
            return []
        
        # Format context for the pattern
        pattern_context = self._format_pattern_context(pattern, schema, rich_context)
        
        # Create prompt for the LLM
        prompt = f"""Given the following graph database pattern and examples, generate 1-2 realistic natural language questions that users might ask about this pattern, along with the corresponding Neo4j Cypher query to answer each question.

PATTERN:
({source_type})-[:{relationship_type}]->({target_type})

CONTEXT:
{pattern_context}

For each question, provide:
1. A natural language question
2. A Cypher query that accurately answers the question
3. A brief explanation of why this query answers the question

Format your response as a JSON array with objects containing 'question', 'cypher', and 'explanation' fields.
"""

        try:
            # Call the LLM to generate examples
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a graph database query specialist skilled at creating natural language questions about graph patterns and corresponding Cypher queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            try:
                # Get the raw content first
                content = response.choices[0].message.content
                logger.info(f"Raw LLM response: {content[:200]}...")
                
                # Try to parse as JSON
                try:
                    pattern_examples = json.loads(content)
                    
                    # Try different JSON structures
                    gen_examples = []
                    
                    # Case 1: Response is an object with an 'examples' key
                    if isinstance(pattern_examples, dict) and 'examples' in pattern_examples:
                        gen_examples = pattern_examples.get('examples', [])
                    
                    # Case 2: Response is a list directly
                    elif isinstance(pattern_examples, list):
                        gen_examples = pattern_examples
                        
                    # Case 3: Special case for single example
                    elif isinstance(pattern_examples, dict) and 'question' in pattern_examples and 'cypher' in pattern_examples:
                        gen_examples = [pattern_examples]
                        
                    # Case 4: Response has a 'questions' array
                    elif isinstance(pattern_examples, dict) and 'questions' in pattern_examples:
                        gen_examples = pattern_examples.get('questions', [])
                    
                    logger.info(f"Parsed {len(gen_examples)} examples from LLM response")
                    
                    # Format examples in the expected structure
                    for example in gen_examples:
                        question = example.get('question')
                        cypher = example.get('cypher')
                        explanation = example.get('explanation')
                        
                        if not all([question, cypher]):
                            logger.warning(f"Skipping incomplete example: {example}")
                            continue
                        
                        # Format as a query_plan object similar to what the QueryDecompositionAgent produces
                        query_plan = [
                            {
                                "purpose": f"Retrieve information about {source_type} and {target_type} via {relationship_type}",
                                "cypher": cypher
                            }
                        ]
                        
                        examples.append({
                            "question": question,
                            "query_plan": query_plan,
                            "thought_process": explanation or f"This query finds the relationship between {source_type} and {target_type} using the {relationship_type} relationship."
                        })
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing error: {e}")
                    
                    # Try to extract examples from non-JSON format using regex
                    import re
                    question_pattern = r'(?:Question|Natural language question):\s*(.*?)(?:\n|$)'
                    cypher_pattern = r'(?:Cypher|Query):\s*(MATCH.*?)(?:\n\n|\n[A-Z]|$)'
                    explanation_pattern = r'(?:Explanation|Why):\s*(.*?)(?:\n\n|\n[A-Z]|$)'
                    
                    questions = re.findall(question_pattern, content, re.DOTALL)
                    cyphers = re.findall(cypher_pattern, content, re.DOTALL)
                    explanations = re.findall(explanation_pattern, content, re.DOTALL)
                    
                    logger.info(f"Regex extracted: {len(questions)} questions, {len(cyphers)} cyphers")
                    
                    # Create examples from matched patterns
                    for i in range(min(len(questions), len(cyphers))):
                        question = questions[i].strip()
                        cypher = cyphers[i].strip()
                        explanation = explanations[i].strip() if i < len(explanations) else None
                        
                        if not question or not cypher:
                            continue
                            
                        query_plan = [
                            {
                                "purpose": f"Retrieve information about {source_type} and {target_type} via {relationship_type}",
                                "cypher": cypher
                            }
                        ]
                        
                        examples.append({
                            "question": question,
                            "query_plan": query_plan,
                            "thought_process": explanation or f"This query finds the relationship between {source_type} and {target_type} using the {relationship_type} relationship."
                        })
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing LLM response: {e}")
                
        except Exception as e:
            logger.warning(f"Error generating examples for pattern {source_type}-{relationship_type}->{target_type}: {e}")
        
        return examples
    
    def _format_pattern_context(self, pattern: Dict[str, Any], schema: Dict[str, Any], rich_context: Dict[str, Any]) -> str:
        """
        Format context about a pattern for the LLM to generate examples.
        
        Args:
            pattern: The pattern information
            schema: The graph schema
            rich_context: Additional context
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        source_type = pattern.get('source_type')
        relationship_type = pattern.get('relationship_type')
        target_type = pattern.get('target_type')
        
        # Add information about the source node type
        if source_type in schema.get('node_types', {}):
            properties = schema.get('node_types', {}).get(source_type, [])
            context_parts.append(f"{source_type} Properties: {', '.join(properties)}")
            
            # Add examples
            examples = rich_context.get('node_examples', {}).get(source_type, [])
            if examples:
                context_parts.append(f"\n{source_type} Examples:")
                for i, example in enumerate(examples[:2], 1):
                    example_str = ", ".join([f"{k}: {v}" for k, v in example.items() if v is not None])
                    context_parts.append(f"  {i}. {example_str}")
                    
        # Add information about the target node type
        if target_type in schema.get('node_types', {}):
            properties = schema.get('node_types', {}).get(target_type, [])
            context_parts.append(f"\n{target_type} Properties: {', '.join(properties)}")
            
            # Add examples
            examples = rich_context.get('node_examples', {}).get(target_type, [])
            if examples:
                context_parts.append(f"\n{target_type} Examples:")
                for i, example in enumerate(examples[:2], 1):
                    example_str = ", ".join([f"{k}: {v}" for k, v in example.items() if v is not None])
                    context_parts.append(f"  {i}. {example_str}")
        
        # Add information about the relationship type
        if relationship_type in schema.get('relationship_types', {}):
            properties = schema.get('relationship_types', {}).get(relationship_type, [])
            context_parts.append(f"\n{relationship_type} Properties: {', '.join(properties)}")
                        
        # Add relationship examples
        rel_key = f"{source_type}-{relationship_type}->{target_type}"
        examples = rich_context.get('relationship_examples', {}).get(rel_key, [])
        if examples:
            context_parts.append(f"\nRelationship Examples ({source_type}-{relationship_type}->{target_type}):")
            for i, example in enumerate(examples, 1):
                source_name = example.get('source_name', 'unknown')
                target_name = example.get('target_name', 'unknown')
                context_parts.append(f"  {i}. {source_name} -> {target_name}")
                
        # Add some common queries for this pattern if available
        common_queries = []
        for query in rich_context.get('common_queries', []):
            description = query.get('description', '')
            cypher = query.get('cypher', '')
            
            # Check if this query involves our pattern
            if (source_type in description and target_type in description and relationship_type in description) or \
               (source_type in cypher and target_type in cypher and relationship_type in cypher):
                common_queries.append(query)
                
        if common_queries:
            context_parts.append("\nCommon Queries:")
            for i, query in enumerate(common_queries[:2], 1):
                description = query.get('description', 'Unknown query')
                cypher = query.get('cypher', '')
                context_parts.append(f"  {i}. {description}")
                context_parts.append(f"     {cypher}")
                
        return "\n".join(context_parts)