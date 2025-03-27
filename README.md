# Graph RAG

A modular implementation of a Graph Retrieval-Augmented Generation system optimized for graph databases.

## Overview

The Graph RAG system is a specialized Retrieval-Augmented Generation framework that:

1. Takes natural language questions about graph data
2. Decomposes them into graph queries (Cypher for Neo4j)
3. Retrieves relevant subgraphs from the database
4. Reasons over the retrieved context to produce comprehensive answers

## Features

- **Schema-aware query generation**: Uses the database schema to generate accurate queries
- **Dynamic example generation**: Automatically creates example question/query pairs based on database schema
- **Modular agent architecture**: Clean separation of concerns with specialized agents
- **Efficient caching**: Schema and example caching for improved performance
- **Rich context building**: Extracts and formats context from graph data
- **Query validation and correction**: Automatically fixes common query issues
- **Evidence-based reasoning**: Answers include supporting evidence and confidence scores
- **RESTful API**: Easy integration via API endpoints
- **Comprehensive testing**: Test suite for both components and end-to-end workflows

## Architecture

The system follows a three-step pipeline:

1. **Query Decomposition**: Transform natural language questions into graph database queries
2. **Graph Retrieval**: Execute generated queries and retrieve relevant subgraphs
3. **Reasoning**: Analyze retrieved data to generate comprehensive answers

## Components

- `QueryDecompositionAgent`: Breaks down questions into graph queries
- `GraphRetrieverAgent`: Executes graph queries and retrieves context
- `ReasoningAgent`: Reasons over graph context to generate answers
- `GraphRAGAgent`: Main orchestrating agent for the workflow
- `SchemaManager`: Manages graph schema information and caching
- `ExampleGenerator`: Dynamically generates example queries based on schema
- `PromptBuilder`: Builds prompts with schema and examples for better performance

## Usage

```python
from graph_rag import GraphRAGAgent

# Initialize the agent
agent = GraphRAGAgent(preload_schema=True)

# Ask a question
result = agent.process_question("What product categories are related to compliance area X?")

# Get the answer
print(result['answer'])
print(f"Confidence: {result['confidence']}")
```

## API

The system includes a FastAPI application that can be run as a service:

```bash
python run_api.py
```

This will start a server with endpoints for:
- `/query`: Process natural language questions
- `/schema`: Get the current database schema
- `/health`: Check system health