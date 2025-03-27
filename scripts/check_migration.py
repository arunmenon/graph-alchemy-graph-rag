#!/usr/bin/env python3
"""
Migration Check Script for Graph RAG

This script verifies that the standalone graph_rag package 
has all the necessary files and structure to function properly.
"""

import os
import logging
import importlib.util
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_file_exists(filepath, critical=True):
    """Check if a file exists and log the result."""
    if os.path.exists(filepath):
        logger.info(f"✅ Found: {filepath}")
        return True
    else:
        if critical:
            logger.error(f"❌ Missing critical file: {filepath}")
        else:
            logger.warning(f"⚠️ Missing non-critical file: {filepath}")
        return False

def check_import(module_name, critical=True):
    """Check if a module can be imported."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            logger.info(f"✅ Import succeeded: {module_name}")
            return True
        else:
            if critical:
                logger.error(f"❌ Module not found: {module_name}")
            else:
                logger.warning(f"⚠️ Module not found (non-critical): {module_name}")
            return False
    except ImportError as e:
        if critical:
            logger.error(f"❌ Import error for {module_name}: {e}")
        else:
            logger.warning(f"⚠️ Import error for {module_name} (non-critical): {e}")
        return False

def check_migration_status():
    """Check the overall status of the migration."""
    # Get the current directory (should be graph_rag)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check package structure
    logger.info("Checking package structure...")
    check_file_exists(os.path.join(current_dir, '__init__.py'))
    check_file_exists(os.path.join(current_dir, 'setup.py'))
    check_file_exists(os.path.join(current_dir, 'README.md'))
    check_file_exists(os.path.join(current_dir, 'requirements.txt'))
    check_file_exists(os.path.join(current_dir, 'agent_base.py'))
    check_file_exists(os.path.join(current_dir, 'workflow_manager.py'))
    
    # Check directories
    logger.info("\nChecking directories...")
    check_file_exists(os.path.join(current_dir, 'agents'))
    check_file_exists(os.path.join(current_dir, 'schema'))
    check_file_exists(os.path.join(current_dir, 'api'))
    
    # Check critical agent files
    logger.info("\nChecking agent files...")
    check_file_exists(os.path.join(current_dir, 'agents', '__init__.py'))
    check_file_exists(os.path.join(current_dir, 'agents', 'rag_orchestrator.py'))
    check_file_exists(os.path.join(current_dir, 'agents', 'query_decomposition.py'))
    check_file_exists(os.path.join(current_dir, 'agents', 'graph_retriever.py'))
    check_file_exists(os.path.join(current_dir, 'agents', 'reasoning.py'))
    
    # Check schema files
    logger.info("\nChecking schema files...")
    check_file_exists(os.path.join(current_dir, 'schema', '__init__.py'))
    check_file_exists(os.path.join(current_dir, 'schema', 'schema_manager.py'))
    
    # Check API files
    logger.info("\nChecking API files...")
    check_file_exists(os.path.join(current_dir, 'api', '__init__.py'))
    check_file_exists(os.path.join(current_dir, 'api', 'endpoints.py'))
    
    # Check import functionality
    logger.info("\nChecking imports...")
    try:
        import sys
        # Add the parent directory to the Python path
        parent_dir = os.path.dirname(current_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Check imports
        check_import('graph_rag')
        check_import('graph_rag.agent_base', critical=True)
        check_import('graph_rag.workflow_manager', critical=True)
        check_import('graph_rag.schema.schema_manager', critical=True)
        
        # Optional imports that should work if migration is complete
        check_import('graph_rag.agents.rag_orchestrator', critical=False)
        check_import('graph_rag.api.endpoints', critical=False)
    except Exception as e:
        logger.error(f"Error checking imports: {e}")
    
    logger.info("\nMigration check complete. Check the logs for any issues that need to be addressed.")

if __name__ == "__main__":
    logger.info("Starting migration status check...")
    check_migration_status()