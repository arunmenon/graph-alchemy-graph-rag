#!/usr/bin/env python3
"""
Cleanup Script for Graph RAG Migration

This script helps clean up the original agentic_workflow.graph_rag module
after the migration to a standalone package is complete.

It creates a migration notice file and can optionally remove the original files,
but only after you confirm the standalone package is working properly.
"""

import os
import shutil
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_migration_notice(agentic_workflow_path):
    """Create a migration notice in the original module location."""
    graph_rag_path = os.path.join(agentic_workflow_path, 'graph_rag')
    notice_path = os.path.join(graph_rag_path, 'MIGRATION_NOTICE.md')
    
    notice_content = """# Migration Notice

This module has been migrated to a standalone package.

Please update your imports from:
```python
from agentic_workflow.graph_rag import ...
```

To:
```python
from graph_rag import ...
```

The standalone package provides the same functionality with an improved structure
and easier maintenance.
"""
    
    try:
        with open(notice_path, 'w') as f:
            f.write(notice_content)
        logger.info(f"Created migration notice at {notice_path}")
    except Exception as e:
        logger.error(f"Error creating migration notice: {e}")

def create_stub_init(agentic_workflow_path):
    """Create a stub __init__.py file that provides import forwarding."""
    graph_rag_path = os.path.join(agentic_workflow_path, 'graph_rag')
    init_path = os.path.join(graph_rag_path, '__init__.py')
    
    stub_content = """\"\"\"
MIGRATION NOTICE: This module has been moved to a standalone package.

Please update your imports to use 'graph_rag' instead of 'agentic_workflow.graph_rag'.
\"\"\"

import warnings

warnings.warn(
    "The agentic_workflow.graph_rag module has been moved to a standalone package. "
    "Please update your imports to use 'graph_rag' instead.",
    DeprecationWarning,
    stacklevel=2
)

try:
    # Try to import from the new package
    from graph_rag import (
        GraphRAGAgent,
        QueryDecompositionAgent,
        GraphRetrieverAgent,
        ReasoningAgent,
        schema_manager,
        get_config,
        DEFAULT_CONFIG,
    )
    
    # Re-export for backwards compatibility
    __all__ = [
        'GraphRAGAgent',
        'QueryDecompositionAgent',
        'GraphRetrieverAgent',
        'ReasoningAgent',
        'schema_manager',
        'get_config',
        'DEFAULT_CONFIG',
    ]
    
except ImportError:
    # If we can't import from the new package,
    # keep original imports for backwards compatibility
    warnings.warn(
        "Could not import from standalone graph_rag package. "
        "Using original implementation, but this will be removed in a future version.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Original imports from this package
    from .agents.query_decomposition import QueryDecompositionAgent
    from .agents.graph_retriever import GraphRetrieverAgent
    from .agents.reasoning import ReasoningAgent
    from .agents.rag_orchestrator import GraphRAGAgent
    from .schema.schema_manager import schema_manager
    from .config import get_config, DEFAULT_CONFIG
    
    __all__ = [
        'GraphRAGAgent',
        'QueryDecompositionAgent',
        'GraphRetrieverAgent',
        'ReasoningAgent',
        'schema_manager',
        'get_config',
        'DEFAULT_CONFIG',
    ]
"""
    
    try:
        with open(init_path, 'w') as f:
            f.write(stub_content)
        logger.info(f"Created stub __init__.py at {init_path}")
    except Exception as e:
        logger.error(f"Error creating stub __init__.py: {e}")

def remove_original_files(agentic_workflow_path, backup=True):
    """
    Remove the original graph_rag files.
    
    Args:
        agentic_workflow_path: Path to the agentic_workflow directory
        backup: Whether to create a backup before removing
    """
    graph_rag_path = os.path.join(agentic_workflow_path, 'graph_rag')
    
    if not os.path.exists(graph_rag_path):
        logger.error(f"Original module not found at {graph_rag_path}")
        return
    
    if backup:
        backup_dir = f"{graph_rag_path}_backup"
        try:
            shutil.copytree(graph_rag_path, backup_dir)
            logger.info(f"Created backup at {backup_dir}")
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return
    
    try:
        # Instead of removing everything, keep the stub __init__.py
        # Delete subdirectories
        for item in os.listdir(graph_rag_path):
            item_path = os.path.join(graph_rag_path, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                logger.info(f"Removed directory: {item_path}")
            elif os.path.isfile(item_path) and item != '__init__.py' and item != 'MIGRATION_NOTICE.md':
                os.remove(item_path)
                logger.info(f"Removed file: {item_path}")
        
        logger.info("Completed removal of original files")
    except Exception as e:
        logger.error(f"Error removing original files: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup original graph_rag module after migration")
    parser.add_argument('--agentic-path', required=True, help='Path to the agentic_workflow directory')
    parser.add_argument('--remove', action='store_true', help='Remove original files (with backup)')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup when removing files')
    args = parser.parse_args()
    
    create_migration_notice(args.agentic_path)
    create_stub_init(args.agentic_path)
    
    if args.remove:
        remove_original_files(args.agentic_path, backup=not args.no_backup)
    else:
        logger.info("Skipping removal of original files. Use --remove to enable this step.")
    
    logger.info("Cleanup process completed")