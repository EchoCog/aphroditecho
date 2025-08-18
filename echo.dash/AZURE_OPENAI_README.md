# Azure OpenAI Service Integration

## Overview

The `copilot_suggestions.py` module has been upgraded to use Azure OpenAI Service instead of the GitHub Copilot API (which is not publicly available). This provides reliable access to AI-powered code suggestions and project analysis.

## Setup

### Prerequisites

1. An Azure subscription with Azure OpenAI Service enabled
2. A deployed GPT model (e.g., GPT-4) in your Azure OpenAI resource

### Environment Variables

Add the following variables to your `.env` file:

```bash
# Azure OpenAI Service (for code suggestions)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### Getting Azure OpenAI Credentials

1. **Create Azure OpenAI Resource:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new "Azure OpenAI" resource
   - Note the endpoint URL (e.g., `https://your-resource.openai.azure.com/`)

2. **Get API Key:**
   - In your Azure OpenAI resource, go to "Keys and Endpoint"
   - Copy one of the API keys

3. **Deploy a Model:**
   - Go to "Model deployments" in your Azure OpenAI resource
   - Deploy a GPT model (recommended: GPT-4)
   - Note the deployment name

## Usage

### Basic Usage

```bash
python copilot_suggestions.py
```

The script will:
1. Load your project notes from `note2self.json`
2. Send them to Azure OpenAI for analysis
3. Receive suggestions for incremental improvements
4. Update the note file with the suggestions

### Custom Note File

```bash
NOTE_FILE=custom_note.json python copilot_suggestions.py
```

## Features

- **Robust Error Handling:** Graceful handling of API errors, rate limits, and network issues
- **Flexible Response Parsing:** Handles both JSON and plain text responses from Azure OpenAI
- **Retry Logic:** Automatic retries with exponential backoff for transient failures
- **Comprehensive Logging:** Detailed logging for debugging and monitoring
- **Environment Validation:** Clear error messages for missing configuration
- **Backward Compatibility:** Maintains the same note file structure and workflow

## API Details

The module uses Azure OpenAI's Chat Completions API with the following configuration:

- **API Version:** `2024-02-15-preview`
- **Temperature:** `0.7` (balanced creativity)
- **Max Tokens:** `1000`
- **Timeout:** `30 seconds`
- **Retry Attempts:** `3`

## Response Format

Azure OpenAI returns suggestions in the following structure:

```json
{
  "suggestions": [
    "Specific improvement suggestion 1",
    "Specific improvement suggestion 2"
  ],
  "next_focus": "Brief description of what to focus on next",
  "timestamp": 1734797500,
  "source": "azure_openai",
  "last_updated": 1734797500,
  "last_update_source": "azure_openai"
}
```

## Error Handling

The module handles various error scenarios:

- **Missing Environment Variables:** Clear error messages for each missing variable
- **Authentication Errors (401):** Invalid API key
- **Resource Not Found (404):** Invalid endpoint or deployment name
- **Rate Limiting (429):** Automatic retry with longer delays
- **Network Errors:** Retry with exponential backoff
- **Invalid JSON Responses:** Fallback to structured text format

## Testing

Run the test suite to verify functionality:

```bash
python -m unittest test_copilot_suggestions.py -v
```

The tests cover:
- Environment variable validation
- API URL construction
- Error handling
- Response parsing
- Note file operations

## Migration from GitHub Copilot

This module replaces the previous GitHub Copilot integration. Key differences:

- **Authentication:** Uses Azure API key instead of GitHub token
- **Endpoint:** Azure OpenAI Service instead of GitHub Copilot API
- **Response Format:** Structured JSON with suggestions and focus areas
- **Rate Limits:** Azure OpenAI rate limits (more predictable)
- **Availability:** Publicly available service vs. private API

## Future Enhancements

The module is designed for future backend modularization:

- **Plugin Architecture:** Easy to extend with additional AI services
- **Configuration Management:** Centralized configuration for multiple backends
- **Performance Optimization:** Caching and batch processing capabilities
- **Analytics Integration:** Usage tracking and performance metrics

## Troubleshooting

### Common Issues

1. **"AZURE_OPENAI_ENDPOINT environment variable is missing"**
   - Ensure `.env` file exists with correct variables
   - Check environment variable names (case-sensitive)

2. **"Unauthorized" (401 error)**
   - Verify your Azure OpenAI API key is correct
   - Ensure the key has not expired

3. **"Resource not found" (404 error)**
   - Check your endpoint URL format
   - Verify the deployment name exists in your Azure resource

4. **Rate limit errors**
   - Wait for the rate limit window to reset
   - Consider upgrading your Azure OpenAI service tier

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger('copilot_suggestions').setLevel(logging.DEBUG)
```

## Security

- **API Keys:** Never commit API keys to version control
- **Environment Files:** Use `.env` files (included in `.gitignore`)
- **Key Rotation:** Regularly rotate your Azure OpenAI API keys
- **Access Control:** Use Azure RBAC to limit resource access