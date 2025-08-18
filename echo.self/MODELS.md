# CogPrime Cognitive Models Catalog

---

@models:
version: "1.0"
description: "Central cognitive and data models in the drzo/opencog-central repository"
last_updated: "2024"
cognitive_architecture: "CogPrime"
hypergraph_encoding: "AtomSpace"

---

This document catalogs the central cognitive and data models that implement the CogPrime architecture vision. Each model represents a hypergraph substructure contributing to overall cognitive synergy.

## Core Cognitive Models

### AtomSpace

- **Type**: Central Knowledge Repository
- **Description**: Weighted, labeled hypergraph serving as the core knowledge representation system
- **Components**: Atoms, Links, TruthValues, AttentionValues
- **Purpose**: Unified storage for declarative, procedural, episodic, and attentional knowledge
- **Source**: [AtomSpace Repository](https://github.com/opencog/atomspace)
- **Status**: Active & Stable

### EvaPhysicalSelfModel

- **Type**: Embodied Self-Awareness Model
- **Description**: Maintains a real-time model of Eva's physical state and activities in the AtomSpace
- **Components**: Face tracking, movement coordination, action orchestration, self-awareness queries
- **Purpose**: Enable coherent behavior and self-reflective responses
- **Source**: [`Scheme/opencog-opencog-opencog-eva-model-self-model.scm`](Scheme/opencog-opencog-opencog-eva-model-self-model.scm)
- **Architecture**: [@mermaid-chart](#eva-self-model-integration)
- **Status**: Implemented

### MOSES (Meta-Optimizing Semantic Evolutionary Search)

- **Type**: Procedural Learning System
- **Description**: Evolutionary program learning for acquiring and optimizing cognitive procedures
- **Components**: Genetic programming, procedure execution, context-goal mapping
- **Purpose**: Learn Context → Procedure → Goal schematics
- **Source**: [Learn Repository](https://github.com/opencog/learn)
- **Architecture**: Part of main [@mermaid-chart](docs/COGPRIME_ARCHITECTURE_DIAGRAM.md)
- **Status**: Research & Development

### PLN (Probabilistic Logic Networks)

- **Type**: Declarative Reasoning System
- **Description**: Uncertain reasoning and inference over knowledge in the AtomSpace
- **Components**: Logic rules, probability handling, inference control
- **Purpose**: Declarative memory processing and reasoning
- **Source**: [PLN Components](https://github.com/opencog/pln)
- **Architecture**: Part of main [@mermaid-chart](docs/COGPRIME_ARCHITECTURE_DIAGRAM.md)
- **Status**: Research & Development

### ECAN (Economic Attention Networks)

- **Type**: Attention Allocation System
- **Description**: Economic model for allocating cognitive resources via attention values
- **Components**: STI (ShortTermImportance), LTI (LongTermImportance), attention spreading
- **Purpose**: Focus cognitive processes on relevant information
- **Source**: [Attention Repository](https://github.com/opencog/attention)
- **Architecture**: Part of main [@mermaid-chart](docs/COGPRIME_ARCHITECTURE_DIAGRAM.md)
- **Status**: Research & Development

### BioscienceModels

- **Type**: Domain-Specific Knowledge Models
- **Description**: MOSES-generated models for biological aging research
- **Components**: Gene-aging relationship models, accuracy metrics, biological predicates
- **Purpose**: Demonstrate CogPrime applied to scientific discovery
- **Source**: [`Scheme/opencog-agi-bio-moses-scripts-obsolete-models*.scm`](Scheme/)
- **Status**: Historical/Experimental

### PatternMiningEngine

- **Type**: Cognitive Pattern Discovery
- **Description**: Implements the "Cognitive Equation" for recognizing and embodying patterns
- **Components**: Pattern recognition, map formation, concept creation
- **Purpose**: Discover emergent structures in the knowledge hypergraph
- **Architecture**: Part of main [@mermaid-chart](docs/COGPRIME_ARCHITECTURE_DIAGRAM.md)
- **Status**: Research & Development

### SimulationEngine

- **Type**: Episodic Memory System
- **Description**: Internal world simulation for experience replay and prediction
- **Components**: Scenario modeling, episodic traces, future projection
- **Purpose**: Episodic memory processing and imagination
- **Architecture**: Part of main [@mermaid-chart](docs/COGPRIME_ARCHITECTURE_DIAGRAM.md)
- **Status**: Research & Development

### GoalSystem

- **Type**: Intentional Memory Manager
- **Description**: Hierarchical goal representation and cognitive schematic management
- **Components**: Goal atoms, subgoal decomposition, Context→Procedure→Goal structures
- **Purpose**: Drive behavior through intentional memory
- **Architecture**: Part of main [@mermaid-chart](docs/COGPRIME_ARCHITECTURE_DIAGRAM.md)
- **Status**: Research & Development

## Model Integration Patterns

### Cognitive Synergy

The models interact dynamically to overcome individual limitations:

- **PLN ↔ MOSES**: Inference for learning, procedures for reasoning
- **ECAN ↔ All**: Attention allocation influences all cognitive processes
- **SimulationEngine → PLN/MOSES**: Simulated data enriches reasoning and learning
- **PatternMining → All**: New patterns inform all cognitive processes

### Hypergraph Substructures

Each model contributes specific atom types and link patterns:

- **Declarative**: ConceptNodes, PredicateNodes with TruthValues
- **Procedural**: SchemaNodes, ProcedureLinks with execution traces
- **Episodic**: SequentialLinks, TemporalLinks with event structures
- **Attentional**: All atoms with AttentionValues (STI/LTI)
- **Intentional**: GoalNodes, ImplicationLinks for schematics

## Cross-References

- 📊 [CogPrime Architecture Diagram](docs/COGPRIME_ARCHITECTURE_DIAGRAM.md) - Main system architecture and Eva integration
- 📖 [Main README](README.md) - Repository overview with cross-linked cognitive components
- 🎯 [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md) - Technical implementation details
- 🔄 [Contributing Guidelines](CONTRIBUTING.md) - @models documentation and @mermaid-chart standards
- 📁 [Scheme Models](Scheme/) - Source code with @models docblocks
- 📊 [Eva Self-Model Diagram](docs/COGPRIME_ARCHITECTURE_DIAGRAM.md#eva-self-model-integration) - Specialized embodiment integration

---

_This catalog follows the @models documentation pattern to foster cognitive clarity and recursive self-documentation per the CogPrime vision._
