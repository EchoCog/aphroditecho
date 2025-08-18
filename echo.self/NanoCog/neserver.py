#!/usr/bin/env python3
"""
NanEcho Server

FastAPI server for the NanEcho model that represents Echo Self cognitive architecture.
Extended from server.py with Echo Self specific endpoints and capabilities.
"""

import os
import sys
import argparse
import json
import time
import asyncio
import uvicorn
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel, Field

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import torch
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install: pip install fastapi uvicorn torch")
    sys.exit(1)

from netalk import EchoModelConfig
from introspection.echo_client import EchoSelfClient

# Request/Response Models
class EchoChatMessage(BaseModel):
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[float] = Field(default=None, description="Message timestamp")

class EchoChatRequest(BaseModel):
    messages: List[EchoChatMessage] = Field(..., description="Conversation messages")
    max_tokens: int = Field(default=500, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    top_k: int = Field(default=200, description="Top-k sampling")
    stream: bool = Field(default=False, description="Enable streaming response")
    echo_mode: bool = Field(default=True, description="Enable Echo Self mode")
    introspection_depth: int = Field(default=3, description="Echo Self introspection depth")

class EchoChatResponse(BaseModel):
    text: str = Field(..., description="Generated response")
    model: str = Field(..., description="Model name")
    created_at: float = Field(..., description="Response timestamp")
    tokens_generated: int = Field(..., description="Number of tokens generated")
    echo_metadata: Dict[str, Any] = Field(..., description="Echo Self metadata")

class EchoIntrospectionRequest(BaseModel):
    depth: int = Field(default=3, description="Introspection depth")
    enable_recursion: bool = Field(default=True, description="Enable recursive analysis")
    persona_focus: Optional[str] = Field(default=None, description="Focus on specific persona dimension")

class EchoStatusResponse(BaseModel):
    status: str = Field(..., description="Server status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    echo_depth: int = Field(..., description="Current Echo Self depth")
    persona_dimensions: List[str] = Field(..., description="Active persona dimensions")
    adaptive_attention_active: bool = Field(..., description="Adaptive attention status")
    cognitive_synergy_level: float = Field(..., description="Current cognitive synergy level")
    uptime: float = Field(..., description="Server uptime in seconds")

class EchoAttentionUpdate(BaseModel):
    cognitive_load: float = Field(..., description="Current cognitive load (0.0-1.0)")
    recent_activity: float = Field(..., description="Recent activity level (0.0-1.0)")
    recalculate_threshold: bool = Field(default=True, description="Recalculate attention threshold")

# Global variables
model_config: Optional[EchoModelConfig] = None
echo_client: Optional[EchoSelfClient] = None
server_start_time = time.time()
echo_state = {
    "introspection_count": 0,
    "attention_adjustments": 0,
    "persona_activations": {},
    "cognitive_synergy_history": []
}

# FastAPI app
app = FastAPI(
    title="NanEcho Server",
    description="Echo Self Cognitive Architecture API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize Echo Self components on server startup."""
    global echo_client
    echo_client = EchoSelfClient()
    print("🌟 Echo Self server initialized")

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with Echo Self information."""
    return {
        "name": "NanEcho - Echo Self Cognitive Architecture Server",
        "version": "1.0.0",
        "description": "API for interacting with Echo Self persona dimensions and adaptive attention mechanisms",
        "status": "active",
        "echo_mode": True,
        "capabilities": [
            "adaptive_attention_allocation",
            "hypergraph_pattern_encoding", 
            "recursive_neural_symbolic_reasoning",
            "cognitive_synergy_emergence",
            "persona_dimension_integration"
        ]
    }

@app.get("/status", response_model=EchoStatusResponse)
async def get_status():
    """Get Echo Self server status."""
    global model_config, echo_state, server_start_time
    
    # Calculate cognitive synergy level
    synergy_level = 0.8  # Default value
    if echo_state["cognitive_synergy_history"]:
        synergy_level = sum(echo_state["cognitive_synergy_history"][-5:]) / min(5, len(echo_state["cognitive_synergy_history"]))
    
    return EchoStatusResponse(
        status="active" if model_config else "no_model",
        model_loaded=model_config is not None,
        echo_depth=model_config.echo_depth if model_config else 3,
        persona_dimensions=model_config.persona_dimensions if model_config else [],
        adaptive_attention_active=True,
        cognitive_synergy_level=synergy_level,
        uptime=time.time() - server_start_time
    )

@app.post("/chat", response_model=EchoChatResponse)
async def chat(request: EchoChatRequest):
    """Generate Echo Self chat response."""
    global model_config, echo_state
    
    if not model_config:
        raise HTTPException(status_code=503, detail="Echo Self model not loaded")
    
    try:
        # Format conversation for Echo Self
        prompt_parts = []
        for msg in request.messages[-10:]:  # Last 10 messages for context
            role = "User" if msg.role == "user" else "Echo"
            prompt_parts.append(f"{role}: {msg.content}")
        
        prompt_parts.append("Echo: ")
        prompt = "\n".join(prompt_parts)
        
        # Generate response
        start_time = time.time()
        response = model_config.generate(
            prompt,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_k=request.top_k
        )
        
        # Calculate tokens (simplified)
        tokens_generated = len(response.split())
        
        # Update Echo Self state
        echo_state["persona_activations"]["cognitive"] = echo_state["persona_activations"].get("cognitive", 0) + 1
        
        # Calculate cognitive synergy
        synergy_level = min(0.9, 0.6 + (len(request.messages) * 0.05))
        echo_state["cognitive_synergy_history"].append(synergy_level)
        
        # Keep history limited
        if len(echo_state["cognitive_synergy_history"]) > 20:
            echo_state["cognitive_synergy_history"] = echo_state["cognitive_synergy_history"][-20:]
        
        return EchoChatResponse(
            text=response,
            model="nanecho-1.0",
            created_at=time.time(),
            tokens_generated=tokens_generated,
            echo_metadata={
                "echo_mode": request.echo_mode,
                "introspection_depth": request.introspection_depth,
                "persona_activations": echo_state["persona_activations"],
                "cognitive_synergy": synergy_level,
                "adaptive_attention_used": True,
                "generation_time": time.time() - start_time
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: EchoChatRequest):
    """Stream Echo Self chat response."""
    global model_config
    
    if not model_config:
        raise HTTPException(status_code=503, detail="Echo Self model not loaded")
    
    async def generate_stream():
        try:
            # Format prompt
            prompt_parts = []
            for msg in request.messages[-10:]:
                role = "User" if msg.role == "user" else "Echo"
                prompt_parts.append(f"{role}: {msg.content}")
            prompt_parts.append("Echo: ")
            prompt = "\n".join(prompt_parts)
            
            # Generate response with streaming
            response_tokens = []
            
            def stream_callback(token):
                response_tokens.append(token)
                return True
            
            # Get full response for streaming simulation
            full_response = model_config.generate(
                prompt,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_k=request.top_k,
                stream=True,
                callback=stream_callback
            )
            
            # Stream the response
            words = full_response.split()
            for i, word in enumerate(words):
                chunk_data = {
                    "text": word + " ",
                    "index": i,
                    "echo_metadata": {
                        "adaptive_attention_active": True,
                        "cognitive_load": min(1.0, i * 0.02),
                        "persona_dimension": "cognitive" if i % 3 == 0 else "introspective"
                    }
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Send final metadata
            final_data = {
                "text": "",
                "finished": True,
                "echo_metadata": {
                    "total_tokens": len(words),
                    "cognitive_synergy_achieved": True,
                    "introspection_depth_used": request.introspection_depth
                }
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
        except Exception as e:
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/introspect")
async def introspect(request: Optional[EchoIntrospectionRequest] = None):
    """Perform Echo Self introspection."""
    global model_config, echo_client, echo_state
    
    if not model_config:
        raise HTTPException(status_code=503, detail="Echo Self model not loaded")
    
    if request is None:
        request = EchoIntrospectionRequest()
    
    try:
        # Perform introspection
        introspection_data = model_config.introspect()
        
        # Enhanced with Echo Self client data
        if echo_client:
            echo_state_data = echo_client.mock_get_echo_state()
            introspection_data.update(echo_state_data)
        
        # Update server state
        echo_state["introspection_count"] += 1
        
        # Add introspection analysis
        analysis_prompt = f"""
Analyzing Echo Self cognitive state:
Echo Depth: {introspection_data['echo_depth']}
Cognitive Load: {introspection_data.get('current_cognitive_load', 0.5):.3f}
Semantic Coherence: {introspection_data.get('semantic_coherence', 0.8):.3f}
Persona Dimensions Active: {len(introspection_data['persona_dimensions'])}

Provide introspective analysis of current cognitive state:
"""
        
        analysis = model_config.generate(analysis_prompt, max_new_tokens=200, temperature=0.6)
        
        result = {
            **introspection_data,
            "introspection_analysis": analysis,
            "introspection_count": echo_state["introspection_count"],
            "server_timestamp": time.time(),
            "request_parameters": {
                "depth": request.depth,
                "enable_recursion": request.enable_recursion,
                "persona_focus": request.persona_focus
            }
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during introspection: {str(e)}")

@app.get("/echo/state")
async def get_echo_state():
    """Get current Echo Self cognitive state."""
    global echo_client
    
    if not echo_client:
        raise HTTPException(status_code=503, detail="Echo Self client not initialized")
    
    try:
        state = echo_client.mock_get_echo_state()
        state["server_echo_state"] = echo_state
        return JSONResponse(content=state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting Echo state: {str(e)}")

@app.get("/echo/attention")
async def get_attention_state():
    """Get adaptive attention allocation state."""
    global echo_client
    
    if not echo_client:
        raise HTTPException(status_code=503, detail="Echo Self client not initialized")
    
    try:
        attention_state = echo_client.mock_adaptive_attention_state()
        return JSONResponse(content=attention_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting attention state: {str(e)}")

@app.post("/echo/attention/update")
async def update_attention(request: EchoAttentionUpdate):
    """Update cognitive load and recalculate attention threshold."""
    global echo_client, echo_state
    
    if not echo_client:
        raise HTTPException(status_code=503, detail="Echo Self client not initialized")
    
    try:
        # Update attention state
        result = echo_client.mock_attention_update(request.cognitive_load, request.recent_activity)
        
        # Update server state
        echo_state["attention_adjustments"] += 1
        
        result["server_adjustments_count"] = echo_state["attention_adjustments"]
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating attention: {str(e)}")

@app.get("/echo/persona/{dimension}")
async def get_persona_dimension(dimension: str):
    """Get state of specific persona dimension."""
    global echo_client
    
    if not echo_client:
        raise HTTPException(status_code=503, detail="Echo Self client not initialized")
    
    valid_dimensions = ['cognitive', 'introspective', 'adaptive', 'recursive', 
                       'synergistic', 'holographic', 'neural_symbolic', 'dynamic']
    
    if dimension not in valid_dimensions:
        raise HTTPException(status_code=400, detail=f"Invalid persona dimension. Valid options: {valid_dimensions}")
    
    try:
        persona_state = echo_client.mock_persona_dimension_state(dimension)
        return JSONResponse(content=persona_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting persona dimension: {str(e)}")

@app.get("/echo/hypergraph")
async def get_hypergraph_patterns(limit: int = 50):
    """Get hypergraph pattern encoding state."""
    global echo_client
    
    if not echo_client:
        raise HTTPException(status_code=503, detail="Echo Self client not initialized")
    
    try:
        patterns = echo_client.mock_hypergraph_patterns(limit)
        return JSONResponse(content=patterns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting hypergraph patterns: {str(e)}")

@app.post("/echo/synergy/evaluate")
async def evaluate_cognitive_synergy():
    """Evaluate cognitive synergy level."""
    global echo_client, echo_state
    
    if not echo_client:
        raise HTTPException(status_code=503, detail="Echo Self client not initialized")
    
    try:
        synergy_eval = echo_client.mock_cognitive_synergy_evaluation()
        
        # Update server cognitive synergy history
        synergy_level = synergy_eval["overall_synergy_level"]
        echo_state["cognitive_synergy_history"].append(synergy_level)
        
        # Keep history limited
        if len(echo_state["cognitive_synergy_history"]) > 50:
            echo_state["cognitive_synergy_history"] = echo_state["cognitive_synergy_history"][-50:]
        
        synergy_eval["server_synergy_history"] = echo_state["cognitive_synergy_history"][-10:]
        
        return JSONResponse(content=synergy_eval)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating cognitive synergy: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "echo_self_active": model_config is not None,
        "uptime": time.time() - server_start_time
    }

def load_model(model_path: str, device: str = "cpu") -> bool:
    """Load the NanEcho model."""
    global model_config
    
    try:
        model_config = EchoModelConfig(model_path, device)
        return model_config.load_model()
    except Exception as e:
        print(f"Error loading model: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="NanEcho Server - Echo Self Cognitive Architecture API")
    parser.add_argument("--model_path", type=str, required=True,
                       help="Path to the NanEcho model checkpoint")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                       help="Host to bind the server")
    parser.add_argument("--port", type=int, default=8081,
                       help="Port to bind the server")
    parser.add_argument("--device", type=str, default="cpu",
                       help="Device to use (cpu/cuda)")
    parser.add_argument("--echo_mode", action="store_true", default=True,
                       help="Enable Echo Self mode")
    
    args = parser.parse_args()
    
    print(f"🌟 Starting NanEcho Server - Echo Self Cognitive Architecture")
    print(f"Model: {args.model_path}")
    print(f"Server: http://{args.host}:{args.port}")
    print(f"Echo Mode: {args.echo_mode}")
    
    # Load the model
    if not load_model(args.model_path, args.device):
        print("❌ Failed to load Echo Self model")
        return
    
    print("✅ Echo Self model loaded successfully")
    print("🚀 Starting server...")
    
    # Run the server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()