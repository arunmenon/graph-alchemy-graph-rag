# Graph RAG Migration Guide

This document provides guidance on migrating the `agentic_workflow.graph_rag` module to a standalone `graph_rag` package.

## Migration Progress

The current migration is partial. Here's what has been done:

1. Created basic package structure for the standalone `graph_rag` package
2. Added essential infrastructure like setup.py, README, .gitignore
3. Added base files for the standalone system to work (agent_base.py, workflow_manager.py)
4. Updated imports in some files to work with the new structure

## What To Complete

To finish the migration, complete these steps:

1. Copy over essential dependency modules:
   - If the system depends on `graph_db` module, you'll need to incorporate that
   - Include any other dependencies from the larger project

2. Fix import statements in all agent files:
   - Change imports from `from ...agent_base import Agent` to `from ..agent_base import Agent`
   - Update any other relative imports

3. Copy required prompt files:
   - Copy prompt files from `prompts/graph_rag/` to a new `graph_rag/prompts/` directory

4. Create or adapt configuration files:
   - Modify configuration to point to new locations for prompts, caches, etc.

5. Update schema_manager paths:
   - Ensure cache paths and other file paths are updated for the new package structure

6. Create simple examples:
   - Add a few example scripts showing the basic usage

7. Test the migration thoroughly:
   - Test the API functionality
   - Test the standalone agent components
   - Ensure the schema system still works

## File Changes Needed

1. Update imports in all agent files
2. Update paths for prompt locations in config.py and rag_orchestrator.py
3. Make sure any cache paths are correct in schema_manager.py
4. Create an examples directory with basic use cases
5. Fix the run_api.py script to work with proper imports

## External Dependencies

Some dependencies you'll need to consider:

1. Neo4j database connection (GraphDatabaseFactory from graph_db module)
2. Any OpenAI or other LLM providers
3. External configuration files or environment variables
4. Prompts and related resources

## Testing the Migration

To test the standalone package:

1. Create a virtual environment
2. Install the package using `pip install -e .`
3. Run the examples to ensure they work properly
4. Test the API functionality

## Adapting Code that Uses the Original Module

When transitioning code that uses `agentic_workflow.graph_rag`, update:

```python
# Old imports 
from agentic_workflow.graph_rag import GraphRAGAgent
from agentic_workflow.graph_rag.schema.schema_manager import schema_manager

# New imports
from graph_rag import GraphRAGAgent
from graph_rag.schema.schema_manager import schema_manager
```

## Helpful Alias During Transition

You may add an alias in your code temporarily to support both structures:

```python
try:
    # Try the new structure first
    from graph_rag import GraphRAGAgent
except ImportError:
    # Fall back to the old structure
    from agentic_workflow.graph_rag import GraphRAGAgent
```