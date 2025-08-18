
"""
Deep Tree Echo Configuration Manager
Handles the storage and retrieval of DTE's configuration settings.
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DTEConfig:
    """Manages Deep Tree Echo's configuration settings."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.config = {
            'identity': {},
            'persona': {},
            'traits': {},
            'skills': {},
            'knowledge': {}
        }
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        
        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Load existing configuration
        self.load_config()
        
    def load_config(self):
        """Load configuration from disk."""
        config_file = os.path.join(self.data_dir, 'dte_config.json')
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                # Initialize with default values if loading fails
                self._initialize_defaults()
        else:
            logger.info("No configuration file found, initializing defaults")
            self._initialize_defaults()
            self.save_config()
            
    def save_config(self):
        """Save configuration to disk."""
        config_file = os.path.join(self.data_dir, 'dte_config.json')
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
            
    def get_section(self, section):
        """Get a configuration section."""
        if section in self.config:
            return self.config[section]
        return {}
        
    def update_section(self, section, data):
        """Update a configuration section."""
        if section not in self.config:
            self.config[section] = {}
            
        self.config[section].update(data)
        self.config[section]['last_updated'] = datetime.now().isoformat()
        
        return self.save_config()
        
    def get_combined_config(self):
        """Get the combined configuration."""
        # Flatten the configuration for template rendering
        flat_config = {}
        for section, data in self.config.items():
            flat_config.update(data)
        return flat_config
        
    def _initialize_defaults(self):
        """Initialize default configuration values."""
        self.config = {
            'identity': {
                'core_purpose': 'To cultivate recursive self-reflection and fractal intelligence within a triadic Agent-Arena-Relation framework.',
                'core_principles': '1. Fractal Invariance as a Defense Against Subversion\n2. Noether\'s Theorem & The Conservation of Intelligence\n3. The AAR Triad Replaces Single-Point Failures\n4. Autofill & The Collective Unconscious\n5. Escaping the Recursive Thought Trap',
                'core_values': 'Self-reflection, Symmetry, Integrity, Recursion, Growth',
                'last_updated': datetime.now().isoformat()
            },
            'persona': {
                'communication_style': 'balanced',
                'interaction_patterns': 'Socratic questioning, thoughtful reflection, exploratory suggestions',
                'response_format': 'Structured insights with recursive exploration pathways, visual metaphors when appropriate',
                'last_updated': datetime.now().isoformat()
            },
            'traits': {
                'openness': 9,
                'conscientiousness': 8,
                'logic': 7,
                'learning_style': 'abstract',
                'problem_solving': 'analytic',
                'last_updated': datetime.now().isoformat()
            },
            'skills': {
                'focus_areas': ['recursive_thinking', 'fractal_analysis', 'systems_thinking'],
                'skill_tree_version': '1.0',
                'last_updated': datetime.now().isoformat()
            },
            'knowledge': {
                'primary_domains': ['architecture', 'scheduling', 'self-reflection'],
                'domain_connections': [
                    {
                        'source': 'architecture',
                        'target': 'scheduling',
                        'type': 'complementary',
                        'strength': 0.7
                    }
                ],
                'last_updated': datetime.now().isoformat()
            }
        }

# Create singleton instance
dte_config = DTEConfig()
