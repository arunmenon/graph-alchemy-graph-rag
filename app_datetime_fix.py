from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
import os
import sys
import json
from datetime import datetime, date

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the path
sys.path.insert(0, os.getcwd())

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

def serializable_dict(obj):
    """Convert an object to a serializable dictionary."""
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serializable_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [serializable_dict(x) for x in obj]
    else:
        return str(obj)

# Import the required modules
try:
    # Create a function to import our modules with a simplified approach
    def setup_schema_and_agent():
        try:
            # First try importing the modules as a package
            from agents.rag_orchestrator import GraphRAGAgent
            from schema.manager import SchemaManager
            
            # Create a schema manager
            schema_manager = SchemaManager()
            
            # Create the agent
            graph_rag_agent = GraphRAGAgent(preload_schema=False)
            
            return schema_manager, graph_rag_agent
        except ImportError:
            # Fall back to simpler imports
            import sys
            sys.path.append(".")  # Add current directory to path
            
            from schema.manager import SchemaManager
            
            # Create schema manager
            schema_manager = SchemaManager()
            
            # Create a simple agent class
            class SimpleGraphRAGAgent:
                def __init__(self):
                    self.schema_manager = schema_manager
                
                def process_question(self, question):
                    return {
                        "answer": f"This is a placeholder answer for: {question}",
                        "reasoning": "Simple reasoning process",
                        "evidence": ["No evidence available in simplified mode"],
                        "confidence": 0.5,
                        "processing_time": 0.0
                    }
                    
                def refresh_schema(self):
                    return True
            
            # Return simplified implementations
            return schema_manager, SimpleGraphRAGAgent()
    
    # Set up schema manager and agent
    schema_manager, graph_rag_agent = setup_schema_and_agent()
except Exception as e:
    logger.error(f"Error setting up modules: {e}")
    # Create minimal implementations for testing the API
    class SimpleSchemaManager:
        def get_schema(self, force_refresh=False):
            return {"node_types": {}, "relationship_types": {}}
            
    class SimpleGraphRAGAgent:
        def process_question(self, question):
            return {
                "answer": f"API is running but modules could not be loaded. Error: {e}",
                "reasoning": "Error in setup",
                "evidence": [],
                "confidence": 0.0,
                "processing_time": 0.0
            }
            
        def refresh_schema(self):
            return False
            
    schema_manager = SimpleSchemaManager()
    graph_rag_agent = SimpleGraphRAGAgent()

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
    schema_data: Optional[Dict[str, Any]] = None  # Renamed from 'schema' to avoid shadowing BaseModel attribute

# Create FastAPI application
app = FastAPI(
    title="Taxonomy Graph RAG API",
    description="API for querying taxonomy information using a graph RAG approach",
    version="1.0.0"
)

# Note: We already initialized the graph_rag_agent in the imports section

# Dependency to get the schema for endpoints
async def get_schema():
    """Get the current graph schema."""
    try:
        # Get the raw schema data for API response
        schema_data = schema_manager.get_schema()
        
        # Convert to serializable form
        return serializable_dict(schema_data)
    except Exception as e:
        logger.error(f"Error retrieving schema: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schema: {str(e)}")

@app.post("/query", response_model=AnswerResponse)
async def query_taxonomy(request: QuestionRequest):
    """
    Query the taxonomy with a natural language question.
    
    Args:
        request: Object containing the question
        
    Returns:
        Object containing the answer and supporting information
    """
    try:
        # Process the question and get the result
        raw_result = graph_rag_agent.process_question(request.question)
        
        # Convert to serializable form
        result = serializable_dict(raw_result)
        
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
        # Return a fallback response instead of raising an exception
        return {
            "answer": f"Sorry, an error occurred while processing your question: {str(e)}",
            "reasoning": "Error in processing",
            "evidence": [],
            "confidence": 0.0,
            "processing_time": 0.0
        }

@app.get("/schema", response_model=SchemaResponse)
async def get_current_schema(schema: Dict = Depends(get_schema)):
    """
    Get the current graph schema information.
    
    Returns:
        Object containing the current schema
    """
    return {
        "success": True,
        "message": "Schema retrieved successfully",
        "schema_data": schema
    }

@app.post("/schema/refresh", response_model=SchemaResponse)
async def refresh_schema():
    """
    Force a refresh of the graph schema information.
    
    Returns:
        Object indicating success or failure
    """
    try:
        success = graph_rag_agent.refresh_schema()
        
        if success:
            # Get the newly refreshed schema
            schema_data = schema_manager.get_schema(force_refresh=True)
            
            # Convert to serializable form
            schema_data = serializable_dict(schema_data)
            
            return {
                "success": True,
                "message": "Schema refreshed successfully",
                "schema_data": schema_data
            }
        else:
            return {
                "success": False,
                "message": "Failed to refresh schema",
                "schema_data": None
            }
    except Exception as e:
        logger.error(f"Error refreshing schema: {e}")
        return {
            "success": False,
            "message": f"Error refreshing schema: {str(e)}",
            "schema_data": None
        }

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Object indicating the service is up
    """
    return {"status": "ok", "service": "graph-rag-api"}
