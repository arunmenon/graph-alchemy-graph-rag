"""
Tier Classification Module - Manages prioritization of entity types for embedding.

This module provides functionality to classify entity types into tiers for prioritized
embedding generation, based on importance and connectivity.
"""

import logging
from typing import Dict, List, Any, Set, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TierClassifier:
    """Classifies entity types into tiers for prioritized embedding generation."""
    
    def __init__(self, graph_db):
        """
        Initialize the tier classifier.
        
        Args:
            graph_db: Graph database connection
        """
        self.graph_db = graph_db
        self.tier_definitions = {
            1: {"name": "Primary", "description": "Key entity types with high importance"},
            2: {"name": "Secondary", "description": "Entity types with moderate connectivity"},
            3: {"name": "Tertiary", "description": "All remaining entity types"}
        }
        
        # Default tier mappings if schema analysis fails
        self.default_tier_mappings = {
            1: ["Table", "Entity", "Concept", "Category", "Product", "Asset"],
            2: ["Property", "Attribute", "Type", "Class", "Department", "Rule"],
            3: ["Instance", "Value", "Record", "Example", "Metadata"]
        }
        
        self.custom_tier_mappings = {}
    
    def analyze_schema(self) -> Dict[int, List[str]]:
        """
        Analyze the database schema to classify entity types into tiers.
        
        Returns:
            Dictionary mapping tier numbers to lists of entity type names
        """
        try:
            # Get all node labels
            label_query = """
            CALL db.labels() YIELD label
            RETURN label
            """
            label_results = self.graph_db.execute_query(label_query)
            all_labels = [record["label"] for record in label_results]
            
            # Get relationship counts for each label
            tier_mappings = {1: [], 2: [], 3: []}
            
            for label in all_labels:
                try:
                    # Count nodes with this label
                    count_query = f"""
                    MATCH (n:{label})
                    RETURN count(n) as node_count
                    """
                    count_result = self.graph_db.execute_query(count_query)
                    node_count = count_result[0]["node_count"] if count_result else 0
                    
                    # Count relationships for this label
                    rel_query = f"""
                    MATCH (n:{label})-[r]-()
                    RETURN count(r) as rel_count
                    """
                    rel_result = self.graph_db.execute_query(rel_query)
                    rel_count = rel_result[0]["rel_count"] if rel_result else 0
                    
                    # Calculate connectivity ratio
                    connectivity = rel_count / node_count if node_count > 0 else 0
                    
                    # Determine tier based on node count and connectivity
                    if any(key_term in label.lower() for key_term in ["table", "entity", "concept", "category"]) or node_count > 1000:
                        tier = 1  # Primary tier for key entities or large collections
                    elif connectivity > 5 or node_count > 500:
                        tier = 2  # Secondary tier for well-connected entities
                    else:
                        tier = 3  # Tertiary tier for everything else
                    
                    # Add to tier mappings
                    tier_mappings[tier].append(label)
                    
                except Exception as label_error:
                    logger.warning(f"Error analyzing label {label}: {label_error}")
                    # Default to tier 3 on error
                    tier_mappings[3].append(label)
            
            logger.info(f"Analyzed schema and classified {len(all_labels)} entity types into tiers")
            logger.info(f"Tier 1 (Primary): {len(tier_mappings[1])} types")
            logger.info(f"Tier 2 (Secondary): {len(tier_mappings[2])} types")
            logger.info(f"Tier 3 (Tertiary): {len(tier_mappings[3])} types")
            
            return tier_mappings
            
        except Exception as e:
            logger.error(f"Error in schema analysis: {e}")
            # Return default tier mappings if analysis fails
            logger.warning("Using default tier mappings due to analysis failure")
            return {tier: self.default_tier_mappings.get(tier, []) for tier in [1, 2, 3]}
    
    def get_tier_for_label(self, label: str) -> int:
        """
        Get the tier number for a specific label.
        
        Args:
            label: Node label to get tier for
            
        Returns:
            Tier number (1, 2, or 3)
        """
        # Check custom mappings first
        for tier, labels in self.custom_tier_mappings.items():
            if label in labels:
                return tier
        
        # If no custom mapping, check each tier in the default mappings
        for tier, labels in self.default_tier_mappings.items():
            if any(key_term.lower() in label.lower() for key_term in labels):
                return tier
        
        # Default to tier 3 if no match found
        return 3
    
    def set_custom_tier_mapping(self, tier_mappings: Dict[int, List[str]]) -> None:
        """
        Set custom tier mappings for entity types.
        
        Args:
            tier_mappings: Dictionary mapping tier numbers to lists of entity type names
        """
        self.custom_tier_mappings = tier_mappings
        logger.info("Set custom tier mappings")
        
        # Log the mappings for debugging
        for tier, labels in tier_mappings.items():
            logger.info(f"Tier {tier}: {', '.join(labels)}")
    
    def get_tier_definitions(self) -> Dict[int, Dict[str, str]]:
        """
        Get definitions for each tier.
        
        Returns:
            Dictionary mapping tier numbers to their definitions
        """
        return self.tier_definitions
    
    def get_labels_for_tier(self, tier: int) -> List[str]:
        """
        Get all labels for a specific tier.
        
        Args:
            tier: Tier number to get labels for
            
        Returns:
            List of entity type names in the specified tier
        """
        if self.custom_tier_mappings and tier in self.custom_tier_mappings:
            return self.custom_tier_mappings[tier]
        
        # If no custom mappings or the tier isn't in custom mappings,
        # fall back to analyzing the schema
        tier_mappings = self.analyze_schema()
        return tier_mappings.get(tier, [])