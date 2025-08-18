"""
Emotional Dynamics module for Deep Tree Echo.

This module integrates the Julia EmotionalMemory framework with Python using PyJulia.
It provides a wrapper for the differential equation-based emotional model from 
EmotionalMemory.md to incorporate emotional states into Deep Tree Echo's processing.
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto

# Julia integration
try:
    from julia import Julia
    from julia import Main as jl
    jl_installed = True
except ImportError:
    jl_installed = False
    logging.warning("Julia or PyJulia not installed. Falling back to Python implementation.")

# Define core emotions matching the Julia implementation
class CoreEmotion(Enum):
    """Core emotions based on Panksepp's affective neuroscience"""
    SEEKING = 0
    RAGE = 1
    FEAR = 2
    LUST = 3
    CARE = 4
    PANIC_GRIEF = 5
    PLAY = 6

@dataclass
class EmotionalState:
    """Represents an emotional state with intensities for core emotions"""
    core_emotions: np.ndarray = field(default_factory=lambda: np.array([0.1] * 7))
    stability: float = 0.5
    decay_rate: float = 0.3
    coupling_matrix: np.ndarray = None
    
    def __post_init__(self):
        if self.coupling_matrix is None:
            # Default coupling matrix - how emotions affect each other
            self.coupling_matrix = np.array([
                # SEEKING RAGE   FEAR   LUST   CARE   PANIC  PLAY
                [  0.1,  -0.2,  -0.1,   0.2,   0.1,  -0.2,   0.3],  # SEEKING affects others
                [ -0.2,   0.1,  -0.3,  -0.2,  -0.3,   0.1,  -0.2],  # RAGE affects others
                [ -0.3,  -0.1,   0.1,  -0.2,  -0.1,   0.3,  -0.3],  # FEAR affects others
                [  0.2,  -0.2,  -0.2,   0.1,   0.3,  -0.1,   0.2],  # LUST affects others
                [  0.3,  -0.3,  -0.2,   0.2,   0.1,  -0.3,   0.3],  # CARE affects others
                [ -0.3,   0.2,   0.3,  -0.2,  -0.1,   0.1,  -0.2],  # PANIC_GRIEF affects others
                [  0.3,  -0.2,  -0.3,   0.2,   0.2,  -0.2,   0.1],  # PLAY affects others
            ])

class EmotionalDynamics:
    """
    Handles emotional dynamics for Deep Tree Echo using the Julia differential equations
    framework or a Python fallback implementation.
    """
    
    def __init__(self, use_julia: bool = True):
        """
        Initialize the EmotionalDynamics system.
        
        Args:
            use_julia: Whether to use Julia for emotional simulations (if available)
        """
        self.logger = logging.getLogger(__name__)
        self.use_julia = use_julia and jl_installed
        
        if self.use_julia:
            self._setup_julia()
        
        # Dictionary mapping compound emotion pairs to names
        self.compound_emotions = self._generate_compound_emotions()
        
    def _setup_julia(self):
        """Set up Julia environment and load EmotionalMemory module"""
        try:
            # Load the EmotionalMemory module code from the .md file
            with open("EmotionalMemory.md", "r") as f:
                emotional_memory_code = f.read()
            
            # Execute the Julia code
            jl.eval(emotional_memory_code)
            
            # Access the module
            self.em = jl.EmotionalMemory
            self.logger.info("Successfully loaded Julia EmotionalMemory module")
        except Exception as e:
            self.logger.error(f"Failed to set up Julia environment: {e}")
            self.use_julia = False
    
    def _generate_compound_emotions(self) -> Dict[Tuple[CoreEmotion, CoreEmotion], str]:
        """Generate dictionary of compound emotions"""
        compound_emotions = {}
        
        # Define compound emotions (simplified examples)
        compound_emotions[(CoreEmotion.SEEKING, CoreEmotion.RAGE)] = "Frustration"
        compound_emotions[(CoreEmotion.SEEKING, CoreEmotion.FEAR)] = "Anxiety"
        compound_emotions[(CoreEmotion.SEEKING, CoreEmotion.LUST)] = "Desire"
        compound_emotions[(CoreEmotion.SEEKING, CoreEmotion.CARE)] = "Compassionate Curiosity"
        compound_emotions[(CoreEmotion.SEEKING, CoreEmotion.PANIC_GRIEF)] = "Desperate Searching"
        compound_emotions[(CoreEmotion.SEEKING, CoreEmotion.PLAY)] = "Enthusiastic Exploration"
        
        compound_emotions[(CoreEmotion.RAGE, CoreEmotion.SEEKING)] = "Determined Anger"
        compound_emotions[(CoreEmotion.RAGE, CoreEmotion.FEAR)] = "Defensive Rage"
        compound_emotions[(CoreEmotion.RAGE, CoreEmotion.LUST)] = "Jealousy"
        compound_emotions[(CoreEmotion.RAGE, CoreEmotion.CARE)] = "Protective Anger"
        compound_emotions[(CoreEmotion.RAGE, CoreEmotion.PANIC_GRIEF)] = "Bitter Resentment"
        compound_emotions[(CoreEmotion.RAGE, CoreEmotion.PLAY)] = "Competitive Aggression"
        
        compound_emotions[(CoreEmotion.FEAR, CoreEmotion.SEEKING)] = "Cautious Investigation"
        compound_emotions[(CoreEmotion.FEAR, CoreEmotion.RAGE)] = "Terrified Aggression"
        compound_emotions[(CoreEmotion.FEAR, CoreEmotion.LUST)] = "Sexual Anxiety"
        compound_emotions[(CoreEmotion.FEAR, CoreEmotion.CARE)] = "Worried Concern"
        compound_emotions[(CoreEmotion.FEAR, CoreEmotion.PANIC_GRIEF)] = "Despair"
        compound_emotions[(CoreEmotion.FEAR, CoreEmotion.PLAY)] = "Timid Play"
        
        compound_emotions[(CoreEmotion.LUST, CoreEmotion.SEEKING)] = "Passionate Pursuit"
        compound_emotions[(CoreEmotion.LUST, CoreEmotion.RAGE)] = "Possessive Desire"
        compound_emotions[(CoreEmotion.LUST, CoreEmotion.FEAR)] = "Insecure Attraction"
        compound_emotions[(CoreEmotion.LUST, CoreEmotion.CARE)] = "Romantic Affection"
        compound_emotions[(CoreEmotion.LUST, CoreEmotion.PANIC_GRIEF)] = "Lovesickness"
        compound_emotions[(CoreEmotion.LUST, CoreEmotion.PLAY)] = "Flirtation"
        
        compound_emotions[(CoreEmotion.CARE, CoreEmotion.SEEKING)] = "Nurturing Guidance"
        compound_emotions[(CoreEmotion.CARE, CoreEmotion.RAGE)] = "Fierce Protection"
        compound_emotions[(CoreEmotion.CARE, CoreEmotion.FEAR)] = "Anxious Attachment"
        compound_emotions[(CoreEmotion.CARE, CoreEmotion.LUST)] = "Intimate Bonding"
        compound_emotions[(CoreEmotion.CARE, CoreEmotion.PANIC_GRIEF)] = "Empathetic Sorrow"
        compound_emotions[(CoreEmotion.CARE, CoreEmotion.PLAY)] = "Playful Nurturing"
        
        compound_emotions[(CoreEmotion.PANIC_GRIEF, CoreEmotion.SEEKING)] = "Yearning"
        compound_emotions[(CoreEmotion.PANIC_GRIEF, CoreEmotion.RAGE)] = "Agitated Distress"
        compound_emotions[(CoreEmotion.PANIC_GRIEF, CoreEmotion.FEAR)] = "Traumatic Grief"
        compound_emotions[(CoreEmotion.PANIC_GRIEF, CoreEmotion.LUST)] = "Longing"
        compound_emotions[(CoreEmotion.PANIC_GRIEF, CoreEmotion.CARE)] = "Separation Anxiety"
        compound_emotions[(CoreEmotion.PANIC_GRIEF, CoreEmotion.PLAY)] = "Bitter Humor"
        
        compound_emotions[(CoreEmotion.PLAY, CoreEmotion.SEEKING)] = "Creative Exploration"
        compound_emotions[(CoreEmotion.PLAY, CoreEmotion.RAGE)] = "Rough Play"
        compound_emotions[(CoreEmotion.PLAY, CoreEmotion.FEAR)] = "Thrilling Adventure"
        compound_emotions[(CoreEmotion.PLAY, CoreEmotion.LUST)] = "Erotic Play"
        compound_emotions[(CoreEmotion.PLAY, CoreEmotion.CARE)] = "Nurturing Play"
        compound_emotions[(CoreEmotion.PLAY, CoreEmotion.PANIC_GRIEF)] = "Consoling Play"
        
        return compound_emotions
    
    def simulate_emotional_dynamics(self, 
                                   initial_state: np.ndarray, 
                                   emotional_state: EmotionalState,
                                   time_span: Tuple[float, float]) -> np.ndarray:
        """
        Simulate emotional dynamics over time
        
        Args:
            initial_state: Initial core emotion intensity values
            emotional_state: EmotionalState configuration
            time_span: Time range for simulation (start_time, end_time)
            
        Returns:
            Final emotional state after simulation
        """
        if self.use_julia:
            try:
                # Call Julia simulation
                es = self.em.EmotionalState(
                    emotional_state.core_emotions.tolist(),
                    emotional_state.stability,
                    emotional_state.decay_rate,
                    emotional_state.coupling_matrix.tolist()
                )
                solution = self.em.simulate_emotions(
                    initial_state.tolist(),
                    es,
                    time_span
                )
                # Extract the final state
                return np.array(solution.u[-1])
            except Exception as e:
                self.logger.error(f"Julia simulation failed: {e}. Falling back to Python.")
                return self._simulate_python_fallback(initial_state, emotional_state, time_span)
        else:
            return self._simulate_python_fallback(initial_state, emotional_state, time_span)
    
    def _simulate_python_fallback(self, 
                                 initial_state: np.ndarray, 
                                 emotional_state: EmotionalState,
                                 time_span: Tuple[float, float]) -> np.ndarray:
        """Python fallback implementation for emotional dynamics simulation"""
        # Simple Euler integration of differential equations
        current_state = initial_state.copy()
        t_start, t_end = time_span
        dt = 0.1  # Time step
        
        stability = emotional_state.stability
        decay_rate = emotional_state.decay_rate
        coupling = emotional_state.coupling_matrix
        baseline = emotional_state.core_emotions
        
        t = t_start
        while t < t_end:
            # Calculate derivatives
            derivatives = np.zeros(7)
            for i in range(7):
                # Natural decay term
                decay = -decay_rate * current_state[i]
                
                # Stability term - pulls toward baseline emotional state
                pull_to_baseline = stability * (baseline[i] - current_state[i])
                
                # Coupling term - how other emotions affect this one
                coupling_effect = sum(coupling[j, i] * current_state[j] for j in range(7))
                
                # Combine effects
                derivatives[i] = decay + pull_to_baseline + coupling_effect
            
            # Update state
            current_state += derivatives * dt
            
            # Ensure values stay in [0, 1]
            current_state = np.clip(current_state, 0.0, 1.0)
            
            t += dt
        
        return current_state
    
    def dominant_emotions(self, state: np.ndarray, threshold: float = 0.2) -> List[CoreEmotion]:
        """
        Calculate the dominant emotions from a state vector
        
        Args:
            state: Emotion intensity vector
            threshold: Minimum intensity to be considered active
            
        Returns:
            List of dominant emotions
        """
        # Find emotions above threshold
        active_indices = [i for i, e in enumerate(state) if e > threshold]
        
        # Sort by intensity
        active_indices.sort(key=lambda i: state[i], reverse=True)
        
        # Return as CoreEmotion enum values
        return [CoreEmotion(i) for i in active_indices]
    
    def identify_compound_emotion(self, state: np.ndarray) -> str:
        """
        Identify compound emotion from current state
        
        Args:
            state: Emotion intensity vector
            
        Returns:
            Name of identified compound emotion
        """
        # Get top two emotions
        dom_emotions = self.dominant_emotions(state)
        
        if len(dom_emotions) >= 2:
            emotion_pair = (dom_emotions[0], dom_emotions[1])
            
            # Check if this compound exists in our dictionary
            if emotion_pair in self.compound_emotions:
                return self.compound_emotions[emotion_pair]
        
        # If no compound emotion is found, return the dominant single emotion
        if dom_emotions:
            return dom_emotions[0].name
        else:
            return "Neutral"
    
    def emotion_to_echo_modifier(self, state: np.ndarray) -> float:
        """
        Convert emotional state to echo value modifier
        
        Args:
            state: Emotion intensity vector
            
        Returns:
            Echo value modifier in range [-0.3, 0.3]
        """
        # Get dominant emotions and their values
        emotions = self.dominant_emotions(state)
        
        if not emotions:
            return 0.0
        
        # Different emotions affect echo values differently
        modifiers = {
            CoreEmotion.SEEKING: 0.3,    # Seeking increases echo (exploration)
            CoreEmotion.RAGE: -0.1,      # Rage slightly decreases echo
            CoreEmotion.FEAR: -0.3,      # Fear significantly decreases echo
            CoreEmotion.LUST: 0.1,       # Lust slightly increases echo
            CoreEmotion.CARE: 0.2,       # Care increases echo (connection)
            CoreEmotion.PANIC_GRIEF: -0.2,  # Panic decreases echo
            CoreEmotion.PLAY: 0.3,       # Play significantly increases echo
        }
        
        # Weight by the most dominant emotion
        dominant = emotions[0]
        intensity = state[dominant.value]
        modifier = modifiers[dominant] * intensity
        
        # If we have a secondary emotion, let it influence slightly
        if len(emotions) > 1:
            secondary = emotions[1]
            sec_intensity = state[secondary.value] * 0.5  # Half effect
            modifier += modifiers[secondary] * sec_intensity
            
            # Normalize to range
            modifier = max(-0.3, min(0.3, modifier))
        
        return modifier
    
    def content_to_emotion(self, content: str) -> np.ndarray:
        """
        Extract emotional state from text content
        
        Args:
            content: Text to analyze
            
        Returns:
            Emotion intensity vector
        """
        # This is a simplified implementation
        # In a real system, you'd use sentiment analysis, NLP, etc.
        
        # Define emotion-related keywords
        emotion_keywords = {
            CoreEmotion.SEEKING: ["search", "explore", "discover", "learn", "curious"],
            CoreEmotion.RAGE: ["angry", "rage", "furious", "hate", "destroy"],
            CoreEmotion.FEAR: ["fear", "afraid", "scary", "terror", "dread"],
            CoreEmotion.LUST: ["desire", "want", "crave", "attraction", "passion"],
            CoreEmotion.CARE: ["care", "love", "protect", "nurture", "help"],
            CoreEmotion.PANIC_GRIEF: ["panic", "grief", "loss", "sad", "distress"],
            CoreEmotion.PLAY: ["play", "fun", "joy", "delight", "game"]
        }
        
        # Count keyword occurrences
        content_lower = content.lower()
        counts = np.zeros(7)
        
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                counts[emotion.value] += content_lower.count(keyword)
        
        # Normalize
        total = np.sum(counts)
        if total > 0:
            intensities = counts / (total * 2)  # Divide by total*2 to keep values reasonable
            return np.clip(intensities, 0.1, 1.0)  # Min 0.1 to ensure all emotions present
        else:
            return np.array([0.1] * 7)  # Default mild emotional state