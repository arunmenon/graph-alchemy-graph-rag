"""Base classes and interfaces for agents in the workflow.

This module provides abstract base classes and interfaces to implement
the Strategy, Template Method, and Chain of Responsibility patterns.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class Agent(ABC):
    """
    Abstract base class for all agents in the workflow.
    
    Implements the Template Method pattern by defining a standard process
    method with hooks for pre-processing and post-processing.
    """
    
    def __init__(self, name: str = None):
        """Initialize the agent with a name."""
        self.name = name or self.__class__.__name__
        self.next_agent = None  # For Chain of Responsibility
    
    def set_next(self, agent: 'Agent') -> 'Agent':
        """
        Set the next agent in the chain of responsibility.
        
        Returns the next agent, allowing for method chaining.
        """
        self.next_agent = agent
        return agent
    
    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Template method defining the standard process flow.
        
        Args:
            data: Input data specific to this processing step
            context: Shared workflow context that persists across steps
            
        Returns:
            Processed data with results from this agent
        """
        self.pre_process(data, context)
        result = self.execute(data, context)
        self.post_process(result, context)
        
        if self.next_agent:
            return self.next_agent.process(result, context)
        return result
    
    def pre_process(self, data: Dict[str, Any], context: Dict[str, Any]) -> None:
        """
        Hook method called before execution. Override for custom pre-processing.
        
        Args:
            data: Input data for this agent
            context: Shared workflow context
        """
        pass
    
    @abstractmethod
    def execute(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core execution method that must be implemented by concrete agent classes.
        
        Args:
            data: Input data for this agent
            context: Shared workflow context
            
        Returns:
            Processed data with agent results
        """
        pass
    
    def post_process(self, result: Dict[str, Any], context: Dict[str, Any]) -> None:
        """
        Hook method called after execution. Override for custom post-processing.
        
        Args:
            result: Output from execute method
            context: Shared workflow context
        """
        pass


class LLMProvider(ABC):
    """
    Strategy interface for LLM providers.
    
    Allows different LLM providers to be used interchangeably.
    """
    
    @abstractmethod
    def generate(self, 
                 prompt: str, 
                 system_prompt: str = None, 
                 temperature: float = 0.7,
                 max_tokens: int = None) -> str:
        """
        Generate text using the LLM provider.
        
        Args:
            prompt: User prompt for generation
            system_prompt: System context/instructions
            temperature: Randomness parameter (0-1)
            max_tokens: Maximum output length
            
        Returns:
            Generated text response
        """
        pass