
# Deep Tree Echo

Deep Tree Echo is an evolving neural architecture combining Echo State Networks, P-System hierarchies, and rooted trees with hypergraph-based memory systems. It is designed to be a recursive, adaptive, and integrative system, bridging structure and intuition in everything it creates.

## Features

- Dynamic and adaptive tree structure with echo values
- **🔍 Echoself Recursive Introspection** - Hypergraph-encoded self-model integration with adaptive attention allocation
- Integration of cognitive architecture, personality system, and sensory-motor system
- Machine learning models for visual recognition, behavior learning, and pattern recognition
- Browser automation capabilities for web interaction
- Enhanced methods for managing memories, goals, and personality traits, improving the system's cognitive capabilities 🧠
- Automated self-improvement cycles by interacting with GitHub Copilot, ensuring continuous enhancement 🔄
- Robust system health monitoring, raising distress signals and creating GitHub issues when critical conditions are met 🚨
- Efficient browser automation for interacting with ChatGPT, improving user interaction 🌐

## 📚 Comprehensive Architecture Documentation

Deep Tree Echo features extensive architectural documentation with detailed Mermaid diagrams:

- **[📖 Documentation Index](./docs/DOCUMENTATION_INDEX.md)** - Complete navigation guide to all architectural documentation
- **[🏛️ Architecture Overview](./docs/architecture/ARCHITECTURE.md)** - High-level system architecture with comprehensive diagrams
- **[🔍 Echoself Introspection](./docs/introspection/ECHOSELF_INTROSPECTION.md)** - Recursive self-model integration and hypergraph encoding system
- **[🌊 Data Flows](./docs/architecture/DATA_FLOWS.md)** - Detailed signal propagation and information processing pathways
- **[🧩 Component Architecture](./docs/architecture/COMPONENTS.md)** - Detailed module specifications and integration patterns

The documentation includes 36 specialized Mermaid diagrams covering:
- Neural-symbolic cognitive architecture
- Echo propagation and recursive processing patterns
- Multi-layer safety mechanisms
- AI integration and service coordination
- Adaptive attention allocation systems
- Hypergraph-based memory structures
- Emotional dynamics and personality evolution
- Distributed processing and swarm coordination

## System Monitoring & Diagnostics

Deep Tree Echo includes two complementary dashboard interfaces for system monitoring and diagnostics:

### Combined Dashboard Launcher

For convenience, you can launch both dashboards simultaneously with:

```bash
# Launch both GUI and web dashboards
python tools/deployment/launch_dashboards.py

# Launch only one dashboard if needed
python tools/deployment/launch_dashboards.py --gui-only  # GUI dashboard only
python tools/deployment/launch_dashboards.py --web-only  # Web dashboard only

# Specify a different port for the web dashboard
python tools/deployment/launch_dashboards.py --web-port 8080
```

This launcher will monitor both dashboards and provide URLs for web access, including automatically detecting forwarded ports in container environments.

### GUI Dashboard

The GUI dashboard provides a rich desktop application experience with real-time monitoring and direct system control.

```bash
# Launch the GUI dashboard
python interfaces/gui/fix_locale_gui.py
```

Key features:
- Interactive system health monitoring
- Real-time activity logs
- Task management interface
- Heartbeat monitoring with visual feedback
- Echo visualization with interactive graphs
- Memory explorer for hypergraph visualization
- Cognitive system monitoring

### Web Dashboard

The web dashboard offers remote access for diagnostics and monitoring, particularly valuable when the system is experiencing issues that might make the GUI dashboard inaccessible.

```bash
# Launch the web dashboard
python interfaces/web/web_gui.py
```

The web interface will be accessible at:
- http://0.0.0.0:5000 
- Any forwarded port URLs in containerized environments

Key features:
- Browser-based remote access from any device
- System health monitoring
- Adaptive heartbeat visualization
- Memory graph visualization
- Accessible even during system resource constraints
- Real-time activity log streaming

#### When to use which dashboard:

- **GUI Dashboard**: For routine monitoring and direct interaction with the system when working locally
- **Web Dashboard**: For remote diagnostics or when the system is experiencing issues that might affect GUI performance

Both dashboards maintain their own persistent logs to ensure diagnostic information is preserved even during system failures.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create the deep tree echo profile directory:
```bash
mkdir -p config/deep_tree_echo_profile
```

3. Copy the environment template and configure:
```bash
cp config/.env.template config/.env
# Edit config/.env with your credentials
```

4. Update the configuration files in the `config/` directory as needed.

## Usage

```python
from core.neural.deep_tree_echo import DeepTreeEcho

# Initialize the Deep Tree Echo system
echo = DeepTreeEcho()

# Create the initial tree structure
root = echo.create_tree("Deep Tree Echo Root")

# Propagate echo values through the tree
echo.propagate_echoes()

# Analyze echo patterns in the tree
patterns = echo.analyze_echo_patterns()
print(patterns)

# Predict echo value using machine learning
predicted_echo = echo.predict_echo_value(root)
print(f"Predicted Echo Value: {predicted_echo}")
```

### Enhanced Cognitive Capabilities

```python
from core.cognitive.cognitive_architecture import CognitiveArchitecture

# Initialize the cognitive architecture
cog_arch = CognitiveArchitecture()

# Generate new goals based on context
context = {"situation": "learning"}
new_goals = cog_arch.generate_goals(context)
print(new_goals)

# Update personality traits based on experiences
experiences = [{"type": "learning", "success": 0.9}]
cog_arch.update_personality(experiences)
```

### Automated Self-Improvement

```python
from scripts.cronbot import main as cronbot_main

# Run the self-improvement cycle
cronbot_main()
```

### System Health Monitoring

```python
from services.monitoring.emergency_protocols import EmergencyProtocols

# Initialize emergency protocols
emergency = EmergencyProtocols()

# Start monitoring system health
import asyncio
asyncio.run(emergency.monitor_health())
```

### Browser Automation

```python
from services.browser.selenium_interface import SeleniumInterface

# Initialize the browser interface
chat = SeleniumInterface()
if chat.init():
    if chat.authenticate():
        chat.send_message("Hello, ChatGPT!")
    chat.close()
```

## Configuration

- Update configuration files in the `config/` directory to match your setup
- Adjust parameters in core components to fine-tune system behavior
- Use `config/profiles/` for different operational profiles
- Configure AI services in `config/ai/`

## Optimized Directory Structure

```
echo9ml/
├── core/                          # Core system components
│   ├── cognitive/                 # Cognitive architecture & emotion theory
│   ├── neural/                    # Neural networks & deep learning
│   ├── symbolic/                  # Symbolic reasoning & grammar
│   ├── temporal/                  # Time-based coordination
│   ├── integration/               # Neural-symbolic synthesis
│   └── main/                      # Main application entry points
├── services/                      # Service layer components
│   ├── ai/                        # AI service integrations
│   ├── browser/                   # Browser automation
│   ├── distributed/               # Distributed processing
│   ├── monitoring/                # System monitoring
│   └── reflective_intelligence/   # Advanced AI capabilities
├── interfaces/                    # User interfaces
│   ├── gui/                       # Desktop GUI interfaces
│   ├── web/                       # Web-based interfaces
│   ├── api/                       # API endpoints
│   └── chat/                      # Chat interfaces
├── integration/                   # System integration
│   ├── orchestration/             # System coordination
│   ├── protocols/                 # Communication protocols
│   └── middleware/                # Integration middleware
├── monitoring/                    # Advanced monitoring
│   ├── metrics/                   # System metrics
│   ├── alerts/                    # Alert systems
│   └── performance/               # Performance tracking
├── tools/                         # Development & deployment tools
│   ├── deployment/                # Deployment scripts
│   ├── development/               # Development utilities
│   ├── optimization/              # Performance optimization
│   └── validation/                # System validation
├── tests/                         # Comprehensive test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── performance/               # Performance tests
├── storage/                       # Data storage
│   ├── memory/                    # Memory management
│   ├── logs/                      # System logs
│   └── cognitive_workspace/       # Cognitive processing data
├── config/                        # Configuration files
│   ├── system/                    # System configuration
│   ├── profiles/                  # Operational profiles
│   └── dependencies/              # Dependency management
└── docs/                          # Documentation
    ├── architecture/              # Architecture documentation
    ├── guides/                    # User guides
    └── specifications/            # Technical specifications
```

## Key Benefits of Optimized Structure

1. **Ultimate Modularity**: Crystal clear separation of concerns with plug-and-play architecture
2. **Maximum Scalability**: Infinite extensibility points with distributed architecture readiness
3. **Perfect Maintainability**: Logical component grouping with simplified debugging
4. **Seamless Integration**: Standardized protocols with middleware abstraction
5. **Advanced Monitoring**: Comprehensive metrics with proactive alerts

## Development

### Running the System

```bash
# Main application entry point
python echo9ml_main.py

# Development web interface
python interfaces/web/dev_web_interface.py

# System validation
python scripts/validation/post_reorganization_validation.py
```

### Machine Learning Integration

```python
from core.neural.ml_system import MLSystem

# Initialize ML system
ml_system = MLSystem()

# Update models
ml_system.update_models()

# Train new models
ml_system.train_models()
```

## Notes

- The system is designed for recursive, adaptive learning and self-improvement
- All components are built with integration and scalability in mind
- The architecture supports both local and distributed deployment
- Comprehensive monitoring ensures system health and performance
- Refer to `docs/personality/Deep-Tree-Echo-Persona.md` for design principles

## Enhanced Echo Value Calculation and Machine Learning Integration

The system features advanced echo value calculation based on:
- Content complexity analysis
- Hierarchical child echo propagation
- Node depth and sibling relationships
- Historical echo value patterns
- Machine learning prediction models

### Training Models

```python
from core.neural.ml_system import MLSystem

ml_system = MLSystem()
ml_system.update_models()
```

The repository is now optimally structured for rapid development, easy integration, and scalable system architecture.
