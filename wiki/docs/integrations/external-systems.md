
# External Systems Integration

The Aphrodite Engine with Deep Tree Echo provides comprehensive integration capabilities with external systems, enabling seamless connectivity with various AI/ML platforms, databases, and services.

## 🔌 Supported Integrations

### AI/ML Platform Integrations

#### OpenAI Compatible API
```python
# Integration with OpenAI ecosystem
import openai
from aphrodite import LLM

# Configure Aphrodite as OpenAI-compatible endpoint
llm = LLM(model="meta-llama/Meta-Llama-3.1-70B-Instruct")
openai.api_base = "http://localhost:2242/v1"
openai.api_key = "your-api-key"

# Use standard OpenAI client calls
response = openai.Completion.create(
    model="meta-llama/Meta-Llama-3.1-70B-Instruct",
    prompt="Explain quantum computing",
    max_tokens=150
)
```

#### Hugging Face Integration
```python
# Direct model loading from Hugging Face Hub
from aphrodite import LLM, SamplingParams

llm = LLM(
    model="microsoft/DialoGPT-medium",
    download_dir="./models",
    trust_remote_code=True
)

# Generate with custom parameters
sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=256
)

outputs = llm.generate(["Hello, how are you?"], sampling_params)
```

### Database Integrations

#### Vector Database Support
```python
# Integration with Pinecone
import pinecone
from aphrodite.endpoints.openai import serving_embedding

# Initialize Pinecone
pinecone.init(api_key="your-api-key", environment="us-west1-gcp")
index = pinecone.Index("aphrodite-embeddings")

# Generate embeddings with Aphrodite
embeddings = serving_embedding.generate_embeddings([
    "Document content 1",
    "Document content 2"
])

# Store in Pinecone
index.upsert([
    ("doc1", embeddings[0]),
    ("doc2", embeddings[1])
])
```

#### SQL Database Integration
```python
# Integration with PostgreSQL for conversation storage
import psycopg2
from aphrodite.aar_core.memory import MemoryManager

class DatabaseMemoryBackend:
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)
        self.memory_manager = MemoryManager()
    
    def store_conversation(self, session_id, messages):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (session_id, messages, timestamp) VALUES (%s, %s, NOW())",
            (session_id, json.dumps(messages))
        )
        self.conn.commit()
    
    def retrieve_context(self, session_id, limit=10):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT messages FROM conversations WHERE session_id = %s ORDER BY timestamp DESC LIMIT %s",
            (session_id, limit)
        )
        return cursor.fetchall()
```

### Cloud Platform Integrations

#### AWS Integration
```python
# AWS S3 for model storage
import boto3
from aphrodite.modeling.model_loader import BaseLoader

class S3ModelLoader(BaseLoader):
    def __init__(self, bucket_name, region='us-east-1'):
        self.s3_client = boto3.client('s3', region_name=region)
        self.bucket_name = bucket_name
    
    def download_model(self, model_path, local_path):
        self.s3_client.download_file(
            self.bucket_name, 
            model_path, 
            local_path
        )
        return local_path

# Usage
loader = S3ModelLoader("my-models-bucket")
model_path = loader.download_model(
    "models/llama-7b/pytorch_model.bin",
    "./local_models/"
)
```

#### Azure OpenAI Integration
```yaml
# Configuration for Azure OpenAI
azure_config:
  api_base: "https://your-resource.openai.azure.com"
  api_version: "2023-12-01-preview"
  deployment_name: "gpt-4"
  api_key: "${AZURE_OPENAI_API_KEY}"

# Proxy configuration
proxy:
  azure_openai:
    enabled: true
    endpoint: "https://your-resource.openai.azure.com"
    fallback: true
```

## 🛠️ Integration Patterns

### Middleware Integration
```python
# Custom middleware for request/response processing
from aphrodite.endpoints.openai.api_server import app
from fastapi import Request, Response
import time

@app.middleware("http")
async def custom_processing_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Pre-processing
    if request.url.path.startswith("/v1/chat/completions"):
        # Add custom headers or modify request
        request.state.custom_processing = True
    
    response = await call_next(request)
    
    # Post-processing
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

### Webhook Integration
```python
# Webhook support for real-time notifications
from fastapi import FastAPI, BackgroundTasks
import httpx

class WebhookManager:
    def __init__(self):
        self.webhooks = []
    
    def register_webhook(self, url: str, events: list):
        self.webhooks.append({"url": url, "events": events})
    
    async def trigger_webhook(self, event: str, data: dict):
        for webhook in self.webhooks:
            if event in webhook["events"]:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        webhook["url"],
                        json={"event": event, "data": data}
                    )

# Usage in API endpoints
webhook_manager = WebhookManager()

@app.post("/v1/completions")
async def create_completion(request: CompletionRequest, background_tasks: BackgroundTasks):
    # Process completion
    result = await process_completion(request)
    
    # Trigger webhook
    background_tasks.add_task(
        webhook_manager.trigger_webhook,
        "completion.created",
        {"request_id": result.id, "model": request.model}
    )
    
    return result
```

## 🔗 API Gateway Integration

### Kong Integration
```yaml
# Kong configuration for Aphrodite
services:
  - name: aphrodite-service
    url: http://localhost:2242
    
routes:
  - name: aphrodite-completions
    service: aphrodite-service
    paths:
      - /ai/completions
    strip_path: true
    
plugins:
  - name: rate-limiting
    config:
      minute: 100
      hour: 1000
  
  - name: key-auth
    config:
      key_names: ["X-API-Key"]
  
  - name: prometheus
    config:
      per_consumer: true
```

### NGINX Integration
```nginx
# NGINX configuration for load balancing
upstream aphrodite_backend {
    least_conn;
    server 127.0.0.1:2242 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:2243 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:2244 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    location /v1/ {
        proxy_pass http://aphrodite_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://aphrodite_backend/health;
        access_log off;
    }
}
```

## 📊 Monitoring & Observability Integrations

### Prometheus & Grafana
```python
# Custom metrics export
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics definitions
REQUEST_COUNT = Counter('aphrodite_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('aphrodite_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('aphrodite_active_connections', 'Active connections')

# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    
    ACTIVE_CONNECTIONS.inc()
    
    response = await call_next(request)
    
    REQUEST_DURATION.observe(time.time() - start_time)
    ACTIVE_CONNECTIONS.dec()
    
    return response
```

### DataDog Integration
```python
# DataDog custom metrics
from datadog import DogStatsdClient
import os

statsd = DogStatsdClient(
    host=os.getenv('DD_AGENT_HOST', 'localhost'),
    port=int(os.getenv('DD_DOGSTATSD_PORT', 8125))
)

# Custom metrics tracking
class MetricsTracker:
    def track_request(self, model_name: str, duration: float, tokens: int):
        statsd.increment('aphrodite.requests.count', tags=[f'model:{model_name}'])
        statsd.histogram('aphrodite.requests.duration', duration, tags=[f'model:{model_name}'])
        statsd.histogram('aphrodite.tokens.generated', tokens, tags=[f'model:{model_name}'])
    
    def track_error(self, error_type: str, model_name: str):
        statsd.increment('aphrodite.errors.count', tags=[
            f'error_type:{error_type}',
            f'model:{model_name}'
        ])
```

## 🔐 Authentication & Authorization Integrations

### OAuth 2.0 / JWT Integration
```python
# JWT-based authentication
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

def verify_token(token: str = Depends(security)):
    try:
        payload = jwt.decode(
            token.credentials,
            "your-secret-key",
            algorithms=["HS256"]
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

@app.post("/v1/chat/completions")
async def protected_completion(
    request: ChatCompletionRequest,
    user: dict = Depends(verify_token)
):
    # Process authenticated request
    return await process_chat_completion(request, user_context=user)
```

### LDAP Integration
```python
# LDAP authentication
import ldap
from fastapi import HTTPException

class LDAPAuthenticator:
    def __init__(self, server_url: str, base_dn: str):
        self.server_url = server_url
        self.base_dn = base_dn
    
    def authenticate(self, username: str, password: str) -> dict:
        try:
            conn = ldap.initialize(self.server_url)
            user_dn = f"uid={username},{self.base_dn}"
            conn.simple_bind_s(user_dn, password)
            
            # Get user attributes
            result = conn.search_s(
                user_dn,
                ldap.SCOPE_BASE,
                '(objectClass=*)',
                ['cn', 'mail', 'memberOf']
            )
            
            return {
                "username": username,
                "attributes": result[0][1]
            }
        
        except ldap.INVALID_CREDENTIALS:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")
```

## 📚 SDK Integration Examples

### Python SDK
```python
# Custom Python SDK wrapper
class AphroditeClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = httpx.Client()
    
    def chat_completion(self, messages: list, model: str = "default", **kwargs):
        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": model,
                "messages": messages,
                **kwargs
            }
        )
        return response.json()
    
    def stream_completion(self, messages: list, model: str = "default", **kwargs):
        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": model,
                "messages": messages,
                "stream": True,
                **kwargs
            },
            stream=True
        )
        
        for line in response.iter_lines():
            if line.startswith(b"data: "):
                yield json.loads(line[6:])
```

### Node.js SDK
```javascript
// Node.js integration example
const axios = require('axios');
const EventSource = require('eventsource');

class AphroditeClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }
    
    async chatCompletion(messages, model = 'default', options = {}) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/v1/chat/completions`,
                {
                    model,
                    messages,
                    ...options
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            return response.data;
        } catch (error) {
            throw new Error(`Aphrodite API Error: ${error.response.data.error}`);
        }
    }
    
    streamCompletion(messages, model = 'default', options = {}) {
        const url = `${this.baseUrl}/v1/chat/completions`;
        const eventSource = new EventSource(url, {
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            }
        });
        
        return eventSource;
    }
}
```

This documentation provides comprehensive integration patterns and examples for connecting Aphrodite Engine with external systems, enabling developers to seamlessly incorporate the engine into existing workflows and infrastructure.
