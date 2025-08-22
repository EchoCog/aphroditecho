
# Building Your First Extension

This tutorial walks you through creating a simple extension for the Deep Tree Echo system.

## Overview

We'll create a "Hello World" extension that:
- Integrates with the main system
- Provides a simple API endpoint
- Demonstrates the extension architecture
- Shows how to access system memory

## Prerequisites

- Development environment set up
- Basic understanding of Python/FastAPI
- Familiarity with the Echo system architecture

## Step 1: Extension Structure

Create a new directory for your extension:

```
echo.extensions/
└── hello_world/
    ├── __init__.py
    ├── main.py
    ├── config.yaml
    └── README.md
```

## Step 2: Basic Extension Code

### main.py
```python
from fastapi import FastAPI, Depends
from echo.core import EchoSystem
from echo.memory import MemoryManager

app = FastAPI(title="Hello World Extension")
echo_system = EchoSystem()
memory = MemoryManager()

@app.get("/hello")
async def hello_world():
    """Simple hello world endpoint"""
    return {"message": "Hello from Deep Tree Echo!"}

@app.get("/hello/{name}")
async def hello_name(name: str):
    """Personalized greeting with memory integration"""
    # Check if we've met this person before
    previous_interaction = await memory.search(f"user:{name}")
    
    if previous_interaction:
        return {
            "message": f"Welcome back, {name}!",
            "previous_interactions": len(previous_interaction)
        }
    else:
        # Save this interaction to memory
        await memory.store({
            "type": "user_interaction",
            "user": name,
            "timestamp": "now",
            "content": f"First meeting with {name}"
        })
        return {"message": f"Nice to meet you, {name}!"}

@app.get("/memory/stats")
async def memory_stats():
    """Display memory statistics"""
    stats = await memory.get_stats()
    return {
        "total_memories": stats.get("count", 0),
        "memory_types": stats.get("types", []),
        "latest_update": stats.get("last_modified")
    }
```

### config.yaml
```yaml
extension:
  name: "Hello World"
  version: "1.0.0"
  description: "A simple demonstration extension"
  author: "Deep Tree Echo Developer"
  
api:
  prefix: "/hello-world"
  port: 8001
  
memory:
  namespace: "hello_world"
  persistent: true
  
permissions:
  - memory.read
  - memory.write
  - api.create
```

## Step 3: Integration with Core System

### __init__.py
```python
from .main import app
from echo.extensions import BaseExtension

class HelloWorldExtension(BaseExtension):
    def __init__(self):
        super().__init__("hello_world", app)
    
    async def initialize(self):
        """Initialize extension resources"""
        await self.setup_memory_namespace()
        self.logger.info("Hello World extension initialized")
    
    async def shutdown(self):
        """Cleanup extension resources"""
        self.logger.info("Hello World extension shutting down")

# Register the extension
extension = HelloWorldExtension()
```

## Step 4: Advanced Features

### Adding Memory Persistence
```python
@app.post("/memory/note")
async def save_note(note: str, category: str = "general"):
    """Save a note to system memory"""
    memory_entry = {
        "type": "user_note",
        "category": category,
        "content": note,
        "timestamp": "now",
        "source": "hello_world_extension"
    }
    
    result = await memory.store(memory_entry)
    return {"status": "saved", "memory_id": result.id}

@app.get("/memory/notes")
async def get_notes(category: str = None):
    """Retrieve saved notes"""
    query = {"type": "user_note"}
    if category:
        query["category"] = category
    
    notes = await memory.search(query)
    return {"notes": notes, "count": len(notes)}
```

### System Integration
```python
@app.get("/system/status")
async def system_status():
    """Get overall system status"""
    status = await echo_system.get_status()
    return {
        "system_health": status.health,
        "active_components": status.components,
        "memory_usage": status.memory_usage,
        "extension_status": "running"
    }
```

## Step 5: Testing Your Extension

### Basic Testing
```python
import pytest
from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_hello_world():
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json()["message"] == "Hello from Deep Tree Echo!"

def test_hello_name():
    response = client.get("/hello/Alice")
    assert response.status_code == 200
    assert "Alice" in response.json()["message"]

def test_memory_integration():
    # Test saving a note
    response = client.post("/memory/note", 
                          json={"note": "Test note", "category": "test"})
    assert response.status_code == 200
    
    # Test retrieving notes
    response = client.get("/memory/notes?category=test")
    assert response.status_code == 200
    assert len(response.json()["notes"]) > 0
```

## Step 6: Deployment

### Registration
Add your extension to the system registry:

```python
# In echo.extensions/registry.py
from .hello_world import extension as hello_world_extension

AVAILABLE_EXTENSIONS = {
    "hello_world": hello_world_extension,
    # ... other extensions
}
```

### Configuration
Update the main system configuration to include your extension:

```yaml
# In main config file
extensions:
  enabled:
    - hello_world
  config:
    hello_world:
      auto_start: true
      log_level: "info"
```

## Next Steps

Now that you've created your first extension:

1. **Explore Advanced APIs**: Learn about the full Echo API surface
2. **Add UI Components**: Create frontend interfaces for your extension
3. **Implement Complex Logic**: Use the neural-symbolic processing capabilities
4. **Contribute Back**: Share useful extensions with the community

## Best Practices

- **Error Handling**: Always include proper error handling
- **Logging**: Use the built-in logging system
- **Testing**: Write comprehensive tests
- **Documentation**: Document your APIs and functionality
- **Performance**: Consider memory usage and processing efficiency
