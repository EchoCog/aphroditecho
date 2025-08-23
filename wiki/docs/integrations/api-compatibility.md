
# API Compatibility Matrix

Aphrodite Engine provides extensive API compatibility with major AI/ML platforms and services, ensuring seamless integration with existing workflows and tools.

## 🔗 OpenAI API Compatibility

### Supported Endpoints

| Endpoint | Status | Compatibility | Notes |
|----------|--------|---------------|-------|
| `/v1/chat/completions` | ✅ Full | 100% | Complete OpenAI compatibility |
| `/v1/completions` | ✅ Full | 100% | Legacy completion format |
| `/v1/embeddings` | ✅ Full | 95% | Minor parameter differences |
| `/v1/models` | ✅ Full | 100% | Model listing and info |
| `/v1/audio/transcriptions` | ✅ Full | 90% | Whisper-compatible |
| `/v1/audio/translations` | ✅ Full | 90% | Whisper-compatible |
| `/v1/images/generations` | ⚠️ Partial | 60% | Limited model support |
| `/v1/fine-tuning/jobs` | 🔄 In Progress | - | Coming in v1.2 |

### Parameter Compatibility

#### Chat Completions
```json
{
  "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,           // ✅ Supported
  "top_p": 0.9,                // ✅ Supported
  "max_tokens": 150,           // ✅ Supported
  "stop": ["</s>"],            // ✅ Supported
  "stream": true,              // ✅ Supported
  "frequency_penalty": 0.1,    // ✅ Supported
  "presence_penalty": 0.1,     // ✅ Supported
  "logit_bias": {"50256": -100}, // ✅ Supported
  "user": "user123",           // ✅ Supported
  "tools": [...],              // ✅ Supported
  "tool_choice": "auto",       // ✅ Supported
  "response_format": {...},    // ✅ Supported
  "seed": 42,                  // ✅ Supported
  "logprobs": true,            // ✅ Supported
  "top_logprobs": 5           // ✅ Supported
}
```

### Response Format Compatibility
```json
// Standard OpenAI Response Format
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
  "system_fingerprint": "fp_44709d6fcb",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
```

## 🤗 Hugging Face Transformers Compatibility

### Model Loading Compatibility
```python
# Standard Transformers usage
from transformers import AutoTokenizer, AutoModelForCausalLM

# Aphrodite equivalent
from aphrodite import LLM, SamplingParams

# Both support the same model identifiers
model_name = "microsoft/DialoGPT-medium"

# Transformers approach
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Aphrodite approach (optimized)
llm = LLM(model=model_name)
```

### Configuration Compatibility
```python
# Transformers generation config
generation_config = {
    "max_new_tokens": 100,
    "temperature": 0.8,
    "top_p": 0.95,
    "do_sample": True,
    "pad_token_id": tokenizer.eos_token_id
}

# Aphrodite equivalent
sampling_params = SamplingParams(
    max_tokens=100,
    temperature=0.8,
    top_p=0.95,
    # pad_token_id handled automatically
)
```

## 📊 MLflow Integration

### Model Registry Compatibility
```python
# MLflow model logging
import mlflow
from aphrodite import LLM

# Register Aphrodite model with MLflow
with mlflow.start_run():
    llm = LLM(model="meta-llama/Meta-Llama-3.1-7B-Instruct")
    
    # Log model artifacts
    mlflow.log_param("model_name", "meta-llama/Meta-Llama-3.1-7B-Instruct")
    mlflow.log_param("max_tokens", 512)
    mlflow.log_param("temperature", 0.7)
    
    # Log custom metrics
    mlflow.log_metric("throughput_tokens_per_second", 150.5)
    mlflow.log_metric("memory_usage_gb", 12.3)
```

## 🔧 LangChain Integration

### LLM Interface Compatibility
```python
from langchain.llms.base import LLM as LangChainLLM
from aphrodite import LLM as AphroditeLLM
from typing import Optional, List, Any

class AphroditeLangChain(LangChainLLM):
    """LangChain wrapper for Aphrodite Engine"""
    
    def __init__(self, model: str, **kwargs):
        super().__init__()
        self.llm = AphroditeLLM(model=model, **kwargs)
    
    def _call(
        self, 
        prompt: str, 
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs
    ) -> str:
        from aphrodite import SamplingParams
        
        sampling_params = SamplingParams(
            stop=stop,
            **kwargs
        )
        
        outputs = self.llm.generate([prompt], sampling_params)
        return outputs[0].outputs[0].text
    
    @property
    def _llm_type(self) -> str:
        return "aphrodite"

# Usage in LangChain
llm = AphroditeLangChain(model="meta-llama/Meta-Llama-3.1-7B-Instruct")

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["question"],
    template="Answer the following question: {question}"
)

chain = LLMChain(llm=llm, prompt=prompt)
response = chain.run("What is quantum computing?")
```

## 🦜 LlamaIndex Integration

### LLM Interface
```python
from llama_index.llms.base import LLM as LlamaIndexLLM
from llama_index.llms.base import CompletionResponse, ChatResponse
from aphrodite import LLM as AphroditeLLM

class AphroditeLlamaIndex(LlamaIndexLLM):
    def __init__(self, model: str, **kwargs):
        super().__init__()
        self.llm = AphroditeLLM(model=model, **kwargs)
    
    @property
    def metadata(self):
        return {
            "model_name": self.llm.model_config.model,
            "context_window": self.llm.model_config.max_model_len,
            "num_output": 512,
        }
    
    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        from aphrodite import SamplingParams
        
        sampling_params = SamplingParams(**kwargs)
        outputs = self.llm.generate([prompt], sampling_params)
        
        return CompletionResponse(
            text=outputs[0].outputs[0].text,
            additional_kwargs={}
        )
    
    def chat(self, messages, **kwargs) -> ChatResponse:
        # Convert messages to prompt format
        prompt = self._messages_to_prompt(messages)
        completion = self.complete(prompt, **kwargs)
        
        return ChatResponse(
            message={"role": "assistant", "content": completion.text}
        )
```

## 🌐 FastAPI Integration

### Complete Server Example
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Aphrodite API Server")

# Pydantic models for request/response
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 150
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[dict]
    usage: dict

# Initialize Aphrodite
from aphrodite import LLM, SamplingParams
llm = LLM(model="meta-llama/Meta-Llama-3.1-7B-Instruct")

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    try:
        # Convert messages to prompt
        prompt = format_messages_for_model(request.messages)
        
        # Set up sampling parameters
        sampling_params = SamplingParams(
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Generate response
        outputs = llm.generate([prompt], sampling_params)
        response_text = outputs[0].outputs[0].text
        
        # Format OpenAI-compatible response
        return ChatCompletionResponse(
            id=f"chatcmpl-{generate_id()}",
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(prompt.split()) + len(response_text.split())
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 🔌 Streaming Response Compatibility

### Server-Sent Events (SSE)
```python
from fastapi.responses import StreamingResponse
import json

@app.post("/v1/chat/completions/stream")
async def stream_chat_completions(request: ChatCompletionRequest):
    async def generate_stream():
        # Initialize streaming generation
        prompt = format_messages_for_model(request.messages)
        
        # Stream tokens as they're generated
        for token_data in llm.generate_stream([prompt]):
            chunk = {
                "id": f"chatcmpl-{generate_id()}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "content": token_data.text
                    },
                    "finish_reason": None
                }]
            }
            
            yield f"data: {json.dumps(chunk)}\n\n"
        
        # Send final chunk
        final_chunk = {
            "id": f"chatcmpl-{generate_id()}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
```

## 📊 Compatibility Testing

### Automated Compatibility Tests
```python
import pytest
import requests
import openai
from typing import Dict, Any

class TestAPICompatibility:
    def setup_method(self):
        self.base_url = "http://localhost:2242"
        self.openai_client = openai.OpenAI(
            api_key="test-key",
            base_url=f"{self.base_url}/v1"
        )
    
    def test_openai_chat_completion_compatibility(self):
        """Test OpenAI client compatibility"""
        response = self.openai_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-7B-Instruct",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=10
        )
        
        # Verify response structure
        assert response.id is not None
        assert response.object == "chat.completion"
        assert len(response.choices) > 0
        assert response.choices[0].message.role == "assistant"
        assert response.choices[0].message.content is not None
    
    def test_streaming_compatibility(self):
        """Test streaming response compatibility"""
        stream = self.openai_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-7B-Instruct",
            messages=[{"role": "user", "content": "Count to 5"}],
            max_tokens=50,
            stream=True
        )
        
        chunks = list(stream)
        assert len(chunks) > 0
        
        # Verify chunk structure
        for chunk in chunks[:-1]:  # Exclude final [DONE] chunk
            assert chunk.id is not None
            assert chunk.object == "chat.completion.chunk"
    
    def test_parameter_compatibility(self):
        """Test parameter handling compatibility"""
        params_to_test = [
            {"temperature": 0.5},
            {"top_p": 0.9},
            {"frequency_penalty": 0.1},
            {"presence_penalty": 0.1},
            {"stop": ["STOP"]},
            {"max_tokens": 20},
            {"logit_bias": {"1": -100}}
        ]
        
        for params in params_to_test:
            response = self.openai_client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-7B-Instruct",
                messages=[{"role": "user", "content": "Test"}],
                **params
            )
            assert response.choices[0].message.content is not None

if __name__ == "__main__":
    pytest.main([__file__])
```

This comprehensive compatibility matrix ensures that Aphrodite Engine can seamlessly integrate with existing AI/ML workflows and tools while maintaining full API compatibility with industry standards.
