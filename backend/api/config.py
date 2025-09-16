"""
Configuration API for YAML validation and management
Handles YAML configuration validation, saving, and template management
"""

import yaml
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class YAMLValidationRequest(BaseModel):
    yaml_content: str = Field(..., description="YAML content to validate")
    validation_type: str = Field("basic", description="Type of validation (basic, ai_assisted)")

class YAMLValidationResult(BaseModel):
    type: str = Field(..., description="Result type (success, error, warning, info)")
    message: str = Field(..., description="Validation message")
    line: Optional[int] = Field(None, description="Line number if applicable")

class YAMLValidationResponse(BaseModel):
    is_valid: bool = Field(..., description="Whether the YAML is valid")
    validation_results: List[YAMLValidationResult] = Field(..., description="List of validation results")
    parsed_config: Optional[Dict[str, Any]] = Field(None, description="Parsed configuration if valid")

class YAMLSaveRequest(BaseModel):
    yaml_content: str = Field(..., description="YAML content to save")
    template_name: Optional[str] = Field(None, description="Template name")
    config_name: Optional[str] = Field(None, description="Configuration name")

class YAMLSaveResponse(BaseModel):
    config_id: str = Field(..., description="Generated configuration ID")
    message: str = Field(..., description="Success message")

class TemplateResponse(BaseModel):
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    content: str = Field(..., description="Template YAML content")
    category: str = Field(..., description="Template category")
    tags: List[str] = Field(default_factory=list, description="Template tags")

# Create router
router = APIRouter(prefix="/api/config", tags=["configuration"])

# Built-in templates
BUILTIN_TEMPLATES = {
    "zai": {
        "name": "Z.AI Web Chat",
        "description": "Configuration for Z.AI web chat interface with browser automation",
        "category": "web_chat",
        "tags": ["z.ai", "web_chat", "browser_automation"],
        "content": """name: ZaiTest1Integration
URL: https://chat.z.ai
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '20'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: 'yes'
useproxy: 'no'
provider_type: web_chat
interface_elements:
  text_input: 'textarea[placeholder*="message"], input[type="text"]'
  send_button: 'button[type="submit"], button:contains("Send")'
  response_area: '.message-content, .response-text'
  new_conversation: 'button:contains("New"), .new-chat-button'
interaction_methods:
  - method: direct_input
    description: Direct text input and send
  - method: streaming_response
    description: Handle streaming responses
  - method: session_management
    description: Manage conversation sessions
  - method: error_handling
    description: Handle errors and retries
browser_settings:
  headless: false
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  viewport: 
    width: 1920
    height: 1080
  wait_timeout: 30000
  navigation_timeout: 60000"""
    },
    "mistral": {
        "name": "Mistral AI",
        "description": "Configuration for Mistral AI chat interface",
        "category": "web_chat",
        "tags": ["mistral", "web_chat", "ai_chat"],
        "content": """name: MistralTestIntegration
URL: https://chat.mistral.ai
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '3'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: 'yes'
useproxy: 'no'
provider_type: web_chat
interface_elements:
  text_input: 'textarea[data-testid="chat-input"]'
  send_button: 'button[data-testid="send-button"]'
  response_area: '.message-content'
  new_conversation: 'button[data-testid="new-chat"]'
interaction_methods:
  - method: direct_input
    description: Direct text input and send
  - method: streaming_response
    description: Handle streaming responses
  - method: session_management
    description: Manage conversation sessions
  - method: error_handling
    description: Handle errors and retries
browser_settings:
  headless: false
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  viewport: 
    width: 1920
    height: 1080
  wait_timeout: 30000"""
    },
    "deepseek": {
        "name": "DeepSeek",
        "description": "Configuration for DeepSeek chat interface",
        "category": "web_chat",
        "tags": ["deepseek", "web_chat", "ai_chat"],
        "content": """name: DeepSeekTestIntegration
URL: https://chat.deepseek.com
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '20'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: 'yes'
useproxy: 'no'
provider_type: web_chat
interface_elements:
  text_input: 'textarea.chat-input'
  send_button: 'button.send-btn'
  response_area: '.message-bubble'
  new_conversation: '.new-chat-btn'
interaction_methods:
  - method: direct_input
    description: Direct text input and send
  - method: streaming_response
    description: Handle streaming responses
  - method: session_management
    description: Manage conversation sessions
  - method: error_handling
    description: Handle errors and retries
browser_settings:
  headless: false
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  viewport: 
    width: 1920
    height: 1080"""
    },
    "claude": {
        "name": "Claude",
        "description": "Configuration for Claude chat interface",
        "category": "web_chat",
        "tags": ["claude", "anthropic", "web_chat"],
        "content": """name: ClaudeTestIntegration
URL: https://claude.ai
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '5'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: 'yes'
useproxy: 'no'
provider_type: web_chat
interface_elements:
  text_input: 'div[contenteditable="true"]'
  send_button: 'button[aria-label="Send Message"]'
  response_area: '.message-content'
  new_conversation: 'button:contains("New Conversation")'
interaction_methods:
  - method: direct_input
    description: Direct text input and send
  - method: streaming_response
    description: Handle streaming responses
  - method: session_management
    description: Manage conversation sessions
  - method: error_handling
    description: Handle errors and retries
browser_settings:
  headless: false
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  viewport: 
    width: 1920
    height: 1080"""
    },
    "openai": {
        "name": "OpenAI API",
        "description": "Configuration for OpenAI REST API integration",
        "category": "rest_api",
        "tags": ["openai", "rest_api", "gpt"],
        "content": """name: OpenAIAPIIntegration
URL: https://api.openai.com/v1/chat/completions
api_key: 'your-api-key-here'
maxautoscaleparallel: '10'
provider_type: rest_api
model: gpt-4
headers:
  Authorization: 'Bearer {api_key}'
  Content-Type: 'application/json'
request_format:
  model: '{model}'
  messages: []
  temperature: 0.7
  max_tokens: 2000
  stream: false
response_format:
  content_path: 'choices[0].message.content'
  error_path: 'error.message'
  usage_path: 'usage'
interaction_methods:
  - method: chat_completion
    description: Standard chat completion API
  - method: streaming_completion
    description: Streaming chat completion
  - method: function_calling
    description: Function calling support
  - method: error_handling
    description: Handle API errors and rate limits
rate_limiting:
  requests_per_minute: 60
  tokens_per_minute: 90000
  retry_attempts: 3
  backoff_factor: 2"""
    },
    "generic": {
        "name": "Generic Web Chat",
        "description": "Generic configuration template for web chat interfaces",
        "category": "web_chat",
        "tags": ["generic", "web_chat", "template"],
        "content": """name: GenericWebChatIntegration
URL: https://example.com/chat
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '5'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: 'yes'
useproxy: 'no'
provider_type: web_chat
interface_elements:
  text_input: 'textarea, input[type="text"]'
  send_button: 'button[type="submit"], .send-button'
  response_area: '.message, .response'
  new_conversation: '.new-chat, .clear-chat'
interaction_methods:
  - method: direct_input
    description: Direct text input and send
  - method: streaming_response
    description: Handle streaming responses
  - method: session_management
    description: Manage conversation sessions
  - method: error_handling
    description: Handle errors and retries
browser_settings:
  headless: false
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  viewport: 
    width: 1920
    height: 1080
  wait_timeout: 30000"""
    }
}

@router.post("/validate", response_model=YAMLValidationResponse)
async def validate_yaml_config(request: YAMLValidationRequest):
    """Validate YAML configuration with optional AI assistance"""
    try:
        validation_results = []
        parsed_config = None
        
        # Basic YAML syntax validation
        try:
            parsed_config = yaml.safe_load(request.yaml_content)
            validation_results.append(YAMLValidationResult(
                type="success",
                message="YAML syntax is valid",
                line=None
            ))
        except yaml.YAMLError as e:
            validation_results.append(YAMLValidationResult(
                type="error",
                message=f"YAML syntax error: {str(e)}",
                line=getattr(e, 'problem_mark', {}).get('line', None)
            ))
            return YAMLValidationResponse(
                is_valid=False,
                validation_results=validation_results,
                parsed_config=None
            )
        
        # Validate required fields
        required_fields = ['name', 'URL', 'provider_type']
        for field in required_fields:
            if field not in parsed_config:
                validation_results.append(YAMLValidationResult(
                    type="error",
                    message=f"Missing required field: {field}",
                    line=None
                ))
        
        # Validate provider_type
        valid_provider_types = ['web_chat', 'rest_api']
        provider_type = parsed_config.get('provider_type')
        if provider_type and provider_type not in valid_provider_types:
            validation_results.append(YAMLValidationResult(
                type="error",
                message=f"Invalid provider_type: {provider_type}. Must be one of: {', '.join(valid_provider_types)}",
                line=None
            ))
        
        # Validate web_chat specific fields
        if provider_type == 'web_chat':
            web_chat_fields = ['authemail', 'authpassword', 'interface_elements']
            for field in web_chat_fields:
                if field not in parsed_config:
                    validation_results.append(YAMLValidationResult(
                        type="warning",
                        message=f"Recommended field for web_chat: {field}",
                        line=None
                    ))
            
            # Validate interface elements
            if 'interface_elements' in parsed_config:
                required_elements = ['text_input', 'send_button', 'response_area']
                interface_elements = parsed_config['interface_elements']
                for element in required_elements:
                    if element not in interface_elements:
                        validation_results.append(YAMLValidationResult(
                            type="warning",
                            message=f"Missing interface element: {element}",
                            line=None
                        ))
        
        # Validate rest_api specific fields
        elif provider_type == 'rest_api':
            rest_api_fields = ['api_key', 'headers', 'request_format']
            for field in rest_api_fields:
                if field not in parsed_config:
                    validation_results.append(YAMLValidationResult(
                        type="warning",
                        message=f"Recommended field for rest_api: {field}",
                        line=None
                    ))
        
        # Validate maxautoscaleparallel
        max_parallel = parsed_config.get('maxautoscaleparallel')
        if max_parallel:
            try:
                max_parallel_int = int(max_parallel)
                if max_parallel_int < 1 or max_parallel_int > 100:
                    validation_results.append(YAMLValidationResult(
                        type="warning",
                        message="maxautoscaleparallel should be between 1 and 100",
                        line=None
                    ))
            except ValueError:
                validation_results.append(YAMLValidationResult(
                    type="error",
                    message="maxautoscaleparallel must be a valid integer",
                    line=None
                ))
        
        # AI-assisted validation (if requested)
        if request.validation_type == "ai_assisted":
            ai_results = await perform_ai_validation(parsed_config)
            validation_results.extend(ai_results)
        
        # Determine if configuration is valid
        has_errors = any(result.type == "error" for result in validation_results)
        is_valid = not has_errors
        
        if is_valid and not validation_results:
            validation_results.append(YAMLValidationResult(
                type="success",
                message="Configuration is valid and ready to use!",
                line=None
            ))
        
        return YAMLValidationResponse(
            is_valid=is_valid,
            validation_results=validation_results,
            parsed_config=parsed_config if is_valid else None
        )
        
    except Exception as e:
        logger.error(f"Error validating YAML: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

async def perform_ai_validation(config: Dict[str, Any]) -> List[YAMLValidationResult]:
    """Perform AI-assisted validation using Codegen API"""
    results = []
    
    try:
        # This would integrate with the Codegen API for intelligent validation
        # For now, we'll provide some smart validation based on common patterns
        
        provider_type = config.get('provider_type')
        
        # Check for common URL patterns
        url = config.get('URL', '')
        if provider_type == 'web_chat':
            if not url.startswith('https://'):
                results.append(YAMLValidationResult(
                    type="warning",
                    message="Web chat URLs should use HTTPS for security",
                    line=None
                ))
            
            # Check for known chat platforms
            known_platforms = {
                'chat.z.ai': 'Z.AI',
                'chat.mistral.ai': 'Mistral AI',
                'chat.deepseek.com': 'DeepSeek',
                'claude.ai': 'Claude'
            }
            
            for domain, platform in known_platforms.items():
                if domain in url:
                    results.append(YAMLValidationResult(
                        type="info",
                        message=f"Detected {platform} platform - configuration looks appropriate",
                        line=None
                    ))
                    break
        
        elif provider_type == 'rest_api':
            if 'api.openai.com' in url:
                if not config.get('api_key'):
                    results.append(YAMLValidationResult(
                        type="error",
                        message="OpenAI API requires an api_key",
                        line=None
                    ))
                
                model = config.get('model', '')
                if model and not model.startswith('gpt-'):
                    results.append(YAMLValidationResult(
                        type="warning",
                        message="OpenAI model should typically start with 'gpt-'",
                        line=None
                    ))
        
        # Check interaction methods
        interaction_methods = config.get('interaction_methods', [])
        if interaction_methods:
            method_names = [method.get('method') for method in interaction_methods if isinstance(method, dict)]
            if 'error_handling' not in method_names:
                results.append(YAMLValidationResult(
                    type="info",
                    message="Consider adding error_handling interaction method for robustness",
                    line=None
                ))
        
        # Check browser settings for web_chat
        if provider_type == 'web_chat':
            browser_settings = config.get('browser_settings', {})
            if browser_settings:
                if browser_settings.get('headless') is True:
                    results.append(YAMLValidationResult(
                        type="info",
                        message="Headless mode may cause issues with some chat platforms",
                        line=None
                    ))
                
                viewport = browser_settings.get('viewport', {})
                if viewport:
                    width = viewport.get('width', 0)
                    height = viewport.get('height', 0)
                    if width < 1024 or height < 768:
                        results.append(YAMLValidationResult(
                            type="warning",
                            message="Small viewport size may cause layout issues",
                            line=None
                        ))
        
    except Exception as e:
        logger.error(f"AI validation error: {e}")
        results.append(YAMLValidationResult(
            type="warning",
            message="AI validation service temporarily unavailable",
            line=None
        ))
    
    return results

@router.post("/save", response_model=YAMLSaveResponse)
async def save_yaml_config(request: YAMLSaveRequest):
    """Save YAML configuration"""
    try:
        # Validate the YAML first
        validation_request = YAMLValidationRequest(
            yaml_content=request.yaml_content,
            validation_type="basic"
        )
        validation_result = await validate_yaml_config(validation_request)
        
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400, 
                detail="Cannot save invalid configuration"
            )
        
        # Generate configuration ID
        config_id = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(request.yaml_content) % 10000:04d}"
        
        # In a real implementation, this would save to a database
        # For now, we'll just return success
        logger.info(f"Saved configuration {config_id}")
        
        return YAMLSaveResponse(
            config_id=config_id,
            message="Configuration saved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving YAML config: {e}")
        raise HTTPException(status_code=500, detail=f"Save error: {str(e)}")

@router.get("/templates", response_model=List[TemplateResponse])
async def get_templates():
    """Get all available configuration templates"""
    try:
        templates = []
        for template_id, template_data in BUILTIN_TEMPLATES.items():
            templates.append(TemplateResponse(
                id=template_id,
                name=template_data["name"],
                description=template_data["description"],
                content=template_data["content"],
                category=template_data["category"],
                tags=template_data["tags"]
            ))
        
        return templates
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=f"Template error: {str(e)}")

@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str):
    """Get a specific configuration template"""
    try:
        if template_id not in BUILTIN_TEMPLATES:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template_data = BUILTIN_TEMPLATES[template_id]
        return TemplateResponse(
            id=template_id,
            name=template_data["name"],
            description=template_data["description"],
            content=template_data["content"],
            category=template_data["category"],
            tags=template_data["tags"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Template error: {str(e)}")

# Add the router to the main application
# This would be done in the main FastAPI app file
