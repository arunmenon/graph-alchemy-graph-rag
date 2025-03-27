#!/bin/bash
# Run the Graph RAG API for testing

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
  echo "Activating virtual environment..."
  source venv/bin/activate
fi

# Set environment variables for Neo4j connection
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="Rathum12!"
export NEO4J_DATABASE="neo4j"

# Set OpenAI API key if provided as argument
if [ ! -z "$1" ]; then
  export OPENAI_API_KEY="$1"
fi

# Display a warning if OpenAI API key is not set
if [ -z "$OPENAI_API_KEY" ]; then
  echo "WARNING: OPENAI_API_KEY is not set. API queries that require LLM will fail."
  echo "Run this script with your API key as the first argument:"
  echo "  ./run_api.sh sk-your-api-key"
fi

# Extract port if provided
port=8000
for arg in "$@"; do
  if [[ $arg == --port=* ]]; then
    port=${arg#*=}
  fi
done

# Run the API with auto-reload for development
echo "Starting Graph RAG API on port $port..."
python scripts/run_api.py --reload --port $port

# Deactivate virtual environment on exit
if [ -d "venv" ]; then
  deactivate
fi