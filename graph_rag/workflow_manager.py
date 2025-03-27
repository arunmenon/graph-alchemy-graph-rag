"""Workflow Manager - Reusable workflow functionality shared by different agent pipelines.

This module provides a workflow manager that can be used by different agent pipelines
to manage agent registration and execution in a uniform way.
"""

import logging
import time
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def make_serializable(obj: Any) -> Any:
    """Convert any object to a JSON serializable format."""
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [make_serializable(x) for x in obj]
    else:
        # Convert any other object to string
        return str(obj)

class WorkflowManager:
    """Reusable workflow functionality shared by different agent pipelines."""
    
    def __init__(self, name: str = "workflow", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the workflow manager.
        
        Args:
            name: Name of the workflow for logging purposes
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.agents = {}
        self.agent_pipeline = []
        self.hooks = {
            'pre_process': [],
            'post_process': []
        }
    
    def add_agent(self, agent):
        """
        Add an agent to the workflow.
        
        Args:
            agent: The agent to add to the workflow
            
        Returns:
            The added agent for method chaining
        """
        agent_name = agent.name
        self.agents[agent_name] = agent
        if agent_name not in self.agent_pipeline:
            self.agent_pipeline.append(agent_name)
        logger.debug(f"Added agent '{agent_name}' to workflow '{self.name}'")
        return agent
    
    def register_hook(self, hook_point: str, hook_function):
        """
        Register a hook function to be called at a specific point in the workflow.
        
        Args:
            hook_point (str): The point in the workflow to call the hook 
                              ('pre_process' or 'post_process')
            hook_function (callable): A function to call at the specified hook point
            
        Returns:
            bool: True if hook was registered, False if hook_point is invalid
        """
        if hook_point in self.hooks:
            self.hooks[hook_point].append(hook_function)
            return True
        return False
    
    def _run_hooks(self, hook_point: str, **kwargs):
        """
        Run all registered hooks for a given hook point with the provided arguments.
        
        Args:
            hook_point: The hook point to run
            **kwargs: Arguments to pass to the hook functions
            
        Returns:
            List of hook function results
        """
        results = []
        for hook_func in self.hooks.get(hook_point, []):
            try:
                result = hook_func(**kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in {hook_point} hook: {str(e)}")
        return results
    
    def run_pipeline(self, input_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the workflow with the given input data.
        
        Args:
            input_data: The input data to process through the workflow
            context: Optional shared context
            
        Returns:
            The result of the workflow
        """
        logger.info(f"Running workflow '{self.name}'...")
        
        # Start timing
        start_time = time.time()
        
        # Initialize context if not provided
        context = context or {}
        
        # Run pre-process hooks
        self._run_hooks('pre_process', workflow=self, input_data=input_data, context=context)
        
        # Start with the input data
        result = input_data
        
        # Run each agent in the pipeline
        for agent_name in self.agent_pipeline:
            agent = self.agents.get(agent_name)
            if agent:
                logger.info(f"Running agent: {agent_name}")
                agent_start_time = time.time()
                try:
                    # Execute the agent and ensure result is serializable
                    agent_result = agent.execute(result, context)
                    if agent_result:
                        result = agent_result
                    agent_execution_time = time.time() - agent_start_time
                    logger.info(f"Agent {agent_name} completed in {agent_execution_time:.2f}s")
                except Exception as e:
                    logger.error(f"Error in agent {agent_name}: {e}")
                    # Add error to result if possible
                    if isinstance(result, dict):
                        result['error'] = str(e)
                        result['error_agent'] = agent_name
            else:
                logger.warning(f"Agent {agent_name} not found in workflow")
        
        # Calculate total processing time
        processing_time = time.time() - start_time
        
        # Add processing time to result
        if isinstance(result, dict):
            result['processing_time'] = processing_time
        
        # Run post-process hooks
        self._run_hooks('post_process', workflow=self, result=result, context=context)
        
        # Make sure the result is JSON serializable
        serializable_result = make_serializable(result)
        
        logger.info(f"Workflow '{self.name}' completed in {processing_time:.2f}s")
        return serializable_result