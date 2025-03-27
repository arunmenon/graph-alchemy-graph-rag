"""
Examples module - Provides functionality for generating and managing example Q&A pairs.

This module contains components for:
1. Generators: Generate examples based on schema and data patterns
2. Storage: Store and retrieve generated examples
3. Factory: Create appropriate generators based on configuration
"""

# Import key components for easier access
from .factory import ExampleGeneratorFactory
from .generators.base_generator import ExampleGeneratorInterface
from .generators.pattern_generator import PatternExampleGenerator
from .storage.example_repository import ExampleRepositoryInterface, FileExampleRepository