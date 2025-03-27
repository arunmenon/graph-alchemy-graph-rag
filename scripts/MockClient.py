"""
Mock LLM Client Module - For testing purposes only.

This module provides a simplified mock client to allow tests to run without 
requiring actual API calls to LLM services.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)

class MockCompletionChoice:
    def __init__(self, content):
        self.message = MagicMock()
        self.message.content = content

class MockCompletion:
    def __init__(self, content):
        self.choices = [MockCompletionChoice(content)]

class MockOpenAI:
    def __init__(self):
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        
        def create(*args, **kwargs):
            # Generate content based on the prompt
            model = kwargs.get('model', 'gpt-4o')
            messages = kwargs.get('messages', [])
            
            # Check the prompt content to determine what to return
            if any('graph' in msg.get('content', '') for msg in messages):
                # Graph query decomposition
                return MockCompletion(json.dumps({
                    "query_plan": [
                        {
                            "purpose": "Find products by category",
                            "cypher": "MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: 'Electronics'}) RETURN p.name, p.price"
                        }
                    ],
                    "thought_process": "This query finds all products in the Electronics category"
                }))
            elif any('example' in msg.get('content', '') for msg in messages):
                # Example generation
                return MockCompletion(json.dumps({
                    "examples": [
                        {
                            "question": "What products are in the Electronics category?",
                            "cypher": "MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: 'Electronics'}) RETURN p.name, p.price",
                            "explanation": "This query finds all products that belong to the Electronics category"
                        }
                    ]
                }))
            elif any('reason' in msg.get('content', '') for msg in messages):
                # Reasoning
                return MockCompletion(json.dumps({
                    "answer": "There are 5 products in the Electronics category.",
                    "reasoning": "The query returned 5 products that have a BELONGS_TO relationship to the Electronics category.",
                    "evidence": ["Product: Laptop, Price: 999.99", "Product: Smartphone, Price: 699.99"],
                    "confidence": 0.95
                }))
            else:
                # Default response
                return MockCompletion(json.dumps({
                    "response": "This is a mock response for testing purposes."
                }))
                
        self.chat.completions.create = create

def get_llm_client():
    """
    Get a mock LLM client for testing.
    
    Returns:
        Mock OpenAI client
    """
    return MockOpenAI()