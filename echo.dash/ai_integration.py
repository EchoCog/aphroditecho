import os
import time
import json
import logging
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class AIService:
    """Base class for AI API services"""
    
    def __init__(self):
        self.name = "base_ai_service"
        self.rate_limits = {
            "requests_per_minute": 60,
            "tokens_per_minute": 10000
        }
        self.request_timestamps = []
        self.token_counts = []
    
    def _check_rate_limit(self, token_count: int = 0) -> bool:
        """Check if we're within rate limits
        
        Args:
            token_count: Number of tokens in the request
            
        Returns:
            True if within limits, False otherwise
        """
        now = time.time()
        
        # Clean up old timestamps (older than 1 minute)
        self.request_timestamps = [t for t in self.request_timestamps if now - t < 60]
        self.token_counts = self.token_counts[-len(self.request_timestamps):]
        
        # Check request limit
        if len(self.request_timestamps) >= self.rate_limits["requests_per_minute"]:
            logger.warning(f"{self.name} request rate limit reached")
            return False
            
        # Check token limit
        if sum(self.token_counts) + token_count > self.rate_limits["tokens_per_minute"]:
            logger.warning(f"{self.name} token rate limit reached")
            return False
            
        return True
    
    def _record_usage(self, token_count: int = 0):
        """Record API usage
        
        Args:
            token_count: Number of tokens in the request
        """
        self.request_timestamps.append(time.time())
        self.token_counts.append(token_count)


class OpenAIService(AIService):
    """OpenAI API service integration"""
    
    def __init__(self):
        super().__init__()
        self.name = "openai"
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Set rate limits based on model
        if "gpt-4" in self.model:
            self.rate_limits = {
                "requests_per_minute": 10,
                "tokens_per_minute": 10000
            }
        else:
            self.rate_limits = {
                "requests_per_minute": 60,
                "tokens_per_minute": 60000
            }
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if not self.api_key:
            logger.error("OpenAI API key not set")
            return []
            
        # Simple token count estimate
        token_count = len(text.split())
        if not self._check_rate_limit(token_count):
            logger.warning("Rate limit reached, cannot generate embedding")
            return []
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "input": text,
                "model": "text-embedding-3-small"
            }
            
            response = requests.post(
                f"{self.api_base}/embeddings",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                self._record_usage(token_count)
                return result["data"][0]["embedding"]
            else:
                logger.error(f"OpenAI API error: {response.status_code} {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return []
    
    def complete_text(self, prompt: str, system: str = None, 
                     max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text completion
        
        Args:
            prompt: User prompt
            system: Optional system message
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        if not self.api_key:
            logger.error("OpenAI API key not set")
            return "API key not configured"
            
        # Simple token count estimate
        token_count = len(prompt.split()) + (len(system.split()) if system else 0)
        if not self._check_rate_limit(token_count):
            logger.warning("Rate limit reached, cannot complete text")
            return "Rate limit reached, please try again later"
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                self._record_usage(token_count + result["usage"]["completion_tokens"])
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenAI API error: {response.status_code} {response.text}")
                return f"API error: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error completing text: {str(e)}")
            return f"Error: {str(e)}"
    
    async def analyze_text(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze text for specific attributes
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis to perform
                ('general', 'sentiment', 'entities', 'summarize', 'concepts')
            
        Returns:
            Analysis results
        """
        if not self.api_key:
            logger.error("OpenAI API key not set")
            return {"error": "API key not configured"}
            
        # Prepare system prompt based on analysis type
        system_prompts = {
            "general": "Analyze the following text and provide insights on key themes, tone, and structure.",
            "sentiment": "Analyze the sentiment of the following text. Return a JSON object with 'sentiment' (positive/negative/neutral), 'score' (from -1 to 1), and 'explanation'.",
            "entities": "Extract entities from the following text. Return a JSON array with objects containing 'entity', 'type', and 'salience'.",
            "summarize": "Summarize the following text concisely while preserving the key information.",
            "concepts": "Extract the main concepts from the following text. Return a JSON array with objects containing 'concept', 'importance', and 'related_concepts'."
        }
        
        system = system_prompts.get(analysis_type, system_prompts["general"])
        
        # Add instruction to return JSON
        if analysis_type != "summarize" and "JSON" not in system:
            system += " Return your analysis as a properly formatted JSON object."
        
        # Simple token count estimate
        token_count = len(text.split()) + len(system.split())
        if not self._check_rate_limit(token_count):
            logger.warning("Rate limit reached, cannot analyze text")
            return {"error": "Rate limit reached, please try again later"}
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": text}
            ]
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.3  # Lower temperature for more deterministic analysis
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                self._record_usage(token_count + result["usage"]["completion_tokens"])
                
                # If not a summary, parse as JSON
                if analysis_type != "summarize":
                    try:
                        # Extract JSON if it's within markdown code blocks
                        if "```json" in content:
                            json_content = content.split("```json")[1].split("```")[0].strip()
                            return json.loads(json_content)
                        elif "```" in content:
                            json_content = content.split("```")[1].strip()
                            return json.loads(json_content)
                        else:
                            return json.loads(content)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse JSON from response: {content}")
                        return {"result": content, "warning": "Response was not valid JSON"}
                else:
                    return {"summary": content}
            else:
                logger.error(f"OpenAI API error: {response.status_code} {response.text}")
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            return {"error": str(e)}


class AnthropicService(AIService):
    """Anthropic API service integration"""
    
    def __init__(self):
        super().__init__()
        self.name = "anthropic"
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        
        # Set rate limits
        self.rate_limits = {
            "requests_per_minute": 20,
            "tokens_per_minute": 20000
        }
    
    def complete_text(self, prompt: str, system: str = None, 
                     max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text completion using Anthropic Claude
        
        Args:
            prompt: User prompt
            system: Optional system message
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        if not self.api_key:
            logger.error("Anthropic API key not set")
            return "API key not configured"
            
        # Simple token count estimate
        token_count = len(prompt.split()) + (len(system.split()) if system else 0)
        if not self._check_rate_limit(token_count):
            logger.warning("Rate limit reached, cannot complete text")
            return "Rate limit reached, please try again later"
            
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            if system:
                data["system"] = system
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                self._record_usage(token_count)  # Approximate, we don't have exact usage from API
                return result["content"][0]["text"]
            else:
                logger.error(f"Anthropic API error: {response.status_code} {response.text}")
                return f"API error: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error completing text with Anthropic: {str(e)}")
            return f"Error: {str(e)}"


class AIIntegration:
    """Main AI integration manager"""
    
    def __init__(self):
        self.services = {}
        self.setup_services()
        self.cache_dir = Path("ai_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Load cache
        self.cache = self._load_cache()
    
    def setup_services(self):
        """Set up available AI services"""
        # Try to set up OpenAI
        if os.getenv("OPENAI_API_KEY"):
            self.services["openai"] = OpenAIService()
            logger.info("OpenAI service initialized")
        else:
            logger.warning("OpenAI API key not found, service not available")
            
        # Try to set up Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            self.services["anthropic"] = AnthropicService()
            logger.info("Anthropic service initialized")
        else:
            logger.warning("Anthropic API key not found, service not available")
    
    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        cache_file = self.cache_dir / "ai_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache: {str(e)}")
                return {"embeddings": {}, "completions": {}}
        else:
            return {"embeddings": {}, "completions": {}}
    
    def _save_cache(self):
        """Save cache to disk"""
        cache_file = self.cache_dir / "ai_cache.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(self.cache, f)
        except Exception as e:
            logger.error(f"Error saving cache: {str(e)}")
    
    def get_embedding(self, text: str, service: str = "openai") -> List[float]:
        """Get embedding for text with caching
        
        Args:
            text: Text to embed
            service: AI service to use
            
        Returns:
            Embedding vector
        """
        # Check cache first
        cache_key = f"{service}_{hash(text)}"
        if cache_key in self.cache.get("embeddings", {}):
            return self.cache["embeddings"][cache_key]
            
        # Get service
        ai_service = self.services.get(service)
        if not ai_service:
            logger.error(f"Service {service} not available")
            return []
            
        # Generate embedding
        if isinstance(ai_service, OpenAIService):
            embedding = ai_service.generate_embedding(text)
            
            # Cache result
            if embedding:
                if "embeddings" not in self.cache:
                    self.cache["embeddings"] = {}
                self.cache["embeddings"][cache_key] = embedding
                self._save_cache()
                
            return embedding
        else:
            logger.error(f"Service {service} does not support embeddings")
            return []
    
    def complete_text(self, prompt: str, system: str = None, service: str = "openai",
                     max_tokens: int = 1000, temperature: float = 0.7,
                     cache: bool = True) -> str:
        """Complete text using specified service with optional caching
        
        Args:
            prompt: User prompt
            system: Optional system message
            service: AI service to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            cache: Whether to cache results
            
        Returns:
            Completed text
        """
        # Only cache deterministic completions
        use_cache = cache and temperature < 0.1
        
        # Check cache if applicable
        if use_cache:
            cache_key = f"{service}_{hash(prompt)}_{hash(system) if system else ''}_{max_tokens}"
            if cache_key in self.cache.get("completions", {}):
                return self.cache["completions"][cache_key]
        
        # Get service
        ai_service = self.services.get(service)
        if not ai_service:
            logger.error(f"Service {service} not available")
            return f"Service {service} not available"
            
        # Generate completion
        completion = ai_service.complete_text(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Cache result if applicable
        if use_cache and completion:
            if "completions" not in self.cache:
                self.cache["completions"] = {}
            self.cache["completions"][cache_key] = completion
            self._save_cache()
            
        return completion
    
    async def analyze_text(self, text: str, analysis_type: str = "general", 
                         service: str = "openai") -> Dict[str, Any]:
        """Analyze text using specified service
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis
            service: AI service to use
            
        Returns:
            Analysis results
        """
        # Get service
        ai_service = self.services.get(service)
        if not ai_service:
            logger.error(f"Service {service} not available")
            return {"error": f"Service {service} not available"}
            
        # Perform analysis
        if isinstance(ai_service, OpenAIService):
            return await ai_service.analyze_text(text, analysis_type)
        else:
            # Fall back to simple completion for services without dedicated analysis
            system_prompts = {
                "general": "Analyze the following text and provide insights on key themes, tone, and structure. Return your analysis as JSON.",
                "sentiment": "Analyze the sentiment of the following text. Return a JSON object with 'sentiment' (positive/negative/neutral), 'score' (from -1 to 1), and 'explanation'.",
                "entities": "Extract entities from the following text. Return a JSON array with objects containing 'entity', 'type', and 'salience'.",
                "summarize": "Summarize the following text concisely while preserving the key information.",
                "concepts": "Extract the main concepts from the following text. Return a JSON array with objects containing 'concept', 'importance', and 'related_concepts'."
            }
            
            system = system_prompts.get(analysis_type, system_prompts["general"])
            result = ai_service.complete_text(prompt=text, system=system, temperature=0.3)
            
            # Try to parse as JSON if not a summary
            if analysis_type != "summarize":
                try:
                    # Extract JSON if it's within markdown code blocks
                    if "```json" in result:
                        json_content = result.split("```json")[1].split("```")[0].strip()
                        return json.loads(json_content)
                    elif "```" in result:
                        json_content = result.split("```")[1].strip()
                        return json.loads(json_content)
                    else:
                        return json.loads(result)
                except json.JSONDecodeError:
                    return {"result": result, "warning": "Response was not valid JSON"}
            else:
                return {"summary": result}
    
    def semantic_similarity(self, text1: str, text2: str, service: str = "openai") -> float:
        """Calculate semantic similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            service: AI service to use
            
        Returns:
            Similarity score (0-1)
        """
        # Get embeddings
        embedding1 = self.get_embedding(text1, service)
        embedding2 = self.get_embedding(text2, service)
        
        if not embedding1 or not embedding2:
            logger.error("Could not generate embeddings")
            return 0.0
            
        # Calculate cosine similarity
        embedding1 = np.array(embedding1)
        embedding2 = np.array(embedding2)
        
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        similarity = dot_product / (norm1 * norm2) if norm1 * norm2 != 0 else 0
        
        return float(similarity)
    
    async def enhance_content(self, content: str, enhancement_type: str = "elaborate", 
                           service: str = "openai") -> str:
        """Enhance content using AI
        
        Args:
            content: Content to enhance
            enhancement_type: Type of enhancement
                ('elaborate', 'simplify', 'formalize', 'creative')
            service: AI service to use
            
        Returns:
            Enhanced content
        """
        # Prepare system prompt based on enhancement type
        system_prompts = {
            "elaborate": "Elaborate on the following content by adding more details, examples, and explanations.",
            "simplify": "Simplify the following content to make it more accessible and easier to understand.",
            "formalize": "Rewrite the following content in a more formal, professional tone.",
            "creative": "Enhance the following content with creative elements, metaphors, and engaging language."
        }
        
        system = system_prompts.get(enhancement_type, system_prompts["elaborate"])
        
        # Get service
        ai_service = self.services.get(service)
        if not ai_service:
            logger.error(f"Service {service} not available")
            return f"Service {service} not available"
            
        # Perform enhancement
        if isinstance(ai_service, OpenAIService):
            return ai_service.complete_text(content, system=system, temperature=0.7)
        else:
            # Fall back to simple completion
            prompt = f"{system}\n\n{content}"
            return ai_service.complete_text(prompt=prompt, temperature=0.7)
    
    async def generate_echo_connections(self, content: str, existing_concepts: List[str],
                                    service: str = "openai") -> List[Dict]:
        """Generate potential echo connections for content
        
        Args:
            content: New content
            existing_concepts: List of existing concepts
            service: AI service to use
            
        Returns:
            List of potential connections
        """
        # Prepare system prompt
        system = """
        Analyze the provided content and existing concepts to identify potential connections.
        For each connection, provide:
        1. Source concept or content excerpt
        2. Target concept
        3. Relationship type (e.g., "is_part_of", "contradicts", "elaborates", "exemplifies")
        4. Strength (0.0-1.0)
        5. Explanation
        
        Return your analysis as a JSON array of connection objects.
        """
        
        # Prepare prompt
        prompt = f"""
        CONTENT:
        {content}
        
        EXISTING CONCEPTS:
        {', '.join(existing_concepts)}
        
        Identify up to 5 most meaningful connections between the content and concepts.
        """
        
        # Get service
        ai_service = self.services.get(service)
        if not ai_service:
            logger.error(f"Service {service} not available")
            return []
            
        # Generate connections
        if isinstance(ai_service, OpenAIService):
            result = await ai_service.analyze_text(prompt, "general")
            
            # Extract connections
            if isinstance(result, dict) and "error" not in result:
                if "connections" in result:
                    return result["connections"]
                else:
                    return result.get("result", [])
            else:
                logger.error(f"Error generating connections: {result}")
                return []
        else:
            # Fall back to simple completion
            completion = ai_service.complete_text(
                prompt=prompt, 
                system=system,
                temperature=0.3
            )
            
            try:
                # Extract JSON
                if "```json" in completion:
                    json_content = completion.split("```json")[1].split("```")[0].strip()
                    return json.loads(json_content)
                elif "```" in completion:
                    json_content = completion.split("```")[1].strip()
                    return json.loads(json_content)
                else:
                    return json.loads(completion)
            except json.JSONDecodeError:
                logger.error(f"Could not parse connections from: {completion}")
                return []

# Initialize the global AI integration manager
ai_manager = AIIntegration()