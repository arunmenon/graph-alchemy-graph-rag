#!/usr/bin/env python3
"""
Run Graph RAG API - Script to start the Graph RAG API server.

This script launches the FastAPI server for the Graph RAG service.
"""

import uvicorn
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Graph RAG API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()
    
    logger.info(f"Starting Graph RAG API server on {args.host}:{args.port}")

    # Import sys and add the current working directory to the path
    import sys, os
    sys.path.insert(0, os.getcwd())
    
    # Create endpoint app file in the current directory if it doesn't exist
    endpoint_file = "app.py"
    if not os.path.exists(endpoint_file):
        logger.info(f"Creating endpoint file: {endpoint_file}")
        with open(endpoint_file, "w") as f:
            f.write("""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the path
sys.path.insert(0, os.getcwd())

# Import the required modules
try:
    from agents.rag_orchestrator import GraphRAGAgent
    from schema.manager import SchemaManager
    schema_manager = SchemaManager()
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    raise

# Define API models
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    reasoning: str
    evidence: List[str]
    confidence: float
    processing_time: float

class SchemaResponse(BaseModel):
    success: bool
    message: str
    schema: Optional[Dict[str, Any]] = None

# Create FastAPI application
app = FastAPI(
    title="Taxonomy Graph RAG API",
    description="API for querying taxonomy information using a graph RAG approach",
    version="1.0.0"
)

# Initialize the Graph RAG agent with preloading disabled for faster startup
# The schema will be loaded on the first request instead
graph_rag_agent = GraphRAGAgent(preload_schema=False)

# Dependency to get the schema for endpoints
async def get_schema():
    \"\"\"Get the current graph schema.\"\"\"
    try:
        # Get the raw schema data for API response
        schema_data = schema_manager.get_schema()
        return schema_data
    except Exception as e:
        logger.error(f"Error retrieving schema: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schema: {str(e)}")

@app.post("/query", response_model=AnswerResponse)
async def query_taxonomy(request: QuestionRequest):
    \"\"\"
    Query the taxonomy with a natural language question.
    
    Args:
        request: Object containing the question
        
    Returns:
        Object containing the answer and supporting information
    \"\"\"
    try:
        result = graph_rag_agent.process_question(request.question)
        
        # Extract the relevant fields for the response
        response = {
            "answer": result.get("answer", ""),
            "reasoning": result.get("reasoning", ""),
            "evidence": result.get("evidence", []),
            "confidence": result.get("confidence", 0.0),
            "processing_time": result.get("processing_time", 0.0)
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema", response_model=SchemaResponse)
async def get_current_schema(schema: Dict = Depends(get_schema)):
    \"\"\"
    Get the current graph schema information.
    
    Returns:
        Object containing the current schema
    \"\"\"
    return {
        "success": True,
        "message": "Schema retrieved successfully",
        "schema": schema
    }

@app.post("/schema/refresh", response_model=SchemaResponse)
async def refresh_schema():
    \"\"\"
    Force a refresh of the graph schema information.
    
    Returns:
        Object indicating success or failure
    \"\"\"
    success = graph_rag_agent.refresh_schema()
    
    if success:
        # Get the newly refreshed schema
        schema_data = schema_manager.get_schema(force_refresh=True)
        return {
            "success": True,
            "message": "Schema refreshed successfully",
            "schema": schema_data
        }
    else:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to refresh schema",
                "schema": None
            }
        )

@app.get("/health")
async def health_check():
    \"\"\"
    Health check endpoint.
    
    Returns:
        Object indicating the service is up
    \"\"\"
    return {"status": "ok", "service": "graph-rag-api"}
"""
            )
    
    # Run the API with the local endpoint file
    logger.info(f"Running with local app.py file")
    uvicorn.run(
        "app:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload
    )