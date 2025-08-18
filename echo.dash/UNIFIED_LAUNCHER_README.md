# Unified Launcher for Deep Tree Echo

This document describes the unified launcher system that consolidates the multiple launch scripts in the Deep Tree Echo project.

## Overview

The unified launcher system addresses the architecture gap of having multiple launch scripts by providing a single, configurable backend that all launch scripts can use. This reduces code duplication while maintaining backward compatibility.

## Components

### Core Module
- `unified_launcher.py` - The main unified launcher implementation

### Launch Scripts (Updated to use unified launcher)
- `launch_deep_tree_echo.py` - Main async system launcher
- `launch_dashboards.py` - Dashboard process manager  
- `launch_gui.py` - Comprehensive GUI launcher
- `launch_gui_standalone.py` - Simplified GUI launcher

## Usage

All existing launch scripts continue to work with their original command-line interfaces:

```bash
# Launch Deep Tree Echo with GUI and browser
python launch_deep_tree_echo.py --gui --browser --debug

# Launch both dashboards
python launch_dashboards.py --web-port 8080 --gui-port 5000

# Launch GUI dashboard only
python launch_gui.py --debug --no-activity

# Launch standalone GUI
python launch_gui_standalone.py --no-activity
```

## Unified Launcher Modes

The unified launcher supports the following modes:

1. **deep-tree-echo** - Full async system with all components
2. **gui** - GUI dashboard with full component initialization  
3. **gui-standalone** - Simplified GUI with minimal dependencies
4. **web** - Web dashboard only
5. **dashboards** - Process manager for multiple dashboards

## Configuration

The `LauncherConfig` class provides a unified configuration interface:

```python
from unified_launcher import LauncherConfig, LaunchMode

config = LauncherConfig(
    mode=LaunchMode.DEEP_TREE_ECHO,
    debug=True,
    gui=True,
    browser=True,
    storage_dir="custom_storage"
)
```

## Benefits

✅ **Code Consolidation**: Reduced from 943 lines across 4 scripts to 671 total lines
✅ **Unified Configuration**: Single configuration system for all launch modes  
✅ **Consistent Error Handling**: Standardized logging and error management
✅ **Backward Compatibility**: All existing scripts work unchanged
✅ **Maintainability**: Single source of truth for launch logic
✅ **Extensibility**: Easy to add new launch modes

## Testing

Run the test suite to verify functionality:

```bash
python test_unified_launcher.py
```

## Architecture

The unified launcher uses a strategy pattern with different launch modes:

```
unified_launcher.py
├── LauncherConfig (configuration)
├── UnifiedLauncher (main class)
├── LaunchMode (enum of available modes)
└── Mode-specific launch methods
    ├── _launch_deep_tree_echo()
    ├── _launch_gui_dashboard()
    ├── _launch_web_dashboard()
    └── _launch_dashboard_manager()
```

Each existing launch script now acts as a thin wrapper that:
1. Parses command-line arguments using the unified parser
2. Creates a configuration object
3. Delegates to the unified launcher

This approach maintains the original interfaces while eliminating code duplication and providing a foundation for future enhancements.