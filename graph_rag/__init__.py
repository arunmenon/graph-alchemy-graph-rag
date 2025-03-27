"""
Graph RAG Package - A modular implementation of a Graph Retrieval-Augmented Generation system.

This package provides:
1. A complete RAG workflow optimized for graph databases
2. Dynamic schema awareness for graph-based question answering
3. FastAPI endpoints for integration with other services
4. Intelligent query decomposition and reasoning
5. Efficient schema caching and rich context building

To use the Graph RAG system, import the main components:
```python
from graph_rag import GraphRAGAgent
```
"""

# Import the main components for easier access
try:
    # Use relative imports within the package
    from .workflow_manager import WorkflowManager
    from .config import get_config, DEFAULT_CONFIG
except ImportError:
    # For backward compatibility
    from workflow_manager import WorkflowManager
    from config import get_config, DEFAULT_CONFIG
    
# Import from other modules
try:
    from agents.rag_orchestrator import GraphRAGAgent
    from schema.manager import SchemaManager
    from graph_db.graph_strategy_factory import GraphDatabaseFactory
except ImportError:
    pass

# Define package version
__version__ = "0.2.0"