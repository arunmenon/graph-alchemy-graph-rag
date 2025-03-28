"""
Test Semantic Search Module - Tests for the semantic search implementation.

This module contains tests for the semantic search functionality, including
embedding providers, entity retrieval, and tier classification.
"""

import os
import sys
import unittest
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from semantic.embedding_provider import DummyEmbeddingProvider
from semantic.entity_retriever import SemanticEntityRetriever
from semantic.tier_classification import TierClassifier
from graph_db.graph_strategy_factory import GraphDatabaseFactory

class TestEmbeddingProvider(unittest.TestCase):
    """Tests for the embedding provider implementation."""
    
    def test_dummy_provider(self):
        """Test the dummy embedding provider."""
        provider = DummyEmbeddingProvider(dimension=128)
        
        # Test single text encoding
        single_embedding = provider.encode("Test text")
        self.assertEqual(len(single_embedding), 128)
        
        # Test batch encoding
        batch_embeddings = provider.batch_encode(["Text 1", "Text 2", "Text 3"])
        self.assertEqual(len(batch_embeddings), 3)
        self.assertEqual(len(batch_embeddings[0]), 128)
        
        # Test similarity
        similarity = provider.similarity(
            [0.1] * 128,
            [0.2] * 128
        )
        self.assertTrue(0 <= similarity <= 1)

class TestSemanticEntityRetriever(unittest.TestCase):
    """Tests for the semantic entity retriever."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test dependencies."""
        cls.graph_db = GraphDatabaseFactory.create_graph_database_strategy()
        connected = cls.graph_db.connect()
        if not connected:
            logger.warning("Could not connect to Neo4j, some tests will be skipped")
        
        cls.embedding_provider = DummyEmbeddingProvider()
        cls.retriever = SemanticEntityRetriever(cls.graph_db, cls.embedding_provider)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test dependencies."""
        if cls.graph_db:
            cls.graph_db.close()
    
    def test_search_functionality(self):
        """Test basic search functionality."""
        # Skip if database connection failed
        if not self.graph_db.driver:
            self.skipTest("No database connection")
        
        # Test text search (without vector index)
        results = self.retriever.search("test query", limit=5)
        
        # Just verify that it returns a list (may be empty depending on database)
        self.assertIsInstance(results, list)
        
        # Check result format if any returned
        if results:
            result = results[0]
            self.assertIn("id", result)
            self.assertIn("labels", result)
            self.assertIn("properties", result)
            self.assertIn("score", result)
    
    def test_tier_classifier(self):
        """Test tier classification."""
        # Skip if database connection failed
        if not self.graph_db.driver:
            self.skipTest("No database connection")
        
        classifier = TierClassifier(self.graph_db)
        
        # Test default tier mappings
        tier = classifier.get_tier_for_label("Table")
        self.assertEqual(tier, 1)
        
        tier = classifier.get_tier_for_label("SomeRandomEntity")
        self.assertEqual(tier, 3)
        
        # Test custom tier mappings
        custom_mappings = {
            1: ["CustomEntity", "PrimaryType"],
            2: ["SecondaryType"],
            3: ["TertiaryType"]
        }
        classifier.set_custom_tier_mapping(custom_mappings)
        
        tier = classifier.get_tier_for_label("CustomEntity")
        self.assertEqual(tier, 1)

def run_tests():
    """Run all tests."""
    unittest.main()

if __name__ == "__main__":
    run_tests()