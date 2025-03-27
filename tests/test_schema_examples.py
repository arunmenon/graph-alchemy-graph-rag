"""
Test Schema-Aware Examples - Tests the new schema-aware example generation functionality.

This test script exercises the new modular components:
1. Schema loading and caching
2. Example generation based on schema
3. Dynamic prompt building with examples
4. End-to-end query decomposition with examples
"""

import os
import sys
import logging
import unittest
from unittest.mock import MagicMock, patch
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the modules we need
from schema.core.schema_loader import Neo4jSchemaLoader
from schema.core.schema_cache import MemorySchemaCache
from schema.manager import SchemaManager
from examples.generators.pattern_generator import PatternExampleGenerator
from examples.storage.example_repository import MemoryExampleRepository
from prompts.prompt_builder import PromptBuilder
from agents.query_decomposition import QueryDecompositionAgent

class TestSchemaExamples(unittest.TestCase):
    """Tests for the schema-aware example generation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock schema
        self.mock_schema = {
            'node_types': {
                'Product': ['id', 'name', 'category', 'price'],
                'Category': ['id', 'name', 'description'],
                'Regulation': ['id', 'name', 'description', 'severity']
            },
            'relationship_types': {
                'BELONGS_TO': ['since'],
                'REGULATED_BY': ['score', 'confidence']
            },
            'relationships': [
                '(Product)-[:BELONGS_TO]->(Category)',
                '(Product)-[:REGULATED_BY]->(Regulation)'
            ],
            'relationship_map': {
                'Product': {
                    'BELONGS_TO': ['Category'],
                    'REGULATED_BY': ['Regulation']
                }
            },
            'node_counts': {
                'Product': 100,
                'Category': 10,
                'Regulation': 20
            }
        }
        
        # Create a mock rich context
        self.mock_rich_context = {
            'node_examples': {
                'Product': [
                    {'id': 'P001', 'name': 'Laptop', 'category': 'Electronics', 'price': 999.99},
                    {'id': 'P002', 'name': 'T-shirt', 'category': 'Apparel', 'price': 19.99}
                ],
                'Category': [
                    {'id': 'C001', 'name': 'Electronics', 'description': 'Electronic devices and accessories'},
                    {'id': 'C002', 'name': 'Apparel', 'description': 'Clothing and accessories'}
                ],
                'Regulation': [
                    {'id': 'R001', 'name': 'Safety Standard 1', 'description': 'General product safety standard', 'severity': 'High'},
                    {'id': 'R002', 'name': 'Materials Restriction', 'description': 'Restriction on harmful materials', 'severity': 'Medium'}
                ]
            },
            'relationship_examples': {
                'Product-BELONGS_TO->Category': [
                    {'source_name': 'Laptop', 'target_name': 'Electronics'},
                    {'source_name': 'T-shirt', 'target_name': 'Apparel'}
                ],
                'Product-REGULATED_BY->Regulation': [
                    {'source_name': 'Laptop', 'target_name': 'Safety Standard 1'},
                    {'source_name': 'T-shirt', 'target_name': 'Materials Restriction'}
                ]
            },
            'common_queries': [
                {
                    'description': 'Find products in a specific category',
                    'cypher': 'MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: "Electronics"}) RETURN p.name, p.price'
                },
                {
                    'description': 'Find regulations applying to a product',
                    'cypher': 'MATCH (p:Product {name: "Laptop"})-[r:REGULATED_BY]->(reg:Regulation) RETURN reg.name, r.confidence'
                }
            ]
        }
        
        # Mock examples that might be generated
        self.mock_examples = [
            {
                'question': 'What products are in the Electronics category?',
                'query_plan': [
                    {
                        'purpose': 'Find products in the Electronics category',
                        'cypher': 'MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: "Electronics"}) RETURN p.name, p.price'
                    }
                ],
                'thought_process': 'This query finds all Product nodes that have a BELONGS_TO relationship to a Category node with name "Electronics"'
            },
            {
                'question': 'Which regulations apply to Laptop products?',
                'query_plan': [
                    {
                        'purpose': 'Find regulations for Laptop products',
                        'cypher': 'MATCH (p:Product {name: "Laptop"})-[r:REGULATED_BY]->(reg:Regulation) RETURN reg.name, reg.description, r.confidence'
                    }
                ],
                'thought_process': 'This query finds all Regulation nodes that have a REGULATED_BY relationship from a Product node with name "Laptop"'
            }
        ]
    
    @patch('scripts.client.get_llm_client')
    def test_schema_loader(self, mock_get_llm_client):
        """Test the schema loader functionality."""
        # Create a mock DB factory
        mock_db_factory = MagicMock()
        mock_db = MagicMock()
        mock_db_factory.create_graph_database_strategy.return_value = mock_db
        
        # Set up mock query results
        mock_db.execute_query.side_effect = [
            [{'label': 'Product', 'properties': ['id', 'name', 'category', 'price']}],
            [{'type': 'BELONGS_TO', 'properties': ['since']}],
            [{'source_label': 'Product', 'relationship': 'BELONGS_TO', 'target_label': 'Category'}],
            [{'relationship_type': 'BELONGS_TO'}],
            [],  # For the relationship connections query
            [{'count': 100}]  # For the node count query
        ]
        
        # Create schema loader
        schema_loader = Neo4jSchemaLoader(mock_db_factory)
        
        # Test loading schema
        schema = schema_loader.get_formatted_schema()
        
        # Check that we got a schema
        self.assertIsNotNone(schema)
        self.assertIsInstance(schema, str)
        
        # Check that DB methods were called
        mock_db.connect.assert_called()
        mock_db.execute_query.assert_called()
        mock_db.close.assert_called()
    
    def test_schema_cache(self):
        """Test the schema cache functionality."""
        # Create a memory cache
        cache = MemorySchemaCache(ttl=3600)
        
        # Test setting and getting
        cache.set('test_key', {'data': 'test_data'})
        result = cache.get('test_key')
        
        # Check the result
        self.assertEqual(result, {'data': 'test_data'})
        
        # Test invalid key
        invalid_result = cache.get('invalid_key')
        self.assertIsNone(invalid_result)
        
        # Test invalidation
        cache.invalidate('test_key')
        invalid_after_invalidate = cache.get('test_key')
        self.assertIsNone(invalid_after_invalidate)
    
    @patch('examples.generators.pattern_generator.PatternExampleGenerator._generate_examples_for_pattern')
    def test_example_generator(self, mock_generate):
        """Test the example generator functionality."""
        # Set up the mock
        mock_generate.return_value = self.mock_examples
        
        # Create a generator
        generator = PatternExampleGenerator(llm_client=MagicMock())
        
        # Generate examples
        examples = generator.generate_examples(
            schema=self.mock_schema,
            rich_context=self.mock_rich_context,
            count=2
        )
        
        # Check the examples
        self.assertEqual(len(examples), 2)
        self.assertEqual(examples[0]['question'], 'What products are in the Electronics category?')
        self.assertEqual(examples[1]['question'], 'Which regulations apply to Laptop products?')
    
    def test_prompt_builder(self):
        """Test the prompt builder functionality."""
        # Create a prompt builder
        builder = PromptBuilder()
        
        # Build a prompt
        prompt = builder.build_query_decomposition_prompt(
            question='What products are regulated by Safety Standard 1?',
            schema='MOCK SCHEMA',
            examples=self.mock_examples
        )
        
        # Check the prompt
        self.assertIsNotNone(prompt)
        self.assertIn('What products are regulated by Safety Standard 1?', prompt)
        self.assertIn('MOCK SCHEMA', prompt)
        self.assertIn('What products are in the Electronics category?', prompt)
        self.assertIn('Which regulations apply to Laptop products?', prompt)
        
        # Test template caching
        self.assertIn('query_decomposition_prompt.txt', builder.template_cache)
        
        # Build another prompt and verify it uses the cache
        with patch.object(builder, '_load_template', wraps=builder._load_template) as mock_load:
            prompt2 = builder.build_query_decomposition_prompt(
                question='What categories have products regulated by Materials Restriction?',
                schema='MOCK SCHEMA',
                examples=self.mock_examples
            )
            
            # Verify the method was called but file wasn't read
            mock_load.assert_called_once()
            self.assertIn('What categories have products regulated by Materials Restriction?', prompt2)
    
    @patch('scripts.client.get_llm_client')
    @patch('schema.manager.SchemaManager.get_schema')
    @patch('schema.manager.SchemaManager.get_formatted_schema')
    @patch('schema.manager.SchemaManager.get_examples')
    def test_query_decomposition_agent(self, mock_get_examples, mock_get_formatted_schema, mock_get_schema, mock_get_llm_client):
        """Test the query decomposition agent with examples."""
        # Set up mocks
        mock_get_schema.return_value = self.mock_schema
        mock_get_formatted_schema.return_value = "MOCK FORMATTED SCHEMA"
        mock_get_examples.return_value = self.mock_examples
        
        # Create a mock LLM client
        mock_llm = MagicMock()
        mock_get_llm_client.return_value = mock_llm
        
        # Set up the LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "query_plan": [
                {
                    "purpose": "Find products regulated by Safety Standard 1",
                    "cypher": "MATCH (p:Product)-[r:REGULATED_BY]->(reg:Regulation {name: 'Safety Standard 1'}) RETURN p.name, p.category, r.confidence"
                }
            ],
            "thought_process": "This query finds all Product nodes that have a REGULATED_BY relationship to a Regulation node with name 'Safety Standard 1'"
        })
        mock_llm.chat.completions.create.return_value = mock_response
        
        # Create a schema manager with mocks
        schema_manager = SchemaManager(
            schema_loader=MagicMock(),
            schema_cache=MagicMock(),
            example_repository=MagicMock(),
            llm_client=mock_llm
        )
        
        # Create an agent
        agent = QueryDecompositionAgent(schema_manager=schema_manager)
        
        # Process a question
        result = agent.process({'question': 'What products are regulated by Safety Standard 1?'})
        
        # Verify the result
        self.assertIn('query_plan', result)
        self.assertEqual(len(result['query_plan']), 1)
        self.assertEqual(
            result['query_plan'][0]['purpose'], 
            'Find products regulated by Safety Standard 1'
        )
        
        # Verify that examples were used in the prompt
        prompt_args = mock_llm.chat.completions.create.call_args[1]['messages'][1]['content']
        self.assertIn('What products are in the Electronics category?', prompt_args)
        self.assertIn('Which regulations apply to Laptop products?', prompt_args)
    
    @patch('scripts.client.get_llm_client')
    def test_end_to_end_with_mocks(self, mock_get_llm_client):
        """Test the end-to-end flow with mocked components."""
        # Create mock LLM client
        mock_llm = MagicMock()
        mock_get_llm_client.return_value = mock_llm
        
        # Set up the LLM response for schema generation
        mock_schema_response = MagicMock()
        mock_schema_response.choices = [MagicMock()]
        mock_schema_response.choices[0].message.content = json.dumps({
            "examples": self.mock_examples
        })
        
        # Set up the LLM response for query decomposition
        mock_query_response = MagicMock()
        mock_query_response.choices = [MagicMock()]
        mock_query_response.choices[0].message.content = json.dumps({
            "query_plan": [
                {
                    "purpose": "Find products regulated by Safety Standard 1",
                    "cypher": "MATCH (p:Product)-[r:REGULATED_BY]->(reg:Regulation {name: 'Safety Standard 1'}) RETURN p.name, p.category, r.confidence"
                }
            ],
            "thought_process": "This query finds all Product nodes that have a REGULATED_BY relationship to a Regulation node with name 'Safety Standard 1'"
        })
        
        # Configure the mock to return different responses based on the prompt
        def mock_llm_side_effect(**kwargs):
            messages = kwargs.get('messages', [])
            if any('generate' in msg.get('content', '') for msg in messages):
                return mock_schema_response
            else:
                return mock_query_response
                
        mock_llm.chat.completions.create.side_effect = mock_llm_side_effect
        
        # Create schema cache
        schema_cache = MemorySchemaCache()
        schema_cache.set('schema', self.mock_schema)
        schema_cache.set('rich_context', self.mock_rich_context)
        
        # Create example repository
        example_repo = MemoryExampleRepository()
        example_repo.store_examples(self.mock_examples)
        
        # Create schema loader (with pre-filled mock data)
        schema_loader = MagicMock()
        schema_loader.load_schema.return_value = self.mock_schema
        schema_loader.get_formatted_schema.return_value = "MOCK FORMATTED SCHEMA"
        
        # Create schema manager
        schema_manager = SchemaManager(
            schema_loader=schema_loader,
            schema_cache=schema_cache,
            example_repository=example_repo,
            llm_client=mock_llm
        )
        
        # Create prompt builder
        prompt_builder = PromptBuilder()
        
        # Create query decomposition agent
        agent = QueryDecompositionAgent(schema_manager=schema_manager)
        agent.prompt_builder = prompt_builder
        agent.llm_client = mock_llm
        
        # Process a query
        result = agent.process({'question': 'What products are regulated by Safety Standard 1?'})
        
        # Check the result
        self.assertIn('query_plan', result)
        self.assertEqual(len(result['query_plan']), 1)
        self.assertEqual(
            result['query_plan'][0]['purpose'], 
            'Find products regulated by Safety Standard 1'
        )
        
        # Verify that the LLM was called with examples in the prompt
        self.assertTrue(mock_llm.chat.completions.create.called)

if __name__ == '__main__':
    unittest.main()