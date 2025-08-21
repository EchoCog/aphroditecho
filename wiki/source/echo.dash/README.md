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

- **[📖 Documentation Index](./DOCUMENTATION_INDEX.md)** - Complete navigation guide to all architectural documentation
- **[🏛️ Architecture Overview](./ARCHITECTURE.md)** - High-level system architecture with comprehensive diagrams
- **[🔍 Echoself Introspection](./ECHOSELF_INTROSPECTION.md)** - Recursive self-model integration and hypergraph encoding system
- **[🌊 Data Flows](./DATA_FLOWS.md)** - Detailed signal propagation and information processing pathways
- **[🧩 Component Architecture](./COMPONENTS.md)** - Detailed module specifications and integration patterns

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
./launch_dashboards.py

# Launch only one dashboard if needed
./launch_dashboards.py --gui-only  # GUI dashboard only
./launch_dashboards.py --web-only  # Web dashboard only

# Specify a different port for the web dashboard
./launch_dashboards.py --web-port 8080
```

This launcher will monitor both dashboards and provide URLs for web access, including automatically detecting forwarded ports in container environments.

### GUI Dashboard

The GUI dashboard provides a rich desktop application experience with real-time monitoring and direct system control.

```bash
# Launch the GUI dashboard
python3 fix_locale_gui.py
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
python3 web_gui.py
```

The web interface will be accessible at:
- http://localhost:5000 
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

2. Create the `deep_tree_echo_profile` directory in the root of the repository:
```bash
mkdir deep_tree_echo_profile
```

3. Copy `.env.template` to `.env` and fill in your credentials:
```bash
cp .env.template .env
```

4. Update the configuration files in the `deep_tree_echo_profile` directory as needed.

## Usage

```python
from deep_tree_echo import DeepTreeEcho

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

### New Features Usage Examples

#### Enhanced Cognitive Capabilities

```python
from cognitive_architecture import CognitiveArchitecture

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

#### Automated Self-Improvement

```python
import cronbot

# Run the self-improvement cycle
cronbot.main()
```

#### System Health Monitoring

```python
from emergency_protocols import EmergencyProtocols

# Initialize emergency protocols
emergency = EmergencyProtocols()

# Start monitoring system health
import asyncio
asyncio.run(emergency.monitor_health())
```

#### Browser Automation for ChatGPT

```python
from selenium_interface import SeleniumInterface

# Initialize the browser interface
chat = SeleniumInterface()
if chat.init():
    if chat.authenticate():
        chat.send_message("Hello, ChatGPT!")
    chat.close()
```

## Configuration

- Update the configuration files in the `deep_tree_echo_profile` directory to match your setup.
- Adjust the parameters in `deep_tree_echo.py` to fine-tune the echo propagation and analysis.

## Directory Structure

```
deep_tree_echo/
├── deep_tree_echo.py
├── launch_deep_tree_echo.py
├── ml_system.py
├── selenium_interface.py
├── deep_tree_echo_profile/
│   ├── activity-stream.discovery_stream.json
│   ├── addonStartup.json.lz4
│   ├── broadcast-listeners.json
│   ├── cache2/
│   ├── compatibility.ini
│   ├── containers.json
│   ├── content-prefs.sqlite
│   ├── cookies.sqlite
│   ├── datareporting/
│   ├── extension-preferences.json
│   ├── extensions.json
│   ├── favicons.sqlite
│   ├── formhistory.sqlite
│   ├── handlers.json
│   ├── permissions.sqlite
│   ├── places.sqlite
│   ├── prefs.js
│   ├── search.json.mozlz4
│   ├── sessionstore-backups/
│   ├── shader-cache/
│   ├── storage/
│   ├── times.json
│   ├── webappsstore.sqlite
│   ├── xulstore.json
```

## Notes

- Ensure that the `deep_tree_echo_profile` directory contains all necessary files and configurations for Deep Tree Echo's operation.
- Refer to the `Deep-Tree-Echo-Persona.md` file for design principles and persona details.

## Enhanced Echo Value Calculation and Machine Learning Integration

The `DeepTreeEcho` class has been enhanced to calculate echo values based on content length, complexity, child echoes, node depth, sibling nodes, and historical echo values. Additionally, machine learning models are now integrated to predict echo values.

### Setup

1. Ensure you have followed the initial setup steps mentioned above.

2. Train the machine learning models:
```python
from ml_system import MLSystem

ml_system = MLSystem()
ml_system.update_models()
```

3. Update the `deep_tree_echo.py` file to use the machine learning models for echo value prediction.

### Usage

```python
from deep_tree_echo import DeepTreeEcho

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

### Configuration

- Update the configuration files in the `deep_tree_echo_profile` directory to match your setup.
- Adjust the parameters in `deep_tree_echo.py` to fine-tune the echo propagation, analysis, and machine learning integration.
