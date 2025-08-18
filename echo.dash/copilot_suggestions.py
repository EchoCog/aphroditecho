"""
Azure OpenAI Service Integration for Code Suggestions

This module provides functionality to fetch code improvement suggestions using Azure OpenAI Service
instead of the GitHub Copilot API (which is not publicly available).

The module:
1. Loads project notes from a JSON file
2. Sends the notes to Azure OpenAI Service for analysis
3. Receives structured suggestions for incremental improvements
4. Updates the note file with the suggestions

Required Environment Variables:
- AZURE_OPENAI_ENDPOINT: The endpoint URL for your Azure OpenAI resource 
  (e.g., https://your-resource.openai.azure.com/)
- AZURE_OPENAI_KEY: The API key for your Azure OpenAI resource
- AZURE_OPENAI_DEPLOYMENT: The deployment name of your model (e.g., gpt-4)

Usage:
    python copilot_suggestions.py

The module is designed for future backend modularization and maintains compatibility
with the existing note file structure and logging patterns.
"""

import json
import requests
import os
import logging
import time

# Azure OpenAI Service configuration
NOTE_FILE = "note2self.json"

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fetch_suggestions_from_azure_openai(note, introspection_context=None):
    """
    Fetch code suggestions from Azure OpenAI Service with AI introspection context.
    
    Required environment variables:
    - AZURE_OPENAI_ENDPOINT: The endpoint URL for your Azure OpenAI resource
    - AZURE_OPENAI_KEY: The API key for your Azure OpenAI resource  
    - AZURE_OPENAI_DEPLOYMENT: The deployment name of your model
    
    Args:
        note: The note data to analyze for suggestions
        introspection_context: Optional AI introspection data for enhanced context
        
    Returns:
        dict: Suggestions response or None if failed
    """
    # Check required environment variables
    azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    azure_key = os.getenv('AZURE_OPENAI_KEY')
    azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    
    if not azure_endpoint:
        logger.error("Error: AZURE_OPENAI_ENDPOINT environment variable is missing.")
        return None
    if not azure_key:
        logger.error("Error: AZURE_OPENAI_KEY environment variable is missing.")
        return None
    if not azure_deployment:
        logger.error("Error: AZURE_OPENAI_DEPLOYMENT environment variable is missing.")
        return None

    # Ensure endpoint has correct format
    if not azure_endpoint.endswith('/'):
        azure_endpoint += '/'
    
    # Construct the Azure OpenAI API URL
    api_url = f"{azure_endpoint}openai/deployments/{azure_deployment}/chat/completions?api-version=2024-02-15-preview"
    
    headers = {
        "api-key": azure_key,
        "Content-Type": "application/json"
    }
    
    # Create the prompt based on the note data
    note_text = json.dumps(note, indent=2) if isinstance(note, dict) else str(note)
    
    # Enhanced system message with introspection awareness
    system_message = """You are an AI assistant that helps analyze project notes and suggests incremental improvements. 
    Based on the provided summary of last cycle events and AI introspection context, identify specific, actionable items for the next incremental improvement.
    When AI introspection data is available, use it to provide more targeted and context-aware suggestions.
    Respond with a JSON object containing 'suggestions' (array of specific improvement suggestions) and 'next_focus' (a brief description of what to focus on next)."""
    
    # Build enhanced user message with introspection context
    user_message = f"""This is a summary of last cycle events. Please can you help me take a look at the repo so we can identify an item for the next incremental improvement?

Note data:
{note_text}"""

    # Add introspection context if available
    if introspection_context:
        introspection_text = json.dumps(introspection_context, indent=2)
        user_message += f"""

AI Introspection Context:
{introspection_text}

Use this AI introspection data to provide more targeted and context-aware improvement suggestions. 
Focus on the highest salience files and areas identified by the AI analysis."""
    
    user_message += "\n\nPlease analyze this and provide specific, actionable suggestions for incremental improvements."

    payload = {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            logger.debug(f"Making request to Azure OpenAI API: {api_url}")
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    logger.debug(f"Received response from Azure OpenAI: {content}")
                    
                    # Try to parse the response as JSON, fall back to structured format
                    try:
                        suggestions_data = json.loads(content)
                        return suggestions_data
                    except json.JSONDecodeError:
                        # If not valid JSON, create a structured response
                        return {
                            "suggestions": [content],
                            "next_focus": "Review and implement the suggested improvements",
                            "timestamp": time.time(),
                            "source": "azure_openai"
                        }
                else:
                    logger.error("No choices in Azure OpenAI response")
                    return None
                    
            elif response.status_code == 401:
                logger.error("Error: Unauthorized. Please check your AZURE_OPENAI_KEY.")
                return None
            elif response.status_code == 404:
                logger.error("Error: Resource not found. Please check your AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT.")
                return None
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded. Waiting before retry...")
                retries += 1
                time.sleep(10)  # Longer wait for rate limits
            else:
                logger.error(f"Failed to fetch suggestions from Azure OpenAI: {response.status_code}")
                logger.debug(f"Response content: {response.text}")
                retries += 1
                time.sleep(5)
                
        except requests.RequestException as e:
            logger.error(f"Request exception: {e}")
            retries += 1
            time.sleep(5)
    
    logger.error("Max retries reached. Unable to fetch suggestions from Azure OpenAI.")
    return None

def update_note_with_suggestions(suggestions):
    """
    Update the note file with suggestions from Azure OpenAI Service.
    
    Args:
        suggestions: Dict containing suggestions and analysis from Azure OpenAI
    """
    try:
        with open(NOTE_FILE, 'r') as file:
            note = json.load(file)
    except FileNotFoundError:
        note = {"timestamp": None, "improvement": {}, "assessment": ""}
        logger.info("Note file not found, creating new note structure.")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from note file: {e}")
        note = {"timestamp": None, "improvement": {}, "assessment": ""}

    # Update note with suggestions, preserving existing structure
    note.update(suggestions)
    
    # Add metadata about the update
    note["last_updated"] = time.time()
    note["last_update_source"] = "azure_openai"

    try:
        with open(NOTE_FILE, 'w') as file:
            json.dump(note, file, indent=2)
        logger.debug(f"Successfully updated note file: {NOTE_FILE}")
    except Exception as e:
        logger.error(f"Failed to write updated note to file: {e}")

def load_introspection_context():
    """Load AI introspection context if available"""
    try:
        # Try to load from request payload first
        with open('.github/workflows/request_payload.json', 'r') as f:
            payload = json.load(f)
            if 'ai_introspection_context' in payload:
                logger.info("Found AI introspection context in request payload")
                return payload['ai_introspection_context']
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    try:
        # Try to load from standalone introspection file
        with open('ai_introspection_data.json', 'r') as f:
            introspection_data = json.load(f)
            logger.info("Found AI introspection data file")
            return introspection_data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    logger.info("No AI introspection context available")
    return None

def main():
    """
    Main function to fetch suggestions from Azure OpenAI and update the note file.
    
    This function:
    1. Loads the existing note from note2self.json
    2. Loads AI introspection context if available
    3. Sends enhanced data to Azure OpenAI Service for analysis and suggestions
    4. Updates the note file with the received suggestions
    
    Required environment variables:
    - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI resource endpoint
    - AZURE_OPENAI_KEY: Your Azure OpenAI API key
    - AZURE_OPENAI_DEPLOYMENT: Your model deployment name
    """
    try:
        with open(NOTE_FILE, 'r') as file:
            note = json.load(file)
    except FileNotFoundError:
        note = {"timestamp": None, "improvement": {}, "assessment": ""}
        logger.info("Note file not found, starting with empty note.")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from note file: {e}")
        note = {"timestamp": None, "improvement": {}, "assessment": ""}

    # Load AI introspection context
    introspection_context = load_introspection_context()
    if introspection_context:
        logger.info(f"Using AI introspection context: {introspection_context.get('introspection_status', 'unknown')}")
        logger.info(f"Files analyzed: {introspection_context.get('files_analyzed', 0)}")

    logger.info("Fetching suggestions from Azure OpenAI Service with enhanced context...")
    suggestions = fetch_suggestions_from_azure_openai(note, introspection_context)
    if suggestions:
        update_note_with_suggestions(suggestions)
        logger.info("Note updated with suggestions from Azure OpenAI Service.")
    else:
        logger.error("No suggestions received from Azure OpenAI Service.")

if __name__ == "__main__":
    main()
