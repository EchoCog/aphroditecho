#pragma once

/**
 * @file ecan_attention.h
 * @brief Economic Attention Networks (ECAN) implementation using GGML tensors
 * 
 * This file implements the ECAN attention allocation system for managing
 * cognitive resources in the OpenCog architecture using efficient tensor operations.
 */

#include "../atomspace/tensor_atomspace.h"
#include "../operations/ggml_opencog_ops.h"
#include <vector>
#include <queue>
#include <memory>

namespace opencog {

/**
 * @brief Economic agent for attention allocation
 */
struct AttentionAgent {
    std::string name;
    float wage;              // Economic wage for this agent
    float activation_level;  // Current activation
    int priority;           // Agent priority
    bool active;            // Whether agent is currently active
    
    AttentionAgent(const std::string& n, float w = 1.0f, int p = 1) 
        : name(n), wage(w), activation_level(0.0f), priority(p), active(true) {}
};

/**
 * @brief Attention bank for economic attention allocation
 */
class AttentionBank {
private:
    float total_stimulus;           // Total stimulus in the system
    float total_funding;            // Total funding available
    float min_sti;                  // Minimum STI threshold
    float max_sti;                  // Maximum STI threshold
    size_t attentional_focus_size_; // Size of attentional focus
    
    // GGML tensors for efficient computation
    struct ggml_context* ctx_;
    struct ggml_tensor* attention_tensor_;    // [STI, LTI, VLTI] for all atoms
    struct ggml_tensor* stimulus_tensor_;     // Stimulus values
    struct ggml_tensor* wage_tensor_;         // Economic wages
    
public:
    explicit AttentionBank(struct ggml_context* ctx);
    ~AttentionBank();
    
    /**
     * @brief Set bank parameters
     */
    void set_parameters(float total_funding = 1000.0f,
                       float min_sti = 0.0f,
                       float max_sti = 1.0f,
                       size_t focus_size = 100);
    
    /**
     * @brief Update attention values for all atoms
     */
    void update_attention_values(TensorAtomSpace* atomspace);
    
    /**
     * @brief Allocate stimulus to atom
     */
    void stimulate_atom(Handle atom, float amount);
    
    /**
     * @brief Rent collection for attention decay
     */
    void collect_rent(TensorAtomSpace* atomspace);
    
    /**
     * @brief Get attentional focus set
     */
    std::vector<Handle> get_attentional_focus(TensorAtomSpace* atomspace) const;
    
    /**
     * @brief Get bank statistics
     */
    struct BankStats {
        float total_sti;
        float total_lti;
        float avg_attention;
        size_t atoms_in_focus;
        float stimulus_spent;
    };
    
    BankStats get_statistics(TensorAtomSpace* atomspace) const;

private:
    void normalize_attention_values();
    void update_tensor_data(TensorAtomSpace* atomspace);
};

/**
 * @brief ECAN attention allocation system
 */
class ECANAttentionSystem {
private:
    TensorAtomSpace* atomspace_;
    std::unique_ptr<AttentionBank> bank_;
    std::vector<std::unique_ptr<AttentionAgent>> agents_;
    
    // System parameters
    float forgetting_rate_;
    float spreading_rate_;
    int update_frequency_;
    int cycle_count_;
    
    // Performance monitoring
    struct ECANStats {
        size_t total_cycles;
        float avg_focus_size;
        float attention_efficiency;
        std::map<std::string, float> agent_performance;
    };
    
    mutable ECANStats stats_;

public:
    /**
     * @brief Constructor
     */
    explicit ECANAttentionSystem(TensorAtomSpace* atomspace);
    
    /**
     * @brief Destructor
     */
    ~ECANAttentionSystem();
    
    /**
     * @brief Initialize ECAN system
     */
    void initialize(float total_funding = 1000.0f, 
                   size_t focus_size = 100);
    
    /**
     * @brief Run one ECAN cycle
     */
    void run_cycle();
    
    /**
     * @brief Add attention agent
     */
    void add_agent(std::unique_ptr<AttentionAgent> agent);
    
    /**
     * @brief Remove attention agent
     */
    void remove_agent(const std::string& agent_name);
    
    /**
     * @brief Set system parameters
     */
    void set_parameters(float forgetting_rate = 0.01f,
                       float spreading_rate = 0.1f,
                       int update_freq = 10);
    
    /**
     * @brief Focus on specific atom
     */
    void focus_on_atom(Handle atom, float intensity = 1.0f);
    
    /**
     * @brief Spread activation from atom
     */
    void spread_activation(Handle source_atom, float amount = 0.1f);
    
    /**
     * @brief Get current attentional focus
     */
    std::vector<Handle> get_focus() const;
    
    /**
     * @brief Get atom importance ranking
     */
    std::vector<std::pair<Handle, float>> get_importance_ranking(size_t top_n = 20) const;
    
    /**
     * @brief Update attention based on external stimulus
     */
    void external_stimulus(Handle atom, float intensity);
    
    /**
     * @brief Get system statistics
     */
    ECANStats get_statistics() const;
    
    /**
     * @brief Reset attention system
     */
    void reset();

private:
    // Internal ECAN algorithms
    void run_importance_updating();
    void run_importance_diffusion();
    void run_forgetting();
    void run_rent_collection();
    
    // Agent management
    void activate_agents();
    void update_agent_wages();
    
    // Utility functions
    float calculate_attention_efficiency() const;
    void update_statistics();
};

/**
 * @brief Specific attention agents for different cognitive functions
 */

/**
 * @brief Agent for novelty detection
 */
class NoveltyDetectionAgent : public AttentionAgent {
public:
    NoveltyDetectionAgent() : AttentionAgent("NoveltyDetection", 1.0f, 2) {}
    
    void run(TensorAtomSpace* atomspace, AttentionBank* bank);

private:
    std::unordered_map<Handle, float> last_seen_sti_;
    float novelty_threshold_ = 0.1f;
};

/**
 * @brief Agent for importance spreading
 */
class ImportanceSpreadingAgent : public AttentionAgent {
public:
    ImportanceSpreadingAgent() : AttentionAgent("ImportanceSpreading", 0.8f, 1) {}
    
    void run(TensorAtomSpace* atomspace, AttentionBank* bank);

private:
    float spreading_factor_ = 0.1f;
    float decay_factor_ = 0.95f;
};

/**
 * @brief Agent for forgetting low-importance atoms
 */
class ForgettingAgent : public AttentionAgent {
public:
    ForgettingAgent() : AttentionAgent("Forgetting", 0.5f, 3) {}
    
    void run(TensorAtomSpace* atomspace, AttentionBank* bank);

private:
    float forgetting_threshold_ = 0.01f;
    float forgetting_rate_ = 0.02f;
};

/**
 * @brief Agent for reinforcement learning from successful inferences
 */
class ReinforcementAgent : public AttentionAgent {
public:
    ReinforcementAgent() : AttentionAgent("Reinforcement", 1.2f, 2) {}
    
    void run(TensorAtomSpace* atomspace, AttentionBank* bank);
    void reinforce_successful_inference(const std::vector<Handle>& atoms, float reward);

private:
    std::vector<std::vector<Handle>> successful_patterns_;
    std::vector<float> pattern_rewards_;
    float learning_rate_ = 0.1f;
};

/**
 * @brief Factory for creating standard ECAN agents
 */
class ECANAgentFactory {
public:
    static std::vector<std::unique_ptr<AttentionAgent>> create_standard_agents();
    static std::unique_ptr<AttentionAgent> create_agent(const std::string& type);
};

} // namespace opencog