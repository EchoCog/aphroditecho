/**
 * @file ecan_attention.cpp
 * @brief Implementation of ECAN attention system using GGML tensors
 */

#include "ecan_attention.h"
#include <algorithm>
#include <cmath>
#include <random>
#include <iostream>

namespace opencog {

// AttentionBank implementation

AttentionBank::AttentionBank(struct ggml_context* ctx) 
    : ctx_(ctx), total_stimulus(0.0f), total_funding(1000.0f),
      min_sti(0.0f), max_sti(1.0f), attentional_focus_size_(100),
      attention_tensor_(nullptr), stimulus_tensor_(nullptr), wage_tensor_(nullptr) {
}

AttentionBank::~AttentionBank() {
    // Tensors are managed by GGML context
}

void AttentionBank::set_parameters(float total_funding, float min_sti, 
                                  float max_sti, size_t focus_size) {
    total_funding = total_funding;
    min_sti = min_sti;
    max_sti = max_sti;
    attentional_focus_size_ = focus_size;
}

void AttentionBank::update_attention_values(TensorAtomSpace* atomspace) {
    if (!atomspace) return;
    
    // Get atomspace statistics
    auto stats = atomspace->get_stats();
    if (stats.num_atoms == 0) return;
    
    // Create or update attention tensor if needed
    if (!attention_tensor_ || ggml_nelements(attention_tensor_) != stats.num_atoms * 3) {
        attention_tensor_ = ggml_new_tensor_2d(ctx_, GGML_TYPE_F32, 3, stats.num_atoms);
        stimulus_tensor_ = ggml_new_tensor_1d(ctx_, GGML_TYPE_F32, stats.num_atoms);
        wage_tensor_ = ggml_new_tensor_1d(ctx_, GGML_TYPE_F32, stats.num_atoms);
    }
    
    update_tensor_data(atomspace);
    
    // Apply ECAN update algorithm using custom GGML operation
    struct ggml_tensor* updated_attention = ggml_attention_update(
        ctx_, attention_tensor_, stimulus_tensor_, wage_tensor_);
    
    // Copy results back to attention tensor
    if (updated_attention && updated_attention->data && attention_tensor_->data) {
        memcpy(attention_tensor_->data, updated_attention->data, 
               ggml_nbytes(attention_tensor_));
    }
    
    normalize_attention_values();
}

void AttentionBank::stimulate_atom(Handle atom, float amount) {
    total_stimulus += amount;
    // This would update the specific atom's stimulus in the tensor
}

void AttentionBank::collect_rent(TensorAtomSpace* atomspace) {
    if (!attention_tensor_) return;
    
    float* attention_data = (float*)attention_tensor_->data;
    if (!attention_data) return;
    
    size_t num_atoms = ggml_nelements(attention_tensor_) / 3;
    
    // Apply rent collection (attention decay)
    for (size_t i = 0; i < num_atoms; ++i) {
        size_t sti_idx = i * 3;
        float& sti = attention_data[sti_idx];
        
        // Rent formula: higher STI pays more rent
        float rent = sti * 0.01f; // 1% rent rate
        sti = std::max(min_sti, sti - rent);
    }
}

std::vector<Handle> AttentionBank::get_attentional_focus(TensorAtomSpace* atomspace) const {
    std::vector<Handle> focus_atoms;
    if (!atomspace) return focus_atoms;
    
    // Get all atoms with high attention
    auto high_attention_atoms = atomspace->get_attentional_focus(0.5f);
    
    // Sort by attention value and take top N
    std::sort(high_attention_atoms.begin(), high_attention_atoms.end(),
              [atomspace](Handle a, Handle b) {
                  auto* atom_a = atomspace->get_atom(a);
                  auto* atom_b = atomspace->get_atom(b);
                  return atom_a->attention.sti > atom_b->attention.sti;
              });
    
    // Return top atoms up to focus size
    size_t focus_size = std::min(attentional_focus_size_, high_attention_atoms.size());
    focus_atoms.assign(high_attention_atoms.begin(), 
                      high_attention_atoms.begin() + focus_size);
    
    return focus_atoms;
}

AttentionBank::BankStats AttentionBank::get_statistics(TensorAtomSpace* atomspace) const {
    BankStats stats = {};
    
    if (!atomspace || !attention_tensor_) return stats;
    
    const float* attention_data = (const float*)attention_tensor_->data;
    if (!attention_data) return stats;
    
    size_t num_atoms = ggml_nelements(attention_tensor_) / 3;
    
    for (size_t i = 0; i < num_atoms; ++i) {
        stats.total_sti += attention_data[i * 3];
        stats.total_lti += attention_data[i * 3 + 1];
    }
    
    stats.avg_attention = num_atoms > 0 ? stats.total_sti / num_atoms : 0.0f;
    stats.atoms_in_focus = get_attentional_focus(atomspace).size();
    stats.stimulus_spent = total_stimulus;
    
    return stats;
}

void AttentionBank::normalize_attention_values() {
    if (!attention_tensor_) return;
    
    float* attention_data = (float*)attention_tensor_->data;
    if (!attention_data) return;
    
    size_t num_atoms = ggml_nelements(attention_tensor_) / 3;
    
    // Ensure STI values stay within bounds
    for (size_t i = 0; i < num_atoms; ++i) {
        float& sti = attention_data[i * 3];
        sti = std::max(min_sti, std::min(max_sti, sti));
    }
}

void AttentionBank::update_tensor_data(TensorAtomSpace* atomspace) {
    // This would sync the tensor data with atomspace attention values
    // Implementation depends on the atomspace internal structure
}

// ECANAttentionSystem implementation

ECANAttentionSystem::ECANAttentionSystem(TensorAtomSpace* atomspace)
    : atomspace_(atomspace), forgetting_rate_(0.01f), spreading_rate_(0.1f),
      update_frequency_(10), cycle_count_(0) {
    
    bank_ = std::make_unique<AttentionBank>(atomspace->get_context());
    stats_ = {};
}

ECANAttentionSystem::~ECANAttentionSystem() = default;

void ECANAttentionSystem::initialize(float total_funding, size_t focus_size) {
    bank_->set_parameters(total_funding, 0.0f, 1.0f, focus_size);
    
    // Add default agents
    auto default_agents = ECANAgentFactory::create_standard_agents();
    for (auto& agent : default_agents) {
        agents_.push_back(std::move(agent));
    }
}

void ECANAttentionSystem::run_cycle() {
    cycle_count_++;
    
    // Run ECAN sub-processes
    run_importance_updating();
    run_importance_diffusion();
    run_forgetting();
    
    if (cycle_count_ % update_frequency_ == 0) {
        run_rent_collection();
    }
    
    // Activate agents
    activate_agents();
    
    update_statistics();
    stats_.total_cycles++;
}

void ECANAttentionSystem::add_agent(std::unique_ptr<AttentionAgent> agent) {
    agents_.push_back(std::move(agent));
}

void ECANAttentionSystem::remove_agent(const std::string& agent_name) {
    agents_.erase(
        std::remove_if(agents_.begin(), agents_.end(),
                      [&agent_name](const std::unique_ptr<AttentionAgent>& agent) {
                          return agent->name == agent_name;
                      }),
        agents_.end());
}

void ECANAttentionSystem::set_parameters(float forgetting_rate, 
                                        float spreading_rate, int update_freq) {
    forgetting_rate_ = forgetting_rate;
    spreading_rate_ = spreading_rate;
    update_frequency_ = update_freq;
}

void ECANAttentionSystem::focus_on_atom(Handle atom, float intensity) {
    bank_->stimulate_atom(atom, intensity);
    atomspace_->update_attention(atom, AttentionValue(intensity, 0.0f, 0.0f));
}

void ECANAttentionSystem::spread_activation(Handle source_atom, float amount) {
    atomspace_->spread_activation(source_atom, amount);
}

std::vector<Handle> ECANAttentionSystem::get_focus() const {
    return bank_->get_attentional_focus(atomspace_);
}

std::vector<std::pair<Handle, float>> ECANAttentionSystem::get_importance_ranking(size_t top_n) const {
    auto focus_atoms = get_focus();
    std::vector<std::pair<Handle, float>> ranking;
    
    for (Handle atom : focus_atoms) {
        auto* tensor_atom = atomspace_->get_atom(atom);
        if (tensor_atom) {
            ranking.emplace_back(atom, tensor_atom->attention.sti);
        }
    }
    
    // Sort by STI descending
    std::sort(ranking.begin(), ranking.end(),
              [](const auto& a, const auto& b) {
                  return a.second > b.second;
              });
    
    // Return top N
    if (ranking.size() > top_n) {
        ranking.resize(top_n);
    }
    
    return ranking;
}

void ECANAttentionSystem::external_stimulus(Handle atom, float intensity) {
    focus_on_atom(atom, intensity);
}

ECANAttentionSystem::ECANStats ECANAttentionSystem::get_statistics() const {
    return stats_;
}

void ECANAttentionSystem::reset() {
    cycle_count_ = 0;
    stats_ = {};
    agents_.clear();
    initialize(); // Reinitialize with default agents
}

// Internal methods

void ECANAttentionSystem::run_importance_updating() {
    bank_->update_attention_values(atomspace_);
}

void ECANAttentionSystem::run_importance_diffusion() {
    auto focus_atoms = get_focus();
    
    // Spread importance among connected atoms
    for (Handle atom : focus_atoms) {
        spread_activation(atom, spreading_rate_);
    }
}

void ECANAttentionSystem::run_forgetting() {
    // Apply forgetting to low-importance atoms
    auto all_atoms = atomspace_->get_attentional_focus(0.0f); // Get all atoms
    
    for (Handle atom : all_atoms) {
        auto* tensor_atom = atomspace_->get_atom(atom);
        if (tensor_atom && tensor_atom->attention.sti < 0.1f) {
            // Apply forgetting
            AttentionValue new_av = tensor_atom->attention;
            new_av.sti *= (1.0f - forgetting_rate_);
            atomspace_->update_attention(atom, new_av);
        }
    }
}

void ECANAttentionSystem::run_rent_collection() {
    bank_->collect_rent(atomspace_);
}

void ECANAttentionSystem::activate_agents() {
    for (auto& agent : agents_) {
        if (agent->active) {
            // Run agent-specific logic
            // This would be implemented per agent type
        }
    }
}

void ECANAttentionSystem::update_agent_wages() {
    // Update agent wages based on performance
    for (auto& agent : agents_) {
        // Simple performance-based wage adjustment
        agent->wage *= 0.99f; // Slight decay
        if (agent->activation_level > 0.5f) {
            agent->wage *= 1.02f; // Bonus for active agents
        }
    }
}

float ECANAttentionSystem::calculate_attention_efficiency() const {
    auto bank_stats = bank_->get_statistics(atomspace_);
    float total_attention = bank_stats.total_sti + bank_stats.total_lti;
    return total_attention > 0 ? bank_stats.atoms_in_focus / total_attention : 0.0f;
}

void ECANAttentionSystem::update_statistics() {
    stats_.attention_efficiency = calculate_attention_efficiency();
    auto focus = get_focus();
    stats_.avg_focus_size = (stats_.avg_focus_size * (stats_.total_cycles - 1) + focus.size()) / stats_.total_cycles;
}

// Agent implementations

void NoveltyDetectionAgent::run(TensorAtomSpace* atomspace, AttentionBank* bank) {
    // Detect atoms with significant STI changes
    auto focus_atoms = bank->get_attentional_focus(atomspace);
    
    for (Handle atom : focus_atoms) {
        auto* tensor_atom = atomspace->get_atom(atom);
        if (!tensor_atom) continue;
        
        float current_sti = tensor_atom->attention.sti;
        float last_sti = last_seen_sti_[atom];
        
        if (std::abs(current_sti - last_sti) > novelty_threshold_) {
            // Boost attention for novel atoms
            bank->stimulate_atom(atom, 0.1f);
        }
        
        last_seen_sti_[atom] = current_sti;
    }
}

void ImportanceSpreadingAgent::run(TensorAtomSpace* atomspace, AttentionBank* bank) {
    auto focus_atoms = bank->get_attentional_focus(atomspace);
    
    for (Handle atom : focus_atoms) {
        // Spread importance to connected atoms
        atomspace->spread_activation(atom, spreading_factor_);
    }
}

void ForgettingAgent::run(TensorAtomSpace* atomspace, AttentionBank* bank) {
    auto all_atoms = atomspace->get_attentional_focus(0.0f);
    
    for (Handle atom : all_atoms) {
        auto* tensor_atom = atomspace->get_atom(atom);
        if (tensor_atom && tensor_atom->attention.sti < forgetting_threshold_) {
            AttentionValue av = tensor_atom->attention;
            av.sti *= (1.0f - forgetting_rate_);
            atomspace->update_attention(atom, av);
        }
    }
}

void ReinforcementAgent::run(TensorAtomSpace* atomspace, AttentionBank* bank) {
    // Reinforce attention for atoms involved in successful patterns
    for (size_t i = 0; i < successful_patterns_.size(); ++i) {
        const auto& pattern = successful_patterns_[i];
        float reward = pattern_rewards_[i];
        
        for (Handle atom : pattern) {
            bank->stimulate_atom(atom, reward * learning_rate_);
        }
    }
}

void ReinforcementAgent::reinforce_successful_inference(
    const std::vector<Handle>& atoms, float reward) {
    successful_patterns_.push_back(atoms);
    pattern_rewards_.push_back(reward);
    
    // Keep only recent patterns
    if (successful_patterns_.size() > 100) {
        successful_patterns_.erase(successful_patterns_.begin());
        pattern_rewards_.erase(pattern_rewards_.begin());
    }
}

// ECANAgentFactory implementation

std::vector<std::unique_ptr<AttentionAgent>> ECANAgentFactory::create_standard_agents() {
    std::vector<std::unique_ptr<AttentionAgent>> agents;
    
    agents.push_back(std::make_unique<NoveltyDetectionAgent>());
    agents.push_back(std::make_unique<ImportanceSpreadingAgent>());
    agents.push_back(std::make_unique<ForgettingAgent>());
    agents.push_back(std::make_unique<ReinforcementAgent>());
    
    return agents;
}

std::unique_ptr<AttentionAgent> ECANAgentFactory::create_agent(const std::string& type) {
    if (type == "NoveltyDetection") {
        return std::make_unique<NoveltyDetectionAgent>();
    } else if (type == "ImportanceSpreading") {
        return std::make_unique<ImportanceSpreadingAgent>();
    } else if (type == "Forgetting") {
        return std::make_unique<ForgettingAgent>();
    } else if (type == "Reinforcement") {
        return std::make_unique<ReinforcementAgent>();
    }
    
    return nullptr;
}

} // namespace opencog