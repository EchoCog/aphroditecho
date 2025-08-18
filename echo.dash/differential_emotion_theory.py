"""
Differential Emotion Theory integration for Deep Tree Echo

This module extends the emotional_dynamics.py module by implementing
Izard's Differential Emotion Theory with the Julia framework.
It provides mechanisms for:
1. Discrete emotion intensity tracking
2. Emotion transition matrices
3. Emotional scripts and schemas
4. Cognitive-emotion interactions
5. Emotional regulation modeling
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from collections import deque
from emotional_dynamics import EmotionalDynamics, EmotionalState, CoreEmotion

# Julia integration
try:
    from julia import Julia
    from julia import Main as jl
    jl_installed = True
except ImportError:
    jl_installed = False
    logging.warning("Julia or PyJulia not installed. Falling back to Python implementation.")

# Define DET (Differential Emotion Theory) emotion categories
class DETEmotion(IntEnum):
    """
    Emotions based on Izard's Differential Emotion Theory.
    
    These emotions represent a more fine-grained set than Panksepp's core emotions
    and are mapped to the core emotions for compatibility.
    """
    # Mapped to SEEKING
    INTEREST = 0
    EXCITEMENT = 1
    
    # Mapped to RAGE
    ANGER = 2
    CONTEMPT = 3
    DISGUST = 4
    
    # Mapped to FEAR
    FEAR = 5
    SHAME = 6
    SHYNESS = 7
    GUILT = 8
    
    # Mapped to LUST
    DESIRE = 9
    
    # Mapped to CARE
    LOVE = 10
    TENDERNESS = 11
    
    # Mapped to PANIC_GRIEF
    DISTRESS = 12
    SADNESS = 13
    
    # Mapped to PLAY
    JOY = 14
    AMUSEMENT = 15
    SURPRISE = 16

@dataclass
class EmotionalScript:
    """
    Represents an emotional script as defined in Differential Emotion Theory.
    
    Emotional scripts are sequences of emotions, cognitions, and behaviors that 
    are activated in response to specific situations.
    """
    name: str
    triggering_emotions: List[DETEmotion]
    cognitions: List[str]
    behavioral_responses: List[str]
    intensity_modifier: float = 1.0
    recency_weight: float = 0.0  # Recent scripts have higher activation potential
    
    def matches_emotions(self, emotions: List[DETEmotion], threshold: int = 1) -> bool:
        """Check if this script matches the current emotional state"""
        matches = set(self.triggering_emotions).intersection(set(emotions))
        return len(matches) >= threshold

@dataclass
class DETState:
    """
    Represents a Differential Emotion Theory emotional state.
    
    This extends the basic emotional state with more fine-grained emotions,
    emotion transitions, and cognitive-emotion interactions.
    """
    # Fine-grained DET emotion intensities (0.0-1.0)
    det_emotions: np.ndarray = field(default_factory=lambda: np.array([0.1] * 17))
    
    # Transition matrix showing how likely one emotion transitions to another
    transition_matrix: np.ndarray = None
    
    # Cognitive appraisal factors (valence, arousal, control, etc.)
    cognitive_factors: Dict[str, float] = field(default_factory=dict)
    
    # Active emotional scripts
    active_scripts: List[EmotionalScript] = field(default_factory=list)
    
    # Emotion regulation capabilities (0.0-1.0)
    regulation_capacity: float = 0.5
    
    # Script activation history (recent first)
    script_history: deque = field(default_factory=lambda: deque(maxlen=10))
    
    def __post_init__(self):
        if self.transition_matrix is None:
            # Initialize default transition matrix
            # Higher values mean more likely transitions between emotions
            self.transition_matrix = np.zeros((17, 17))
            
            # Set default transitions (simplified)
            # Interest -> Excitement
            self.transition_matrix[DETEmotion.INTEREST, DETEmotion.EXCITEMENT] = 0.7
            
            # Anger -> Disgust/Contempt
            self.transition_matrix[DETEmotion.ANGER, DETEmotion.DISGUST] = 0.5
            self.transition_matrix[DETEmotion.ANGER, DETEmotion.CONTEMPT] = 0.5
            
            # Fear -> Shame/Guilt
            self.transition_matrix[DETEmotion.FEAR, DETEmotion.SHAME] = 0.4
            self.transition_matrix[DETEmotion.FEAR, DETEmotion.GUILT] = 0.4
            
            # Distress -> Sadness
            self.transition_matrix[DETEmotion.DISTRESS, DETEmotion.SADNESS] = 0.8
            
            # Joy -> Amusement
            self.transition_matrix[DETEmotion.JOY, DETEmotion.AMUSEMENT] = 0.7
            
            # Add more transitions based on psychological research
            
        if not self.cognitive_factors:
            # Default cognitive factors
            self.cognitive_factors = {
                "valence": 0.0,      # -1.0 to 1.0 (negative to positive)
                "arousal": 0.5,      # 0.0 to 1.0 (calm to excited)
                "control": 0.5,      # 0.0 to 1.0 (no control to full control)
                "certainty": 0.5,    # 0.0 to 1.0 (uncertain to certain)
                "effort": 0.5,       # 0.0 to 1.0 (effortless to effortful)
                "attention": 0.5,    # 0.0 to 1.0 (minimal to full attention)
            }


class DifferentialEmotionSystem:
    """
    Implementation of Differential Emotion Theory for Deep Tree Echo.
    
    This system extends the basic emotional dynamics with more fine-grained
    emotions, emotional scripts, cognitive-emotion interactions, and regulation.
    """
    
    def __init__(self, use_julia: bool = True):
        """
        Initialize the Differential Emotion Theory system.
        
        Args:
            use_julia: Whether to use Julia for emotional simulations (if available)
        """
        self.logger = logging.getLogger(__name__)
        self.use_julia = use_julia and jl_installed
        
        # Base emotional dynamics system
        self.base_dynamics = EmotionalDynamics(use_julia=use_julia)
        
        # Library of emotional scripts
        self.script_library = self._create_script_library()
        
        # Load Julia extensions if available
        if self.use_julia:
            self._setup_julia_extensions()
    
    def _setup_julia_extensions(self):
        """Set up additional Julia functionality for DET"""
        try:
            # Define Julia functions for differential emotion theory
            julia_code = """
            module DifferentialEmotion
            
            using DifferentialEquations
            using LinearAlgebra
            using Distributions
            
            # Cognitive appraisal simulation
            function simulate_appraisal(emotions::Vector{Float64}, 
                                       cognitive_factors::Dict{String, Float64}, 
                                       time_span::Tuple{Float64, Float64})
                # Create a system of ODEs for cognitive-emotion interactions
                function appraisal_dynamics!(du, u, p, t)
                    emotions, cog_factors = p
                    
                    # Emotion components (first 17 elements of u)
                    e = @view u[1:17]
                    
                    # Cognitive factors (remaining elements)
                    cog = @view u[18:end]
                    
                    # Emotion dynamics
                    for i in 1:17
                        # Natural decay
                        decay = -0.2 * e[i]
                        
                        # Cognitive influence on emotion
                        cognitive_influence = 0.0
                        
                        # Valence affects emotional intensity differently
                        if i in [1, 2, 9, 10, 11, 14, 15, 16]  # Positive emotions
                            cognitive_influence += 0.3 * cog[1]  # Valence boosts positive emotions
                        else  # Negative emotions
                            cognitive_influence += -0.3 * cog[1]  # Valence reduces negative emotions
                        end
                        
                        # Arousal amplifies all emotions
                        cognitive_influence += 0.2 * cog[2] * e[i]
                        
                        # Higher control reduces fear, shame, guilt
                        if i in [5, 6, 7, 8]
                            cognitive_influence += -0.3 * cog[3]
                        end
                        
                        # Apply emotional regulation
                        regulation = -0.2 * e[i] * cog[6]  # Attention as regulation
                        
                        # Combine effects
                        du[i] = decay + cognitive_influence + regulation
                    end
                    
                    # Cognitive dynamics
                    # Valence
                    du[18] = 0.1 * (sum(e[i] for i in [1, 2, 9, 10, 11, 14, 15, 16]) - 
                                    sum(e[i] for i in [3, 4, 5, 6, 7, 8, 12, 13])) - 0.1 * cog[1]
                    
                    # Arousal
                    du[19] = 0.2 * (sum(e[i] for i in [1, 2, 3, 5, 9, 14, 16]) - 
                                   sum(e[i] for i in [7, 13])) - 0.1 * cog[2]
                                   
                    # Control
                    du[20] = 0.1 * (sum(e[i] for i in [1, 3, 4]) - 
                                   sum(e[i] for i in [5, 6, 7, 8, 12, 13])) - 0.1 * cog[3]
                    
                    # Certainty
                    du[21] = -0.3 * e[16] - 0.2 * e[5] - 0.1 * cog[4]
                    
                    # Effort
                    du[22] = 0.2 * (e[1] + e[2]) + 0.1 * e[3] - 0.1 * cog[5]
                    
                    # Attention
                    du[23] = 0.2 * (e[1] + e[16]) - 0.1 * cog[6]
                end
                
                # Create initial state (emotions + cognitive factors)
                initial_state = vcat(
                    emotions, 
                    [cognitive_factors["valence"], 
                     cognitive_factors["arousal"],
                     cognitive_factors["control"],
                     cognitive_factors["certainty"],
                     cognitive_factors["effort"],
                     cognitive_factors["attention"]]
                )
                
                # Set up parameters
                params = (emotions, cognitive_factors)
                
                # Create ODE problem
                prob = ODEProblem(appraisal_dynamics!, initial_state, time_span, params)
                
                # Solve ODE
                sol = solve(prob, Tsit5(), reltol=1e-6, abstol=1e-6)
                
                # Return final state
                final_state = sol.u[end]
                
                # Split into emotions and cognitive factors
                final_emotions = final_state[1:17]
                final_cognitive = Dict(
                    "valence" => final_state[18],
                    "arousal" => final_state[19],
                    "control" => final_state[20],
                    "certainty" => final_state[21],
                    "effort" => final_state[22],
                    "attention" => final_state[23]
                )
                
                return (final_emotions, final_cognitive)
            end
            
            # Simulate emotion regulation
            function simulate_regulation(emotions::Vector{Float64}, 
                                        regulation_capacity::Float64,
                                        regulation_target::Int,
                                        regulation_type::String,
                                        time_span::Tuple{Float64, Float64})
                # Different regulation strategies affect emotions differently
                function regulation_dynamics!(du, u, p, t)
                    reg_capacity, reg_target, reg_type = p
                    
                    for i in 1:length(u)
                        # Natural decay
                        decay = -0.1 * u[i]
                        
                        # Regulation effect
                        regulation = 0.0
                        
                        if reg_type == "suppression"
                            # Suppression reduces target emotion but increases others
                            if i == reg_target + 1
                                regulation = -0.3 * reg_capacity
                            else
                                regulation = 0.05 * reg_capacity
                            end
                        elseif reg_type == "reappraisal"
                            # Reappraisal reduces negative emotions and increases positive
                            if i in [3, 4, 5, 6, 7, 8, 12, 13]  # Negative emotions
                                regulation = -0.2 * reg_capacity
                            elseif i in [1, 2, 9, 10, 11, 14, 15]  # Positive emotions
                                regulation = 0.1 * reg_capacity
                            end
                        elseif reg_type == "distraction"
                            # Distraction reduces all emotions slightly
                            regulation = -0.1 * reg_capacity
                        end
                        
                        # Combine effects
                        du[i] = decay + regulation
                    end
                end
                
                # Create ODE problem
                params = (regulation_capacity, regulation_target, regulation_type)
                prob = ODEProblem(regulation_dynamics!, emotions, time_span, params)
                
                # Solve ODE
                sol = solve(prob, Tsit5(), reltol=1e-6, abstol=1e-6)
                
                # Return final state
                return sol.u[end]
            end
            
            # Extract emotional scripts based on emotion patterns
            function extract_scripts(emotions::Vector{Float64}, 
                                     scripts::Vector{Vector{Int}},
                                     script_thresholds::Vector{Float64})
                activated_scripts = Int[]
                
                for i in 1:length(scripts)
                    script = scripts[i]
                    threshold = script_thresholds[i]
                    
                    # Check if script emotions are active
                    active_emotions = sum(emotions[j] > 0.2 for j in script)
                    if active_emotions / length(script) >= threshold
                        push!(activated_scripts, i)
                    end
                end
                
                return activated_scripts
            end
            
            end # module
            """
            
            # Execute Julia code
            jl.eval(julia_code)
            
            # Access the module
            self.det_julia = jl.DifferentialEmotion
            self.logger.info("Successfully loaded Julia Differential Emotion extension")
            
        except Exception as e:
            self.logger.error(f"Failed to set up Julia extensions for DET: {e}")
            self.use_julia = False
    
    def _create_script_library(self) -> List[EmotionalScript]:
        """Create a library of emotional scripts based on Differential Emotion Theory"""
        scripts = []
        
        # Interest-Excitement script (Exploration)
        scripts.append(EmotionalScript(
            name="Exploration",
            triggering_emotions=[DETEmotion.INTEREST, DETEmotion.EXCITEMENT],
            cognitions=["This is novel", "I want to learn more", "This is fascinating"],
            behavioral_responses=["Approach", "Investigate", "Ask questions"]
        ))
        
        # Fear-Anxiety script (Escape)
        scripts.append(EmotionalScript(
            name="Escape",
            triggering_emotions=[DETEmotion.FEAR, DETEmotion.SHAME],
            cognitions=["This is dangerous", "I need to get away", "I'm not safe"],
            behavioral_responses=["Retreat", "Hide", "Freeze", "Seek safety"]
        ))
        
        # Anger-Rage script (Attack)
        scripts.append(EmotionalScript(
            name="Attack",
            triggering_emotions=[DETEmotion.ANGER, DETEmotion.CONTEMPT, DETEmotion.DISGUST],
            cognitions=["This is an obstacle", "This is unfair", "This threatens my goals"],
            behavioral_responses=["Confront", "Remove obstacle", "Express disapproval"]
        ))
        
        # Joy-Happiness script (Celebration)
        scripts.append(EmotionalScript(
            name="Celebration",
            triggering_emotions=[DETEmotion.JOY, DETEmotion.AMUSEMENT],
            cognitions=["This is good", "I succeeded", "Life is enjoyable"],
            behavioral_responses=["Smile", "Share", "Continue activity", "Express happiness"]
        ))
        
        # Sadness-Distress script (Withdrawal)
        scripts.append(EmotionalScript(
            name="Withdrawal",
            triggering_emotions=[DETEmotion.DISTRESS, DETEmotion.SADNESS],
            cognitions=["I've lost something valuable", "I'm helpless", "Things won't improve"],
            behavioral_responses=["Withdraw", "Seek comfort", "Reduce activity", "Reflect"]
        ))
        
        # Love-Tenderness script (Attachment)
        scripts.append(EmotionalScript(
            name="Attachment",
            triggering_emotions=[DETEmotion.LOVE, DETEmotion.TENDERNESS],
            cognitions=["I care about this", "This is precious", "I want to protect this"],
            behavioral_responses=["Nurture", "Protect", "Stay close", "Express affection"]
        ))
        
        # Surprise script (Orientation)
        scripts.append(EmotionalScript(
            name="Orientation",
            triggering_emotions=[DETEmotion.SURPRISE],
            cognitions=["This is unexpected", "What is this?", "I need to understand"],
            behavioral_responses=["Stop", "Orient", "Pay attention", "Reassess"]
        ))
        
        # Shame-Guilt script (Atonement)
        scripts.append(EmotionalScript(
            name="Atonement",
            triggering_emotions=[DETEmotion.SHAME, DETEmotion.GUILT],
            cognitions=["I did something wrong", "I am inadequate", "I need to make amends"],
            behavioral_responses=["Apologize", "Hide", "Repair damage", "Self-punishment"]
        ))
        
        return scripts
    
    def map_core_to_det(self, core_state: np.ndarray) -> np.ndarray:
        """
        Map from Panksepp's 7 core emotions to 17 DET emotions
        
        Args:
            core_state: 7-element array of core emotion intensities
            
        Returns:
            17-element array of DET emotion intensities
        """
        det_state = np.zeros(17)
        
        # SEEKING -> Interest, Excitement
        det_state[DETEmotion.INTEREST] = core_state[CoreEmotion.SEEKING.value] * 0.7
        det_state[DETEmotion.EXCITEMENT] = core_state[CoreEmotion.SEEKING.value] * 0.6
        
        # RAGE -> Anger, Contempt, Disgust
        det_state[DETEmotion.ANGER] = core_state[CoreEmotion.RAGE.value] * 0.8
        det_state[DETEmotion.CONTEMPT] = core_state[CoreEmotion.RAGE.value] * 0.5
        det_state[DETEmotion.DISGUST] = core_state[CoreEmotion.RAGE.value] * 0.6
        
        # FEAR -> Fear, Shame, Shyness, Guilt
        det_state[DETEmotion.FEAR] = core_state[CoreEmotion.FEAR.value] * 0.9
        det_state[DETEmotion.SHAME] = core_state[CoreEmotion.FEAR.value] * 0.4
        det_state[DETEmotion.SHYNESS] = core_state[CoreEmotion.FEAR.value] * 0.5
        det_state[DETEmotion.GUILT] = core_state[CoreEmotion.FEAR.value] * 0.3
        
        # LUST -> Desire
        det_state[DETEmotion.DESIRE] = core_state[CoreEmotion.LUST.value] * 0.9
        
        # CARE -> Love, Tenderness
        det_state[DETEmotion.LOVE] = core_state[CoreEmotion.CARE.value] * 0.8
        det_state[DETEmotion.TENDERNESS] = core_state[CoreEmotion.CARE.value] * 0.7
        
        # PANIC_GRIEF -> Distress, Sadness
        det_state[DETEmotion.DISTRESS] = core_state[CoreEmotion.PANIC_GRIEF.value] * 0.8
        det_state[DETEmotion.SADNESS] = core_state[CoreEmotion.PANIC_GRIEF.value] * 0.7
        
        # PLAY -> Joy, Amusement, Surprise
        det_state[DETEmotion.JOY] = core_state[CoreEmotion.PLAY.value] * 0.8
        det_state[DETEmotion.AMUSEMENT] = core_state[CoreEmotion.PLAY.value] * 0.7
        det_state[DETEmotion.SURPRISE] = core_state[CoreEmotion.PLAY.value] * 0.3
        
        return det_state
    
    def map_det_to_core(self, det_state: np.ndarray) -> np.ndarray:
        """
        Map from 17 DET emotions to Panksepp's 7 core emotions
        
        Args:
            det_state: 17-element array of DET emotion intensities
            
        Returns:
            7-element array of core emotion intensities
        """
        core_state = np.zeros(7)
        
        # Interest, Excitement -> SEEKING
        core_state[CoreEmotion.SEEKING.value] = (
            det_state[DETEmotion.INTEREST] * 0.6 + 
            det_state[DETEmotion.EXCITEMENT] * 0.4
        ) / 1.0
        
        # Anger, Contempt, Disgust -> RAGE
        core_state[CoreEmotion.RAGE.value] = (
            det_state[DETEmotion.ANGER] * 0.5 + 
            det_state[DETEmotion.CONTEMPT] * 0.3 + 
            det_state[DETEmotion.DISGUST] * 0.2
        ) / 1.0
        
        # Fear, Shame, Shyness, Guilt -> FEAR
        core_state[CoreEmotion.FEAR.value] = (
            det_state[DETEmotion.FEAR] * 0.7 + 
            det_state[DETEmotion.SHAME] * 0.1 + 
            det_state[DETEmotion.SHYNESS] * 0.1 + 
            det_state[DETEmotion.GUILT] * 0.1
        ) / 1.0
        
        # Desire -> LUST
        core_state[CoreEmotion.LUST.value] = det_state[DETEmotion.DESIRE]
        
        # Love, Tenderness -> CARE
        core_state[CoreEmotion.CARE.value] = (
            det_state[DETEmotion.LOVE] * 0.6 + 
            det_state[DETEmotion.TENDERNESS] * 0.4
        ) / 1.0
        
        # Distress, Sadness -> PANIC_GRIEF
        core_state[CoreEmotion.PANIC_GRIEF.value] = (
            det_state[DETEmotion.DISTRESS] * 0.5 + 
            det_state[DETEmotion.SADNESS] * 0.5
        ) / 1.0
        
        # Joy, Amusement, Surprise -> PLAY
        core_state[CoreEmotion.PLAY.value] = (
            det_state[DETEmotion.JOY] * 0.5 + 
            det_state[DETEmotion.AMUSEMENT] * 0.4 + 
            det_state[DETEmotion.SURPRISE] * 0.1
        ) / 1.0
        
        return core_state
    
    def create_det_state_from_core(self, core_state: np.ndarray) -> DETState:
        """
        Create a full DET state from core emotional state
        
        Args:
            core_state: 7-element array of core emotion intensities
            
        Returns:
            DETState object with all DET properties
        """
        # Map core emotions to DET emotions
        det_emotions = self.map_core_to_det(core_state)
        
        # Create default DET state
        return DETState(det_emotions=det_emotions)
    
    def simulate_appraisal(self, 
                          det_state: DETState, 
                          time_span: Tuple[float, float] = (0.0, 5.0)) -> DETState:
        """
        Simulate cognitive appraisal processes and their effects on emotions
        
        Args:
            det_state: Current DET emotional state
            time_span: Time range for simulation (start_time, end_time)
            
        Returns:
            Updated DET state after appraisal processes
        """
        if self.use_julia:
            try:
                # Convert Python dictionary to Julia dictionary for cognitive factors
                cognitive_dict = {k: float(v) for k, v in det_state.cognitive_factors.items()}
                
                # Call Julia simulation
                final_emotions, final_cognitive = self.det_julia.simulate_appraisal(
                    det_state.det_emotions.tolist(),
                    cognitive_dict,
                    time_span
                )
                
                # Update DET state
                result = DETState(
                    det_emotions=np.array(final_emotions),
                    transition_matrix=det_state.transition_matrix.copy(),
                    cognitive_factors={k: float(v) for k, v in final_cognitive.items()},
                    active_scripts=det_state.active_scripts.copy(),
                    regulation_capacity=det_state.regulation_capacity,
                    script_history=det_state.script_history.copy()
                )
                
                return result
                
            except Exception as e:
                self.logger.error(f"Julia appraisal simulation failed: {e}. Falling back to Python.")
                return self._simulate_appraisal_python(det_state, time_span)
        else:
            return self._simulate_appraisal_python(det_state, time_span)
    
    def _simulate_appraisal_python(self, 
                                 det_state: DETState, 
                                 time_span: Tuple[float, float]) -> DETState:
        """Python fallback implementation for cognitive appraisal simulation"""
        # Simple Euler integration of differential equations
        emotions = det_state.det_emotions.copy()
        cog_factors = det_state.cognitive_factors.copy()
        
        t_start, t_end = time_span
        dt = 0.1  # Time step
        
        t = t_start
        while t < t_end:
            # Calculate derivatives for emotions
            emotion_derivatives = np.zeros(17)
            
            for i in range(17):
                # Natural decay
                decay = -0.2 * emotions[i]
                
                # Cognitive influence on emotion
                cognitive_influence = 0.0
                
                # Valence affects emotional intensity differently
                if i in [0, 1, 9, 10, 11, 14, 15, 16]:  # Positive emotions
                    cognitive_influence += 0.3 * cog_factors["valence"]  # Valence boosts positive emotions
                else:  # Negative emotions
                    cognitive_influence += -0.3 * cog_factors["valence"]  # Valence reduces negative emotions
                
                # Arousal amplifies all emotions
                cognitive_influence += 0.2 * cog_factors["arousal"] * emotions[i]
                
                # Higher control reduces fear, shame, guilt
                if i in [5, 6, 7, 8]:
                    cognitive_influence += -0.3 * cog_factors["control"]
                
                # Apply emotional regulation
                regulation = -0.2 * emotions[i] * cog_factors["attention"]  # Attention as regulation
                
                # Combine effects
                emotion_derivatives[i] = decay + cognitive_influence + regulation
            
            # Calculate derivatives for cognitive factors
            cog_derivatives = {}
            
            # Valence
            pos_emotions = sum(emotions[i] for i in [0, 1, 9, 10, 11, 14, 15, 16])
            neg_emotions = sum(emotions[i] for i in [2, 3, 4, 5, 6, 7, 8, 12, 13])
            cog_derivatives["valence"] = 0.1 * (pos_emotions - neg_emotions) - 0.1 * cog_factors["valence"]
            
            # Arousal
            high_arousal = sum(emotions[i] for i in [1, 2, 5, 9, 14, 16])
            low_arousal = sum(emotions[i] for i in [7, 13])
            cog_derivatives["arousal"] = 0.2 * (high_arousal - low_arousal) - 0.1 * cog_factors["arousal"]
            
            # Control
            control_pos = sum(emotions[i] for i in [0, 2, 3])
            control_neg = sum(emotions[i] for i in [5, 6, 7, 8, 12, 13])
            cog_derivatives["control"] = 0.1 * (control_pos - control_neg) - 0.1 * cog_factors["control"]
            
            # Certainty
            cog_derivatives["certainty"] = -0.3 * emotions[16] - 0.2 * emotions[5] - 0.1 * cog_factors["certainty"]
            
            # Effort
            cog_derivatives["effort"] = 0.2 * (emotions[0] + emotions[1]) + 0.1 * emotions[2] - 0.1 * cog_factors["effort"]
            
            # Attention
            cog_derivatives["attention"] = 0.2 * (emotions[0] + emotions[16]) - 0.1 * cog_factors["attention"]
            
            # Update emotions
            emotions += emotion_derivatives * dt
            
            # Update cognitive factors
            for factor in cog_factors:
                cog_factors[factor] += cog_derivatives[factor] * dt
            
            # Ensure values stay in reasonable ranges
            emotions = np.clip(emotions, 0.0, 1.0)
            for factor in cog_factors:
                if factor == "valence":
                    cog_factors[factor] = max(-1.0, min(1.0, cog_factors[factor]))
                else:
                    cog_factors[factor] = max(0.0, min(1.0, cog_factors[factor]))
            
            t += dt
        
        # Create new DET state with updated values
        result = DETState(
            det_emotions=emotions,
            transition_matrix=det_state.transition_matrix.copy(),
            cognitive_factors=cog_factors,
            active_scripts=det_state.active_scripts.copy(),
            regulation_capacity=det_state.regulation_capacity,
            script_history=det_state.script_history.copy()
        )
        
        return result
    
    def regulate_emotion(self, 
                        det_state: DETState, 
                        target_emotion: DETEmotion,
                        regulation_type: str = "reappraisal",
                        time_span: Tuple[float, float] = (0.0, 5.0)) -> DETState:
        """
        Apply emotion regulation strategies to modulate emotional response
        
        Args:
            det_state: Current DET state
            target_emotion: The emotion to regulate
            regulation_type: Strategy to use ("suppression", "reappraisal", or "distraction")
            time_span: Time range for simulation
            
        Returns:
            Updated DET state after regulation
        """
        if self.use_julia:
            try:
                # Call Julia regulation simulation
                regulated_emotions = self.det_julia.simulate_regulation(
                    det_state.det_emotions.tolist(),
                    det_state.regulation_capacity,
                    int(target_emotion),
                    regulation_type,
                    time_span
                )
                
                # Create new DET state with regulated emotions
                result = DETState(
                    det_emotions=np.array(regulated_emotions),
                    transition_matrix=det_state.transition_matrix.copy(),
                    cognitive_factors=det_state.cognitive_factors.copy(),
                    active_scripts=det_state.active_scripts.copy(),
                    regulation_capacity=det_state.regulation_capacity,
                    script_history=det_state.script_history.copy()
                )
                
                return result
                
            except Exception as e:
                self.logger.error(f"Julia emotion regulation failed: {e}. Falling back to Python.")
                return self._regulate_emotion_python(det_state, target_emotion, regulation_type, time_span)
        else:
            return self._regulate_emotion_python(det_state, target_emotion, regulation_type, time_span)
    
    def _regulate_emotion_python(self,
                               det_state: DETState,
                               target_emotion: DETEmotion,
                               regulation_type: str,
                               time_span: Tuple[float, float]) -> DETState:
        """Python fallback implementation for emotion regulation"""
        # Copy current emotional state
        emotions = det_state.det_emotions.copy()
        reg_capacity = det_state.regulation_capacity
        target = int(target_emotion)
        
        t_start, t_end = time_span
        dt = 0.1  # Time step
        
        t = t_start
        while t < t_end:
            derivatives = np.zeros(17)
            
            for i in range(17):
                # Natural decay
                decay = -0.1 * emotions[i]
                
                # Regulation effect
                regulation = 0.0
                
                if regulation_type == "suppression":
                    # Suppression reduces target emotion but increases others slightly
                    if i == target:
                        regulation = -0.3 * reg_capacity
                    else:
                        regulation = 0.05 * reg_capacity
                        
                elif regulation_type == "reappraisal":
                    # Reappraisal reduces negative emotions and increases positive
                    if i in [2, 3, 4, 5, 6, 7, 8, 12, 13]:  # Negative emotions
                        regulation = -0.2 * reg_capacity
                    elif i in [0, 1, 9, 10, 11, 14, 15]:  # Positive emotions
                        regulation = 0.1 * reg_capacity
                        
                elif regulation_type == "distraction":
                    # Distraction reduces all emotions slightly
                    regulation = -0.1 * reg_capacity
                
                # Combine effects
                derivatives[i] = decay + regulation
            
            # Update emotions
            emotions += derivatives * dt
            
            # Ensure values stay in reasonable ranges
            emotions = np.clip(emotions, 0.0, 1.0)
            
            t += dt
        
        # Create new DET state with regulated emotions
        result = DETState(
            det_emotions=emotions,
            transition_matrix=det_state.transition_matrix.copy(),
            cognitive_factors=det_state.cognitive_factors.copy(),
            active_scripts=det_state.active_scripts.copy(),
            regulation_capacity=det_state.regulation_capacity,
            script_history=det_state.script_history.copy()
        )
        
        return result
    
    def identify_active_scripts(self, det_state: DETState, threshold: float = 0.5) -> List[EmotionalScript]:
        """
        Identify which emotional scripts are active based on current emotions
        
        Args:
            det_state: Current DET state
            threshold: Minimum match required to activate a script (0.0-1.0)
            
        Returns:
            List of active emotional scripts
        """
        # Find dominant emotions
        active_emotions = [
            DETEmotion(i) for i, intensity in enumerate(det_state.det_emotions)
            if intensity > 0.2
        ]
        
        # Find matching scripts
        active_scripts = []
        for script in self.script_library:
            # Calculate match percentage
            if script.matches_emotions(active_emotions):
                active_scripts.append(script)
        
        # Update DET state with active scripts
        det_state.active_scripts = active_scripts
        
        # Add to script history
        if active_scripts:
            det_state.script_history.appendleft(active_scripts[0])
        
        return active_scripts
    
    def extract_behavioral_responses(self, det_state: DETState) -> List[str]:
        """
        Extract behavioral responses from active emotional scripts
        
        Args:
            det_state: Current DET state with active scripts
            
        Returns:
            List of behavioral responses from active scripts
        """
        responses = []
        
        for script in det_state.active_scripts:
            responses.extend(script.behavioral_responses)
        
        # Remove duplicates while preserving order
        unique_responses = []
        for response in responses:
            if response not in unique_responses:
                unique_responses.append(response)
        
        return unique_responses
    
    def content_to_det_emotion(self, content: str) -> np.ndarray:
        """
        Extract DET emotional state from text content
        
        Args:
            content: Text to analyze
            
        Returns:
            17-element array of DET emotion intensities
        """
        # Start with core emotion extraction
        core_emotions = self.base_dynamics.content_to_emotion(content)
        
        # Map to DET emotions
        det_emotions = self.map_core_to_det(core_emotions)
        
        # Fine-tune with more specific keywords for DET emotions
        emotion_keywords = {
            DETEmotion.INTEREST: ["interest", "curious", "attention", "focus"],
            DETEmotion.EXCITEMENT: ["excite", "thrill", "enthusiastic", "eager"],
            DETEmotion.ANGER: ["anger", "mad", "furious", "irritated"],
            DETEmotion.CONTEMPT: ["contempt", "disdain", "scorn", "dismissive"],
            DETEmotion.DISGUST: ["disgust", "repulsed", "revolting", "gross"],
            DETEmotion.FEAR: ["fear", "afraid", "scared", "terrified"],
            DETEmotion.SHAME: ["shame", "embarrass", "humiliated", "inadequate"],
            DETEmotion.SHYNESS: ["shy", "timid", "bashful", "hesitant"],
            DETEmotion.GUILT: ["guilt", "remorse", "regret", "apologetic"],
            DETEmotion.DESIRE: ["desire", "want", "crave", "wish"],
            DETEmotion.LOVE: ["love", "adore", "cherish", "devoted"],
            DETEmotion.TENDERNESS: ["tender", "gentle", "soft", "affectionate"],
            DETEmotion.DISTRESS: ["distress", "upset", "troubled", "worried"],
            DETEmotion.SADNESS: ["sad", "sorrow", "misery", "unhappy"],
            DETEmotion.JOY: ["joy", "happy", "pleased", "delight"],
            DETEmotion.AMUSEMENT: ["amuse", "laugh", "funny", "playful"],
            DETEmotion.SURPRISE: ["surprise", "astonish", "shock", "unexpected"]
        }
        
        # Count keyword occurrences for fine-tuning
        content_lower = content.lower()
        total_matches = 0
        match_counts = np.zeros(17)
        
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                count = content_lower.count(keyword)
                match_counts[emotion] += count
                total_matches += count
        
        # If we found specific emotion keywords, use them to adjust the estimates
        if total_matches > 0:
            # Normalize counts
            normalized_counts = match_counts / (total_matches * 2)  # Divide by total*2 to keep values reasonable
            
            # Blend with mapped emotions (70% mapping, 30% keyword analysis)
            det_emotions = 0.7 * det_emotions + 0.3 * normalized_counts
            
            # Ensure values remain in [0.1, 1.0]
            det_emotions = np.clip(det_emotions, 0.1, 1.0)
        
        return det_emotions