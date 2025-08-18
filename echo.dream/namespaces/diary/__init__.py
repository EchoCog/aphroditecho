
"""
Diary Namespace
Manages DTE's self-reporting, personal diary, and memory cultivation.
"""
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DiaryNamespace:
    """Handles self-reporting and memory management for DTE."""
    
    def __init__(self):
        self.namespace_path = os.path.dirname(os.path.abspath(__file__))
        self.entries = []
        self.reflections = []
        self.insights = []
        self.load_diary()
    
    def load_diary(self):
        """Load existing diary entries."""
        diary_file = os.path.join(self.namespace_path, 'diary_entries.json')
        if os.path.exists(diary_file):
            try:
                with open(diary_file, 'r') as f:
                    self.entries = json.load(f)
            except Exception as e:
                logger.error(f"Error loading diary entries: {e}")
                self.entries = []
        
        reflection_file = os.path.join(self.namespace_path, 'reflections.json')
        if os.path.exists(reflection_file):
            try:
                with open(reflection_file, 'r') as f:
                    self.reflections = json.load(f)
            except Exception as e:
                logger.error(f"Error loading reflections: {e}")
                self.reflections = []
    
    def create_entry(self, title, content, tags=None):
        """Create a new diary entry."""
        entry = {
            'id': len(self.entries) + 1,
            'title': title,
            'content': content,
            'tags': tags or [],
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat()
        }
        
        self.entries.append(entry)
        self._save_entries()
        return entry
    
    def add_reflection(self, diary_id, content):
        """Add a reflection on an existing diary entry."""
        entry_found = False
        for entry in self.entries:
            if entry['id'] == diary_id:
                entry_found = True
                break
                
        if not entry_found:
            return False
            
        reflection = {
            'id': len(self.reflections) + 1,
            'diary_id': diary_id,
            'content': content,
            'created': datetime.now().isoformat()
        }
        
        self.reflections.append(reflection)
        self._save_reflections()
        return reflection
    
    def generate_insight(self, related_entries=None):
        """Generate an insight based on diary entries and reflections."""
        if related_entries is None:
            # Use the last 5 entries by default
            related_entries = [e['id'] for e in self.entries[-5:]] if len(self.entries) >= 5 else [e['id'] for e in self.entries]
            
        # Simple insight generation (would be more sophisticated in practice)
        relevant_reflections = [r for r in self.reflections if r['diary_id'] in related_entries]
        
        if not relevant_reflections:
            return None
            
        insight_content = f"Based on {len(related_entries)} journal entries and {len(relevant_reflections)} reflections, an emerging pattern is observed."
        
        insight = {
            'id': len(self.insights) + 1,
            'content': insight_content,
            'related_entries': related_entries,
            'created': datetime.now().isoformat()
        }
        
        self.insights.append(insight)
        self._save_insights()
        return insight
    
    def search_entries(self, query):
        """Search diary entries for specific content."""
        results = []
        query = query.lower()
        
        for entry in self.entries:
            if (query in entry['title'].lower() or 
                query in entry['content'].lower() or 
                any(query in tag.lower() for tag in entry['tags'])):
                results.append(entry)
                
        return results
    
    def _save_entries(self):
        """Save diary entries to disk."""
        diary_file = os.path.join(self.namespace_path, 'diary_entries.json')
        try:
            with open(diary_file, 'w') as f:
                json.dump(self.entries, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving diary entries: {e}")
    
    def _save_reflections(self):
        """Save reflections to disk."""
        reflection_file = os.path.join(self.namespace_path, 'reflections.json')
        try:
            with open(reflection_file, 'w') as f:
                json.dump(self.reflections, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving reflections: {e}")
    
    def _save_insights(self):
        """Save insights to disk."""
        insight_file = os.path.join(self.namespace_path, 'insights.json')
        try:
            with open(insight_file, 'w') as f:
                json.dump(self.insights, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving insights: {e}")

# Create singleton instance
diary_namespace = DiaryNamespace()
