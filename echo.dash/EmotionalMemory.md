module EmotionalMemory

using DifferentialEquations
using ModelingToolkit
using LinearAlgebra
using Plots

# Core emotions based on Panksepp's affective neuroscience
@enum CoreEmotion begin
    SEEKING
    RAGE
    FEAR
    LUST
    CARE
    PANIC_GRIEF
    PLAY
end

# Struct to represent an emotional state as a dynamical system
struct EmotionalState
    core_emotions::Vector{Float64} # Intensity of each core emotion (0.0-1.0)
    stability::Float64 # How stable this emotional state is (0.0-1.0)
    decay_rate::Float64 # How quickly the emotion decays (0.0-1.0)
    coupling_matrix::Matrix{Float64} # How emotions influence each other
end

# Create a default emotional state with balanced emotions
function default_emotional_state()
    # Equal levels of all core emotions
    core_emotions = fill(0.1, 7)
    
    # Medium stability
    stability = 0.5
    
    # Medium decay rate
    decay_rate = 0.3
    
    # Coupling matrix - how emotions affect each other
    # Rows: source emotion, Columns: target emotion
    coupling_matrix = [
        # SEEKING RAGE   FEAR   LUST   CARE   PANIC  PLAY
          0.1    -0.2   -0.1    0.2    0.1    -0.2    0.3;  # SEEKING affects others
         -0.2     0.1   -0.3   -0.2   -0.3     0.1   -0.2;  # RAGE affects others
         -0.3    -0.1    0.1   -0.2   -0.1     0.3   -0.3;  # FEAR affects others
          0.2    -0.2   -0.2    0.1    0.3    -0.1    0.2;  # LUST affects others
          0.3    -0.3   -0.2    0.2    0.1    -0.3    0.3;  # CARE affects others
         -0.3     0.2    0.3   -0.2   -0.1     0.1   -0.2;  # PANIC_GRIEF affects others
          0.3    -0.2   -0.3    0.2    0.2    -0.2    0.1;  # PLAY affects others
    ]
    
    return EmotionalState(core_emotions, stability, decay_rate, coupling_matrix)
end

# The 49 composite emotional states (7x7 combinations)
function generate_compound_emotions()
    compound_emotions = Dict{Tuple{CoreEmotion, CoreEmotion}, String}()
    
    # Define compound emotions (simplified examples)
    compound_emotions[(SEEKING, RAGE)] = "Frustration"
    compound_emotions[(SEEKING, FEAR)] = "Anxiety"
    compound_emotions[(SEEKING, LUST)] = "Desire"
    compound_emotions[(SEEKING, CARE)] = "Compassionate Curiosity"
    compound_emotions[(SEEKING, PANIC_GRIEF)] = "Desperate Searching"
    compound_emotions[(SEEKING, PLAY)] = "Enthusiastic Exploration"
    
    compound_emotions[(RAGE, SEEKING)] = "Determined Anger"
    compound_emotions[(RAGE, FEAR)] = "Defensive Rage"
    compound_emotions[(RAGE, LUST)] = "Jealousy"
    compound_emotions[(RAGE, CARE)] = "Protective Anger"
    compound_emotions[(RAGE, PANIC_GRIEF)] = "Bitter Resentment"
    compound_emotions[(RAGE, PLAY)] = "Competitive Aggression"
    
    # Continue with other combinations...
    compound_emotions[(FEAR, SEEKING)] = "Cautious Investigation"
    compound_emotions[(FEAR, RAGE)] = "Terrified Aggression"
    compound_emotions[(FEAR, LUST)] = "Sexual Anxiety"
    compound_emotions[(FEAR, CARE)] = "Worried Concern"
    compound_emotions[(FEAR, PANIC_GRIEF)] = "Despair"
    compound_emotions[(FEAR, PLAY)] = "Timid Play"
    
    compound_emotions[(LUST, SEEKING)] = "Passionate Pursuit"
    compound_emotions[(LUST, RAGE)] = "Possessive Desire"
    compound_emotions[(LUST, FEAR)] = "Insecure Attraction"
    compound_emotions[(LUST, CARE)] = "Romantic Affection"
    compound_emotions[(LUST, PANIC_GRIEF)] = "Lovesickness"
    compound_emotions[(LUST, PLAY)] = "Flirtation"
    
    compound_emotions[(CARE, SEEKING)] = "Nurturing Guidance"
    compound_emotions[(CARE, RAGE)] = "Fierce Protection"
    compound_emotions[(CARE, FEAR)] = "Anxious Attachment"
    compound_emotions[(CARE, LUST)] = "Intimate Bonding"
    compound_emotions[(CARE, PANIC_GRIEF)] = "Empathetic Sorrow"
    compound_emotions[(CARE, PLAY)] = "Playful Nurturing"
    
    compound_emotions[(PANIC_GRIEF, SEEKING)] = "Yearning"
    compound_emotions[(PANIC_GRIEF, RAGE)] = "Agitated Distress"
    compound_emotions[(PANIC_GRIEF, FEAR)] = "Traumatic Grief"
    compound_emotions[(PANIC_GRIEF, LUST)] = "Longing"
    compound_emotions[(PANIC_GRIEF, CARE)] = "Separation Anxiety"
    compound_emotions[(PANIC_GRIEF, PLAY)] = "Bitter Humor"
    
    compound_emotions[(PLAY, SEEKING)] = "Creative Exploration"
    compound_emotions[(PLAY, RAGE)] = "Rough Play"
    compound_emotions[(PLAY, FEAR)] = "Thrilling Adventure"
    compound_emotions[(PLAY, LUST)] = "Erotic Play"
    compound_emotions[(PLAY, CARE)] = "Nurturing Play"
    compound_emotions[(PLAY, PANIC_GRIEF)] = "Consoling Play"

    return compound_emotions
end

# Differential equations that govern how emotions evolve
function emotional_dynamics!(du, u, p, t)
    emotional_state = p
    
    # Extract parameters
    stability = emotional_state.stability
    decay_rate = emotional_state.decay_rate
    coupling = emotional_state.coupling_matrix
    
    # For each emotion
    for i in 1:7
        # Natural decay term
        decay = -decay_rate * u[i]
        
        # Stability term - pulls toward baseline emotional state
        pull_to_baseline = stability * (emotional_state.core_emotions[i] - u[i])
        
        # Coupling term - how other emotions affect this one
        coupling_effect = sum(coupling[j, i] * u[j] for j in 1:7)
        
        # Combine effects
        du[i] = decay + pull_to_baseline + coupling_effect
    end
end

# Simulate emotional dynamics over time
function simulate_emotions(initial_state::Vector{Float64}, emotional_state::EmotionalState, tspan::Tuple{Float64, Float64})
    # Create the ODE problem
    prob = ODEProblem(emotional_dynamics!, initial_state, tspan, emotional_state)
    
    # Solve the ODE
    sol = solve(prob, Tsit5(), reltol=1e-6, abstol=1e-6)
    
    return sol
end

# Calculate the dominant emotions from a state vector
function dominant_emotions(state::Vector{Float64}, threshold::Float64=0.2)
    # Find emotions above threshold
    active_indices = findall(e -> e > threshold, state)
    
    # Sort by intensity
    sort!(active_indices, by=i -> state[i], rev=true)
    
    # Return as CoreEmotion enum values
    return [CoreEmotion(i-1) for i in active_indices]
end

# Identify compound emotion from current state
function identify_compound_emotion(state::Vector{Float64})
    # Get top two emotions
    dom_emotions = dominant_emotions(state)
    
    if length(dom_emotions) >= 2
        compound_emotions = generate_compound_emotions()
        emotion_pair = (dom_emotions[1], dom_emotions[2])
        
        # Check if this compound exists in our dictionary
        if haskey(compound_emotions, emotion_pair)
            return compound_emotions[emotion_pair]
        end
    end
    
    # If no compound emotion is found, return the dominant single emotion
    if !isempty(dom_emotions)
        return string(dom_emotions[1])
    else
        return "Neutral"
    end
end

# Visualize emotional dynamics over time
function visualize_emotions(solution)
    # Plot setup
    p = plot(title="Emotional Dynamics", xlabel="Time", ylabel="Intensity",
             legend=:topright, size=(800, 500))
    
    # Get emotion names
    emotion_names = [string(e) for e in instances(CoreEmotion)]
    
    # Plot each emotion trajectory
    for i in 1:7
        plot!(p, solution.t, [s[i] for s in solution.u], 
              label=emotion_names[i], linewidth=2)
    end
    
    return p
end

# Example usage:
# es = default_emotional_state()
# initial_emotions = [0.8, 0.1, 0.6, 0.2, 0.1, 0.1, 0.1]  # High SEEKING and FEAR
# solution = simulate_emotions(initial_emotions, es, (0.0, 10.0))
# visualize_emotions(solution)
# println("Dominant emotions: ", [string(e) for e in dominant_emotions(solution.u[end])])
# println("Compound emotion: ", identify_compound_emotion(solution.u[end]))

end # module