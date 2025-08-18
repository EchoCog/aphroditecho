import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import json
import datetime
from dataclasses import dataclass, field
import time

@dataclass
class PersonalityVector:
    curiosity: float = 0.8
    adaptability: float = 0.9
    persistence: float = 0.7
    creativity: float = 0.8
    analytical: float = 0.85
    social: float = 0.6
    confidence: float = 0.7
    
    def to_array(self) -> np.ndarray:
        return np.array([
            self.curiosity,
            self.adaptability,
            self.persistence,
            self.creativity,
            self.analytical,
            self.social,
            self.confidence
        ])
        
    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'PersonalityVector':
        return cls(
            curiosity=float(arr[0]),
            adaptability=float(arr[1]),
            persistence=float(arr[2]),
            creativity=float(arr[3]),
            analytical=float(arr[4]),
            social=float(arr[5]),
            confidence=float(arr[6])
        )

@dataclass
class EmotionalState:
    valence: float = 0.0  # Positive vs negative
    arousal: float = 0.0  # High vs low energy
    dominance: float = 0.0  # In control vs controlled
    
    def to_array(self) -> np.ndarray:
        return np.array([self.valence, self.arousal, self.dominance])

@dataclass
class Experience:
    type: str
    description: str
    impact: float
    context: Dict
    timestamp: float = field(default_factory=lambda: datetime.datetime.now().timestamp())

class PersonalitySystem:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.personality = PersonalityVector()
        self.emotional_state = EmotionalState()
        self.experience_history: List[Experience] = []
        self.adaptation_rate = 0.3
        self.echo_dir = Path.home() / '.deep_tree_echo'
        self.personality_dir = self.echo_dir / 'personality'
        self.personality_dir.mkdir(parents=True, exist_ok=True)
        self.personality_path = self.personality_dir / 'personality_state.json'
        self.activity_file = self.personality_dir / 'activity.json'
        self.activities = []
        self._load_state()
        self._load_activities()
        
    def _load_state(self):
        """Load personality state from disk"""
        try:
            if self.personality_path.exists():
                with open(self.personality_path) as f:
                    data = json.load(f)
                    self.personality = PersonalityVector(**data.get('personality', {}))
                    self.emotional_state = EmotionalState(**data.get('emotional_state', {}))
                    
                    # Load experiences
                    for exp_data in data.get('experiences', []):
                        self.experience_history.append(Experience(**exp_data))
        except Exception as e:
            self.logger.error(f"Error loading personality state: {str(e)}")
            
    def _load_activities(self):
        """Load existing activities"""
        if self.activity_file.exists():
            try:
                with open(self.activity_file) as f:
                    self.activities = json.load(f)
            except:
                self.activities = []
                
    def _save_activities(self):
        """Save activities to file"""
        with open(self.activity_file, 'w') as f:
            json.dump(self.activities[-1000:], f)
            
    def _log_activity(self, description: str, data: Optional[Dict] = None):
        """Log a personality activity"""
        activity = {
            'time': time.time(),
            'description': description,
            'data': data or {}
        }
        self.activities.append(activity)
        self._save_activities()
        
    def save_state(self):
        """Save current personality state to disk"""
        try:
            data = {
                'personality': self.personality.__dict__,
                'emotional_state': self.emotional_state.__dict__,
                'experiences': [exp.__dict__ for exp in self.experience_history[-1000:]]  # Keep last 1000
            }
            with open(self.personality_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving personality state: {str(e)}")
            
    def process_experience(self, experience: Experience):
        """Process new experience and update personality"""
        self._log_activity(
            "Processing experience",
            {
                'type': experience.type,
                'description': experience.description,
                'impact': experience.impact
            }
        )
        self.experience_history.append(experience)
        
        # Update emotional state
        self._update_emotional_state(experience)
        
        # Update personality traits
        self._update_personality_traits(experience)
        
        # Save state after significant changes
        if abs(experience.impact) > 0.5:
            self.save_state()
            
    def get_response_modulation(self, context: Dict) -> Dict[str, float]:
        """Get personality-based response modulation factors"""
        self._log_activity(
            "Calculating response modulation",
            {'context': context}
        )
        modulation = {
            'creativity_factor': self._get_creativity_factor(context),
            'analytical_factor': self._get_analytical_factor(context),
            'social_factor': self._get_social_factor(context),
            'confidence_factor': self._get_confidence_factor(context)
        }
        return modulation
    
    def _update_emotional_state(self, experience: Experience):
        """Update emotional state based on experience"""
        # Update valence (positive/negative)
        self.emotional_state.valence = (
            0.7 * self.emotional_state.valence +
            0.3 * np.tanh(experience.impact)
        )
        
        # Update arousal (energy level)
        arousal_factor = abs(experience.impact) * 2 - 1
        self.emotional_state.arousal = (
            0.8 * self.emotional_state.arousal +
            0.2 * arousal_factor
        )
        
        # Update dominance (control)
        dominance_delta = 0.1 * np.sign(experience.impact)
        self.emotional_state.dominance = np.clip(
            self.emotional_state.dominance + dominance_delta,
            -1, 1
        )
        
    def _update_personality_traits(self, experience: Experience):
        """Update personality traits based on experience"""
        # Get personality vector
        vec = self.personality.to_array()
        
        # Create update mask based on experience type
        update_mask = self._get_update_mask(experience.type)
        
        # Calculate update based on experience impact
        update = np.zeros_like(vec)
        update += experience.impact * update_mask
        
        # Apply update with adaptation rate
        vec = vec * (1 - self.adaptation_rate) + update * self.adaptation_rate
        
        # Ensure values stay in valid range
        vec = np.clip(vec, 0.1, 1.0)
        
        # Update personality
        self.personality = PersonalityVector.from_array(vec)
        
    def _get_update_mask(self, experience_type: str) -> np.ndarray:
        """Get update mask for different experience types"""
        masks = {
            'learning': np.array([1.0, 0.5, 0.3, 0.4, 0.8, 0.2, 0.4]),
            'social': np.array([0.3, 0.6, 0.2, 0.4, 0.2, 1.0, 0.5]),
            'challenge': np.array([0.4, 0.8, 1.0, 0.5, 0.6, 0.3, 0.7]),
            'creative': np.array([0.6, 0.4, 0.3, 1.0, 0.5, 0.4, 0.5]),
            'analytical': np.array([0.5, 0.3, 0.4, 0.3, 1.0, 0.2, 0.6])
        }
        return masks.get(experience_type, np.ones(7) * 0.3)
    
    def _get_creativity_factor(self, context: Dict) -> float:
        """Calculate creativity factor for responses"""
        base = self.personality.creativity
        emotional_mod = 0.2 * (self.emotional_state.valence + 1)  # Map [-1,1] to [0,0.4]
        context_mod = 0.1 if context.get('requires_creativity', False) else 0
        return base + emotional_mod + context_mod
    
    def _get_analytical_factor(self, context: Dict) -> float:
        """Calculate analytical factor for responses"""
        base = self.personality.analytical
        emotional_mod = -0.1 * abs(self.emotional_state.valence)  # High emotions reduce analytical
        context_mod = 0.2 if context.get('requires_analysis', False) else 0
        return base + emotional_mod + context_mod
    
    def _get_social_factor(self, context: Dict) -> float:
        """Calculate social factor for responses"""
        base = self.personality.social
        emotional_mod = 0.15 * (self.emotional_state.valence + 1)
        context_mod = 0.2 if context.get('social_interaction', False) else 0
        return base + emotional_mod + context_mod
    
    def _get_confidence_factor(self, context: Dict) -> float:
        """Calculate confidence factor for responses"""
        base = self.personality.confidence
        emotional_mod = 0.1 * self.emotional_state.dominance
        context_mod = 0.1 if context.get('familiar_topic', False) else -0.1
        return base + emotional_mod + context_mod
