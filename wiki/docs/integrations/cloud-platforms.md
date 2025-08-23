
# Cloud Platform Integration Guide

This guide covers deploying and integrating Aphrodite Engine with major cloud platforms, providing scalable, production-ready solutions for enterprise deployments.

## ☁️ Amazon Web Services (AWS)

### EC2 Deployment

#### Launch Configuration
```bash
#!/bin/bash
# EC2 user data script for Aphrodite deployment

# Update system
sudo yum update -y

# Install Docker
sudo amazon-linux-extras install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install NVIDIA Docker (for GPU instances)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Deploy Aphrodite
docker run -d \
  --name aphrodite-engine \
  --gpus all \
  -p 2242:2242 \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -e MODEL_NAME=meta-llama/Meta-Llama-3.1-70B-Instruct \
  -e TENSOR_PARALLEL_SIZE=4 \
  alpindale/aphrodite-openai:latest \
  --host 0.0.0.0 \
  --port 2242 \
  --model ${MODEL_NAME} \
  --tensor-parallel-size ${TENSOR_PARALLEL_SIZE}
```

#### CloudFormation Template
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Aphrodite Engine Deployment on AWS'

Parameters:
  InstanceType:
    Type: String
    Default: p3.2xlarge
    Description: EC2 instance type for GPU workloads
  
  ModelName:
    Type: String
    Default: meta-llama/Meta-Llama-3.1-70B-Instruct
    Description: Model to deploy

Resources:
  AphroditeSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Aphrodite Engine
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 2242
          ToPort: 2242
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 0.0.0.0/0

  AphroditeInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !Ref InstanceType
      ImageId: ami-0c02fb55956c7d316  # Amazon Linux 2
      SecurityGroupIds:
        - !Ref AphroditeSecurityGroup
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          # Installation script here
      Tags:
        - Key: Name
          Value: AphroditeEngine

  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Type: application
      Scheme: internet-facing
      SecurityGroups:
        - !Ref AphroditeSecurityGroup
      Subnets:
        - subnet-12345678
        - subnet-87654321

Outputs:
  LoadBalancerDNS:
    Description: Load Balancer DNS Name
    Value: !GetAtt ApplicationLoadBalancer.DNSName
```

### EKS Deployment

#### Kubernetes Manifests
```yaml
# aphrodite-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aphrodite-engine
  namespace: ai-inference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aphrodite-engine
  template:
    metadata:
      labels:
        app: aphrodite-engine
    spec:
      containers:
      - name: aphrodite
        image: alpindale/aphrodite-openai:latest
        resources:
          requests:
            nvidia.com/gpu: 1
            cpu: "4"
            memory: "16Gi"
          limits:
            nvidia.com/gpu: 1
            cpu: "4"
            memory: "16Gi"
        ports:
        - containerPort: 2242
        env:
        - name: MODEL_NAME
          value: "meta-llama/Meta-Llama-3.1-70B-Instruct"
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "2242"
        livenessProbe:
          httpGet:
            path: /health
            port: 2242
          initialDelaySeconds: 300
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 2242
          initialDelaySeconds: 60
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: aphrodite-service
  namespace: ai-inference
spec:
  selector:
    app: aphrodite-engine
  ports:
  - port: 80
    targetPort: 2242
    protocol: TCP
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aphrodite-hpa
  namespace: ai-inference
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aphrodite-engine
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### S3 Model Storage Integration
```python
# AWS S3 model loader
import boto3
import os
from pathlib import Path
from aphrodite.modeling.model_loader.base_loader import BaseModelLoader

class S3ModelLoader(BaseModelLoader):
    def __init__(self, bucket_name: str, region: str = 'us-east-1'):
        self.s3_client = boto3.client('s3', region_name=region)
        self.bucket_name = bucket_name
    
    def download_model(self, model_path: str, local_path: str) -> str:
        """Download model from S3 to local storage"""
        local_dir = Path(local_path)
        local_dir.mkdir(parents=True, exist_ok=True)
        
        # List all objects with the model prefix
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=model_path
        )
        
        for obj in response.get('Contents', []):
            key = obj['Key']
            local_file = local_dir / key.replace(model_path, '').lstrip('/')
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(
                self.bucket_name,
                key,
                str(local_file)
            )
        
        return str(local_dir)

# Usage
loader = S3ModelLoader("my-models-bucket")
model_path = loader.download_model(
    "models/llama-70b-instruct/",
    "/tmp/models/"
)
```

## 🔵 Microsoft Azure

### Azure Container Instances (ACI)

#### Deployment Template
```yaml
# azure-aci-template.yaml
apiVersion: 2019-12-01
location: eastus
name: aphrodite-engine
properties:
  containers:
  - name: aphrodite
    properties:
      image: alpindale/aphrodite-openai:latest
      resources:
        requests:
          cpu: 4
          memoryInGB: 16
          gpu:
            count: 1
            sku: V100
      ports:
      - port: 2242
      environmentVariables:
      - name: MODEL_NAME
        value: meta-llama/Meta-Llama-3.1-70B-Instruct
      - name: HOST
        value: 0.0.0.0
      - name: PORT
        value: 2242
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: 2242
  restartPolicy: Always
type: Microsoft.ContainerInstance/containerGroups
```

#### Azure CLI Deployment
```bash
#!/bin/bash
# Deploy Aphrodite on Azure Container Instances

# Create resource group
az group create --name aphrodite-rg --location eastus

# Create container instance
az container create \
  --resource-group aphrodite-rg \
  --name aphrodite-engine \
  --image alpindale/aphrodite-openai:latest \
  --cpu 4 \
  --memory 16 \
  --gpu-count 1 \
  --gpu-sku V100 \
  --ports 2242 \
  --ip-address public \
  --environment-variables \
    MODEL_NAME=meta-llama/Meta-Llama-3.1-70B-Instruct \
    HOST=0.0.0.0 \
    PORT=2242

# Get public IP
az container show --resource-group aphrodite-rg --name aphrodite-engine --query ipAddress.ip --output tsv
```

### Azure Kubernetes Service (AKS)

#### Cluster Setup
```bash
# Create AKS cluster with GPU support
az aks create \
  --resource-group aphrodite-rg \
  --name aphrodite-cluster \
  --node-count 3 \
  --node-vm-size Standard_NC6s_v3 \
  --enable-addons monitoring \
  --enable-node-public-ip \
  --kubernetes-version 1.24.0

# Get credentials
az aks get-credentials --resource-group aphrodite-rg --name aphrodite-cluster

# Install NVIDIA device plugin
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.12.2/nvidia-device-plugin.yml
```

### Azure OpenAI Integration
```python
# Azure OpenAI proxy configuration
from fastapi import FastAPI, Request, HTTPException
import httpx
import os

app = FastAPI()

class AzureOpenAIProxy:
    def __init__(self):
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_key = os.getenv("AZURE_OPENAI_KEY")
        self.api_version = "2023-12-01-preview"
    
    async def proxy_request(self, request: Request, model: str):
        # Map model names
        model_mapping = {
            "gpt-4": "gpt-4-deployment",
            "gpt-3.5-turbo": "gpt-35-turbo-deployment"
        }
        
        deployment_name = model_mapping.get(model, model)
        
        # Construct Azure OpenAI URL
        azure_url = f"{self.azure_endpoint}/openai/deployments/{deployment_name}/chat/completions"
        
        # Forward request to Azure OpenAI
        async with httpx.AsyncClient() as client:
            response = await client.post(
                azure_url,
                json=await request.json(),
                headers={
                    "api-key": self.azure_key,
                    "Content-Type": "application/json"
                },
                params={"api-version": self.api_version}
            )
            
            return response.json()

proxy = AzureOpenAIProxy()

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    model = body.get("model")
    
    if model in ["gpt-4", "gpt-3.5-turbo"]:
        # Route to Azure OpenAI
        return await proxy.proxy_request(request, model)
    else:
        # Route to local Aphrodite
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:2242/v1/chat/completions",
                json=body
            )
            return response.json()
```

## 🟡 Google Cloud Platform (GCP)

### Google Kubernetes Engine (GKE)

#### Cluster Creation
```bash
# Create GKE cluster with GPU support
gcloud container clusters create aphrodite-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --accelerator type=nvidia-tesla-v100,count=1 \
  --enable-autoscaling \
  --max-nodes 10 \
  --min-nodes 1

# Install NVIDIA drivers
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/ubuntu/daemonset-preloaded.yaml
```

#### Deployment Configuration
```yaml
# gke-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aphrodite-engine
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aphrodite-engine
  template:
    metadata:
      labels:
        app: aphrodite-engine
    spec:
      containers:
      - name: aphrodite
        image: gcr.io/PROJECT_ID/aphrodite-engine:latest
        resources:
          limits:
            nvidia.com/gpu: 1
          requests:
            nvidia.com/gpu: 1
        ports:
        - containerPort: 2242
        env:
        - name: MODEL_NAME
          value: "meta-llama/Meta-Llama-3.1-70B-Instruct"
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: "/var/secrets/google/key.json"
        volumeMounts:
        - name: google-cloud-key
          mountPath: /var/secrets/google
          readOnly: true
      volumes:
      - name: google-cloud-key
        secret:
          secretName: google-cloud-key
```

### Cloud Storage Integration
```python
# Google Cloud Storage model loader
from google.cloud import storage
import os
from pathlib import Path

class GCSModelLoader:
    def __init__(self, bucket_name: str):
        self.client = storage.Client()
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket(bucket_name)
    
    def download_model(self, model_prefix: str, local_path: str) -> str:
        """Download model from GCS to local storage"""
        local_dir = Path(local_path)
        local_dir.mkdir(parents=True, exist_ok=True)
        
        # List all blobs with the model prefix
        blobs = self.bucket.list_blobs(prefix=model_prefix)
        
        for blob in blobs:
            # Skip directories
            if blob.name.endswith('/'):
                continue
            
            local_file = local_dir / blob.name.replace(model_prefix, '').lstrip('/')
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            blob.download_to_filename(str(local_file))
        
        return str(local_dir)

# Usage
loader = GCSModelLoader("my-models-bucket")
model_path = loader.download_model(
    "models/llama-70b-instruct/",
    "/tmp/models/"
)
```

### Vertex AI Integration
```python
# Vertex AI model serving integration
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict

class VertexAIIntegration:
    def __init__(self, project_id: str, region: str):
        aiplatform.init(project=project_id, location=region)
        self.project_id = project_id
        self.region = region
    
    def deploy_model(self, model_path: str, endpoint_name: str):
        """Deploy Aphrodite model to Vertex AI"""
        
        # Create model
        model = aiplatform.Model.upload(
            display_name="aphrodite-llama",
            artifact_uri=model_path,
            serving_container_image_uri="gcr.io/project/aphrodite-serving:latest",
            serving_container_predict_route="/v1/chat/completions",
            serving_container_health_route="/health"
        )
        
        # Create endpoint
        endpoint = aiplatform.Endpoint.create(display_name=endpoint_name)
        
        # Deploy model to endpoint
        endpoint.deploy(
            model=model,
            machine_type="n1-highmem-4",
            accelerator_type="NVIDIA_TESLA_V100",
            accelerator_count=1
        )
        
        return endpoint
    
    def predict(self, endpoint_name: str, instances: list):
        """Make predictions using deployed model"""
        endpoint = aiplatform.Endpoint.list(
            filter=f'display_name="{endpoint_name}"'
        )[0]
        
        response = endpoint.predict(instances=instances)
        return response.predictions
```

## 🟠 Oracle Cloud Infrastructure (OCI)

### Container Engine for Kubernetes (OKE)

```yaml
# oci-oke-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aphrodite-engine
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aphrodite-engine
  template:
    metadata:
      labels:
        app: aphrodite-engine
    spec:
      containers:
      - name: aphrodite
        image: iad.ocir.io/tenancy/aphrodite-engine:latest
        resources:
          limits:
            nvidia.com/gpu: 1
          requests:
            nvidia.com/gpu: 1
        ports:
        - containerPort: 2242
        env:
        - name: MODEL_NAME
          value: "meta-llama/Meta-Llama-3.1-70B-Instruct"
```

## 🔧 Multi-Cloud Deployment Strategy

### Terraform Multi-Cloud Configuration
```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

# AWS Deployment
module "aws_deployment" {
  source = "./modules/aws"
  
  instance_type = var.aws_instance_type
  model_name    = var.model_name
  region        = var.aws_region
}

# Azure Deployment
module "azure_deployment" {
  source = "./modules/azure"
  
  vm_size    = var.azure_vm_size
  model_name = var.model_name
  region     = var.azure_region
}

# GCP Deployment
module "gcp_deployment" {
  source = "./modules/gcp"
  
  machine_type = var.gcp_machine_type
  model_name   = var.model_name
  zone         = var.gcp_zone
}

# Outputs
output "endpoints" {
  value = {
    aws   = module.aws_deployment.endpoint_url
    azure = module.azure_deployment.endpoint_url
    gcp   = module.gcp_deployment.endpoint_url
  }
}
```

### Load Balancer Configuration
```yaml
# global-load-balancer.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: aphrodite-global
spec:
  hosts:
  - api.aphrodite.ai
  http:
  - match:
    - headers:
        x-region:
          exact: us-east-1
    route:
    - destination:
        host: aws-aphrodite.aphrodite.ai
  - match:
    - headers:
        x-region:
          exact: eastus
    route:
    - destination:
        host: azure-aphrodite.aphrodite.ai
  - match:
    - headers:
        x-region:
          exact: us-central1
    route:
    - destination:
        host: gcp-aphrodite.aphrodite.ai
  - route:  # Default route
    - destination:
        host: aws-aphrodite.aphrodite.ai
      weight: 34
    - destination:
        host: azure-aphrodite.aphrodite.ai
      weight: 33
    - destination:
        host: gcp-aphrodite.aphrodite.ai
      weight: 33
```

This comprehensive cloud platform integration guide enables organizations to deploy Aphrodite Engine across multiple cloud providers with high availability, scalability, and performance optimization.
