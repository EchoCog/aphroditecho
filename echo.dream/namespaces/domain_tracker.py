
"""
Domain Tracker for Deep Tree Echo
Monitors and analyzes DTE's learning progression across domains
"""

import logging
from datetime import datetime
import json
import os
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

class DomainTracker:
    """Tracks DTE's learning and progression across knowledge domains."""
    
    def __init__(self):
        self.domains = {}
        self.connections = []  # Cross-domain connections
        self.learning_history = []
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        
        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        self.load_domains()
    
    def load_domains(self):
        """Load existing domain data."""
        domains_file = os.path.join(self.data_dir, 'domains.json')
        if os.path.exists(domains_file):
            try:
                with open(domains_file, 'r') as f:
                    data = json.load(f)
                    self.domains = data.get('domains', {})
                    self.connections = data.get('connections', [])
                    self.learning_history = data.get('learning_history', [])
            except Exception as e:
                logger.error(f"Error loading domain data: {e}")
    
    def save_domains(self):
        """Save domain data to disk."""
        domains_file = os.path.join(self.data_dir, 'domains.json')
        data = {
            'domains': self.domains,
            'connections': self.connections,
            'learning_history': self.learning_history
        }
        
        try:
            with open(domains_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving domain data: {e}")
    
    def register_domain(self, name, description, core_concepts=None):
        """Register a new knowledge domain for tracking."""
        if name in self.domains:
            logger.warning(f"Domain {name} already exists")
            return False
        
        self.domains[name] = {
            'name': name,
            'description': description,
            'created': datetime.now().isoformat(),
            'mastery_level': 0.0,  # 0 to 1 scale
            'core_concepts': core_concepts or [],
            'learning_activities': []
        }
        
        self.save_domains()
        return True
    
    def log_learning_activity(self, domain, activity_type, description, duration_minutes, concepts_used=None):
        """Log a learning activity in a domain."""
        if domain not in self.domains:
            logger.error(f"Domain {domain} not found")
            return False
        
        activity = {
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'description': description,
            'duration_minutes': duration_minutes,
            'concepts_used': concepts_used or []
        }
        
        self.domains[domain]['learning_activities'].append(activity)
        
        # Also add to global learning history
        history_entry = activity.copy()
        history_entry['domain'] = domain
        self.learning_history.append(history_entry)
        
        # Update mastery level based on activity
        self._update_mastery(domain, activity)
        
        self.save_domains()
        return True
    
    def create_connection(self, domain1, domain2, connection_type, strength, description):
        """Create a connection between two domains."""
        if domain1 not in self.domains or domain2 not in self.domains:
            logger.error(f"One or both domains not found: {domain1}, {domain2}")
            return False
        
        connection = {
            'domains': [domain1, domain2],
            'type': connection_type,
            'strength': strength,  # 0 to 1 scale
            'description': description,
            'created': datetime.now().isoformat()
        }
        
        self.connections.append(connection)
        self.save_domains()
        return True
    
    def _update_mastery(self, domain, activity):
        """Update mastery level based on learning activity."""
        current_mastery = self.domains[domain]['mastery_level']
        
        # Simple model: each hour of activity increases mastery by 0.01 to 0.05
        # depending on activity type, up to maximum of 1.0
        mastery_gain = min(activity['duration_minutes'] / 60 * 0.03, 0.05)
        
        # Apply diminishing returns as mastery increases
        diminished_gain = mastery_gain * (1 - current_mastery/2)
        
        new_mastery = min(current_mastery + diminished_gain, 1.0)
        self.domains[domain]['mastery_level'] = new_mastery
    
    def get_domain_stats(self, domain=None):
        """Get statistics for one or all domains."""
        if domain:
            if domain not in self.domains:
                logger.error(f"Domain {domain} not found")
                return None
            return self.domains[domain]
        
        # Return summary stats for all domains
        return {
            'total_domains': len(self.domains),
            'total_connections': len(self.connections),
            'mastery_levels': {d: info['mastery_level'] for d, info in self.domains.items()},
            'learning_time': self._calculate_total_learning_time()
        }
    
    def _calculate_total_learning_time(self):
        """Calculate total learning time across all domains."""
        total_minutes = sum(activity['duration_minutes'] 
                           for domain_info in self.domains.values()
                           for activity in domain_info['learning_activities'])
        
        hours = total_minutes / 60
        return hours
    
    def generate_mastery_chart(self, output_file=None):
        """Generate a chart showing mastery levels of different domains."""
        if not self.domains:
            logger.warning("No domains to visualize")
            return False
        
        domain_names = list(self.domains.keys())
        mastery_levels = [self.domains[d]['mastery_level'] for d in domain_names]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(domain_names, mastery_levels, color='skyblue')
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{height:.2f}', ha='center', va='bottom')
        
        plt.title('Domain Mastery Levels')
        plt.xlabel('Knowledge Domains')
        plt.ylabel('Mastery Level (0-1)')
        plt.ylim(0, 1.1)  # Leave room for labels
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file)
            plt.close()
            return True
        else:
            return plt

# Create singleton instance
domain_tracker = DomainTracker()
