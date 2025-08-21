# Deep Tree Echo Dashboard Guide

This guide provides detailed information about the two dashboard interfaces available in Deep Tree Echo: the GUI Dashboard and the Web Dashboard.

## Overview

Deep Tree Echo includes two complementary dashboard interfaces for system monitoring and diagnostics:

1. **GUI Dashboard** - A feature-rich desktop application with interactive visualizations
2. **Web Dashboard** - A browser-based interface for remote monitoring and diagnostics

## When to Use Each Dashboard

### GUI Dashboard
- Local development and monitoring
- Interactive exploration of echo patterns and memory graphs
- Detailed system configuration
- When full system resources are available

### Web Dashboard
- Remote monitoring and diagnostics
- During system resource constraints or stability issues
- When the GUI dashboard might be inaccessible
- For monitoring across different devices

## GUI Dashboard

### Launch

```bash
python3 fix_locale_gui.py
```

### Key Features

#### Dashboard Tab
- System summary with key metrics
- Resource usage pie charts
- At-a-glance overview of echo system status

#### System Health Tab
- Detailed CPU, memory, and disk usage monitoring
- Resource usage graphs with historical data
- System warnings and alerts

#### Activity Logs Tab
- Real-time streaming of all system activity
- Searchable log interface
- Component-specific log filtering

#### Task Management Tab
- Create and monitor system tasks
- Prioritize tasks
- Cancel or modify scheduled operations

#### Heartbeat Monitor Tab
- Real-time monitoring of system heartbeat
- Visual feedback on system rhythm
- Hyper Drive mode controls
- System health indicators

#### Echo Visualization Tab
- Interactive graph visualization of the echo tree
- Propagation controls for echo values
- Threshold adjustment sliders
- Echo pattern metrics

#### Memory Explorer Tab
- Hypergraph visualization of the memory system
- Memory node exploration
- Relationship visualization between memory nodes
- Community detection and visualization

#### Cognitive Systems Tab
- Monitoring of cognitive architecture components
- Personality system metrics
- Sensory-motor system status

### Advanced Features

- **Interactive Visualizations**: Click on nodes in the echo tree or memory graph to explore details
- **Real-time Updates**: All visualizations update in real-time to reflect system state
- **Control Panel**: Direct control over echo propagation, memory pruning, and hyper drive mode

## Web Dashboard

### Launch

```bash
python3 web_gui.py
```

The web interface will be accessible at:
- http://localhost:5000
- Any forwarded port URLs in containerized environments

### Key Features

#### Overview Tab
- System status summary
- Resource usage metrics
- Recent events at a glance
- System health chart

#### System Resources Tab
- CPU, memory, and disk usage monitoring
- Resource usage history charts
- Process list with resource utilization

#### Adaptive Heartbeat Tab
- Heartbeat rate monitoring
- Hyper drive status and controls
- System health indicators
- Heartbeat rate history visualization

#### Activity Logs Tab
- System-wide log viewing
- Component-specific log filtering
- Search functionality

#### Network Tab
- Network status monitoring
- Traffic visualization
- Connection tracking

#### Configuration Tab
- Basic system configuration options
- Parameter adjustments
- Settings for heartbeat thresholds

### Advanced Features

- **Remote Access**: Access from any device with a web browser
- **Low Resource Mode**: Continues functioning even during high system load
- **Persistent Monitoring**: Maintains monitoring even when other system components are strained

## Feature Comparison

| Feature | GUI Dashboard | Web Dashboard |
|---------|--------------|--------------|
| Interface | Desktop application | Browser-based |
| Accessibility | Local machine | Any device with web access |
| Visualization Richness | High (interactive) | Medium (static with refresh) |
| Resource Usage | Moderate to high | Low |
| Real-time Updates | Continuous | Periodic refresh |
| Direct System Control | Comprehensive | Basic controls |
| Resilience to System Issues | Moderate | High |
| Echo Visualization | Interactive tree | Static chart |
| Memory Visualization | Interactive hypergraph | Static network graph |
| Heartbeat Control | Full control panel | Basic controls |
| Custom Configurations | Advanced options | Basic adjustments |

## Troubleshooting

### GUI Dashboard Issues

- **Locale Errors**: The `fix_locale_gui.py` script addresses common locale issues in container environments
- **Display Issues**: Ensure X11 forwarding is properly configured if running remotely
- **High CPU Usage**: Reduce update frequency in the Settings tab if system resources are constrained

### Web Dashboard Issues

- **Connection Issues**: Verify the correct port and URL, especially in containerized environments
- **Chart Loading**: If charts fail to load, try refreshing the page or reducing the data range
- **Authentication**: For deployments outside containers, consider enabling basic authentication

## Best Practices

1. **Run Both Dashboards**: For critical monitoring, run both dashboards for redundancy
2. **Regular Log Review**: Check activity logs periodically for warning signs of system issues
3. **Resource Monitoring**: Keep an eye on resource usage, especially during intensive operations
4. **Heartbeat Awareness**: The adaptive heartbeat system helps manage resource usage - pay attention to its indicators

## Advanced Usage

### Programmatic Interaction with Dashboards

Both dashboards expose APIs that can be used programmatically:

```python
# GUI Dashboard - Inject a random echo
from gui_dashboard import GUIDashboard
dashboard = GUIDashboard.get_instance()
dashboard.inject_random_echo()

# Web Dashboard - Get system metrics
import requests
response = requests.get('http://localhost:5000/api/system_metrics')
metrics = response.json()
print(metrics)
```

### Custom Dashboard Deployments

For production environments, consider:

- Configuring the web dashboard behind a reverse proxy
- Adding authentication for the web interface
- Customizing update intervals based on system capabilities
- Enabling email alerts for critical system events

## Conclusion

The dual dashboard approach provides robust monitoring and diagnostic capabilities for the Deep Tree Echo system. The GUI dashboard offers rich interaction for local development, while the web dashboard ensures access even during system issues or for remote monitoring.