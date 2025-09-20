"""
Configuration Management API Endpoints
Handles YAML configuration validation, saving, and management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import os

from ..config.yaml_parser import (
    AIAssistedYAMLValidator, 
    YAMLConfigManager, 
    YAMLConfig
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["configuration"])

# Pydantic models for API requests/responses
class ValidateConfigRequest(BaseModel):
    yaml_content: str

class ValidateConfigResponse(BaseModel):
    valid: bool
    config: Optional[Dict[str, Any]] = None
    abstraction: Optional[Dict[str, Any]] = None
    issues: List[str] = []
    suggestions: Dict[str, Any] = {}

class SaveConfigRequest(BaseModel):
    yaml_content: str
    validation_results: Optional[Dict[str, Any]] = None

class SaveConfigResponse(BaseModel):
    success: bool
    config_path: str
    abstraction_path: Optional[str] = None
    message: str

class ConfigListResponse(BaseModel):
    configs: List[Dict[str, Any]]
    abstractions: List[Dict[str, Any]]

# Dependency to get AI validator
async def get_ai_validator() -> AIAssistedYAMLValidator:
    """Get AI validator instance with proper configuration"""
    codegen_api_url = os.getenv("CODEGEN_API_URL", "https://codegen-sh--rest-api.modal.run")
    codegen_token = os.getenv("CODEGEN_API_TOKEN", "")
    
    if not codegen_token:
        logger.warning("CODEGEN_API_TOKEN not set, AI validation may not work")
    
    return AIAssistedYAMLValidator(codegen_api_url, codegen_token)

# Dependency to get config manager
def get_config_manager() -> YAMLConfigManager:
    """Get configuration manager instance"""
    config_dir = os.getenv("CONFIG_DIR", "configs")
    return YAMLConfigManager(config_dir)

@router.post("/validate", response_model=ValidateConfigResponse)
async def validate_configuration(
    request: ValidateConfigRequest,
    validator: AIAssistedYAMLValidator = Depends(get_ai_validator)
):
    """
    Validate YAML configuration using AI assistance
    
    This endpoint:
    1. Parses the YAML content
    2. Uses Codegen API for intelligent validation
    3. Creates web interface abstraction
    4. Returns validation results with suggestions
    """
    try:
        async with validator:
            is_valid, config, abstraction, issues = await validator.validate_and_create_abstraction(
                request.yaml_content
            )
            
            # Convert objects to dictionaries for JSON response
            config_dict = None
            abstraction_dict = None
            
            if config:
                config_dict = {
                    "name": config.name,
                    "url": config.url,
                    "auth_email": config.auth_email,
                    "max_autoscale_parallel": config.max_autoscale_parallel,
                    "save_cookies_for_future_use": config.save_cookies_for_future_use,
                    "create_unique_fingerprint_sandbox_deployment_snapshot": config.create_unique_fingerprint_sandbox_deployment_snapshot,
                    "use_proxy": config.use_proxy,
                    "custom_selectors": config.custom_selectors
                }
            
            if abstraction:
                abstraction_dict = abstraction.to_dict()
            
            return ValidateConfigResponse(
                valid=is_valid,
                config=config_dict,
                abstraction=abstraction_dict,
                issues=issues,
                suggestions={}  # Will be populated by AI validation
            )
            
    except Exception as e:
        logger.error(f"Configuration validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Validation failed: {str(e)}"
        )

@router.post("/save", response_model=SaveConfigResponse)
async def save_configuration(
    request: SaveConfigRequest,
    config_manager: YAMLConfigManager = Depends(get_config_manager),
    validator: AIAssistedYAMLValidator = Depends(get_ai_validator)
):
    """
    Save validated YAML configuration and create abstraction
    
    This endpoint:
    1. Validates the configuration if not already validated
    2. Saves the YAML configuration to file
    3. Saves the web interface abstraction
    4. Returns file paths and success status
    """
    try:
        # If validation results are provided, use them; otherwise validate
        if request.validation_results:
            # Use existing validation results
            config_dict = request.validation_results.get('config')
            abstraction_dict = request.validation_results.get('abstraction')
            
            if not config_dict:
                raise ValueError("Invalid validation results: missing config")
            
            # Reconstruct config object
            config = YAMLConfig(
                name=config_dict['name'],
                url=config_dict['url'],
                auth_email=config_dict.get('auth_email'),
                auth_password=config_dict.get('auth_password'),
                max_autoscale_parallel=config_dict.get('max_autoscale_parallel', 1),
                save_cookies_for_future_use=config_dict.get('save_cookies_for_future_use', True),
                create_unique_fingerprint_sandbox_deployment_snapshot=config_dict.get('create_unique_fingerprint_sandbox_deployment_snapshot', True),
                use_proxy=config_dict.get('use_proxy', False),
                custom_selectors=config_dict.get('custom_selectors')
            )
            
            # Reconstruct abstraction if available
            abstraction = None
            if abstraction_dict:
                # This would need proper reconstruction logic
                pass
                
        else:
            # Validate first
            async with validator:
                is_valid, config, abstraction, issues = await validator.validate_and_create_abstraction(
                    request.yaml_content
                )
                
                if not is_valid:
                    raise ValueError(f"Configuration is invalid: {', '.join(issues)}")
        
        # Save configuration
        config_path = config_manager.save_config(config)
        
        # Save abstraction if available
        abstraction_path = None
        if abstraction:
            abstraction_path = config_manager.save_abstraction(abstraction)
        
        return SaveConfigResponse(
            success=True,
            config_path=config_path,
            abstraction_path=abstraction_path,
            message=f"Configuration '{config.name}' saved successfully"
        )
        
    except Exception as e:
        logger.error(f"Configuration save error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Save failed: {str(e)}"
        )

@router.get("/list", response_model=ConfigListResponse)
async def list_configurations(
    config_manager: YAMLConfigManager = Depends(get_config_manager)
):
    """
    List all available configurations and abstractions
    
    Returns:
    - List of saved YAML configurations
    - List of saved web interface abstractions
    """
    try:
        configs = []
        abstractions = []
        
        # Get configuration files
        config_files = config_manager.list_configs()
        for config_file in config_files:
            try:
                config = config_manager.load_config(config_file)
                configs.append({
                    "filename": config_file,
                    "name": config.name,
                    "url": config.url,
                    "type": "web_chat" if config.auth_email else "rest_api",
                    "max_parallel": config.max_autoscale_parallel,
                    "use_proxy": config.use_proxy
                })
            except Exception as e:
                logger.warning(f"Failed to load config {config_file}: {e}")
        
        # Get abstraction files
        abstraction_files = config_manager.list_abstractions()
        for abs_file in abstraction_files:
            try:
                abstraction = config_manager.load_abstraction(abs_file)
                abstractions.append({
                    "filename": abs_file,
                    "name": abstraction.name,
                    "url": abstraction.url,
                    "auth_method": abstraction.auth_method,
                    "elements_count": len(abstraction.elements)
                })
            except Exception as e:
                logger.warning(f"Failed to load abstraction {abs_file}: {e}")
        
        return ConfigListResponse(
            configs=configs,
            abstractions=abstractions
        )
        
    except Exception as e:
        logger.error(f"List configurations error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list configurations: {str(e)}"
        )

@router.get("/templates")
async def get_configuration_templates():
    """
    Get available configuration templates
    
    Returns built-in templates for different AI providers
    """
    templates = {
        "z.ai": {
            "name": "Z.ai Chat Interface",
            "description": "Template for Z.ai web chat integration",
            "provider_type": "web_chat",
            "template": {
                "name": "ZaiIntegration",
                "URL": "chat.z.ai",
                "authemail": "your-email@example.com",
                "authpassword": "your-password",
                "maxautoscaleparallel": "20",
                "savecookiesforfutureuse": "yes",
                "createuniquefingerprintsandboxdeploymentsnapshot": True,
                "useproxy": False,
                "custom_selectors": {
                    "text_input": "textarea[placeholder*=\"message\"]",
                    "send_button": "button[type=\"submit\"]",
                    "response_area": ".message-content",
                    "new_conversation": ".new-chat"
                }
            }
        },
        "mistral": {
            "name": "Mistral AI Chat",
            "description": "Template for Mistral AI web chat integration",
            "provider_type": "web_chat",
            "template": {
                "name": "MistralIntegration",
                "URL": "chat.mistral.ai",
                "authemail": "your-email@example.com",
                "authpassword": "your-password",
                "maxautoscaleparallel": "3",
                "savecookiesforfutureuse": "yes",
                "createuniquefingerprintsandboxdeploymentsnapshot": True,
                "useproxy": False,
                "custom_selectors": {
                    "text_input": "textarea",
                    "send_button": ".send-btn",
                    "response_area": ".chat-content",
                    "new_conversation": ".new-chat"
                }
            }
        },
        "deepseek": {
            "name": "DeepSeek Chat",
            "description": "Template for DeepSeek web chat integration",
            "provider_type": "web_chat",
            "template": {
                "name": "DeepSeekIntegration",
                "URL": "chat.deepseek.com",
                "authemail": "your-email@example.com",
                "authpassword": "your-password",
                "maxautoscaleparallel": "20",
                "savecookiesforfutureuse": "yes",
                "createuniquefingerprintsandboxdeploymentsnapshot": True,
                "useproxy": False,
                "custom_selectors": {
                    "text_input": "textarea[placeholder*=\"Ask\"]",
                    "send_button": "button.send-button",
                    "response_area": ".ai-response",
                    "new_conversation": ".new-conversation"
                }
            }
        },
        "claude": {
            "name": "Claude Chat",
            "description": "Template for Claude/Anthropic web chat integration",
            "provider_type": "web_chat",
            "template": {
                "name": "ClaudeIntegration",
                "URL": "claude.ai",
                "authemail": "your-email@example.com",
                "authpassword": "your-password",
                "maxautoscaleparallel": "5",
                "savecookiesforfutureuse": "yes",
                "createuniquefingerprintsandboxdeploymentsnapshot": True,
                "useproxy": False,
                "custom_selectors": {
                    "text_input": "textarea[placeholder*=\"Talk\"]",
                    "send_button": "button[aria-label*=\"Send\"]",
                    "response_area": ".claude-response",
                    "new_conversation": "button:contains(\"New conversation\")"
                }
            }
        },
        "openai": {
            "name": "OpenAI API",
            "description": "Template for OpenAI REST API integration",
            "provider_type": "rest_api",
            "template": {
                "name": "OpenAIIntegration",
                "URL": "https://api.openai.com",
                "api_key": "your-openai-api-key",
                "maxautoscaleparallel": "10",
                "savecookiesforfutureuse": False,
                "createuniquefingerprintsandboxdeploymentsnapshot": False,
                "useproxy": False,
                "endpoint_config": {
                    "chat_completions": "/v1/chat/completions",
                    "models": "/v1/models",
                    "headers": {
                        "Authorization": "Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                }
            }
        },
        "codegen": {
            "name": "Codegen API",
            "description": "Template for Codegen API integration",
            "provider_type": "rest_api",
            "template": {
                "name": "CodegenIntegration",
                "URL": "https://codegen-sh--rest-api.modal.run",
                "api_key": "your-codegen-api-key",
                "maxautoscaleparallel": "5",
                "savecookiesforfutureuse": False,
                "createuniquefingerprintsandboxdeploymentsnapshot": False,
                "useproxy": False,
                "endpoint_config": {
                    "chat_completions": "/v1/chat/completions",
                    "models": "/v1/models",
                    "headers": {
                        "Authorization": "Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                }
            }
        }
    }
    
    return {"templates": templates}

@router.delete("/config/{config_name}")
async def delete_configuration(
    config_name: str,
    config_manager: YAMLConfigManager = Depends(get_config_manager)
):
    """
    Delete a configuration and its associated abstraction
    """
    try:
        config_file = f"{config_name}.yaml"
        abstraction_file = f"{config_name}_abstraction.json"
        
        # Delete configuration file
        config_path = config_manager.config_dir / config_file
        if config_path.exists():
            config_path.unlink()
        
        # Delete abstraction file
        abstraction_path = config_manager.abstractions_dir / abstraction_file
        if abstraction_path.exists():
            abstraction_path.unlink()
        
        return {"success": True, "message": f"Configuration '{config_name}' deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete configuration error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete configuration: {str(e)}"
        )

@router.get("/config/{config_name}")
async def get_configuration(
    config_name: str,
    config_manager: YAMLConfigManager = Depends(get_config_manager)
):
    """
    Get a specific configuration by name
    """
    try:
        config_file = f"{config_name}.yaml"
        config = config_manager.load_config(config_file)
        
        # Also try to load associated abstraction
        abstraction = None
        try:
            abstraction_file = f"{config_name}_abstraction.json"
            abstraction = config_manager.load_abstraction(abstraction_file)
        except:
            pass  # Abstraction is optional
        
        return {
            "config": {
                "name": config.name,
                "url": config.url,
                "auth_email": config.auth_email,
                "max_autoscale_parallel": config.max_autoscale_parallel,
                "save_cookies_for_future_use": config.save_cookies_for_future_use,
                "create_unique_fingerprint_sandbox_deployment_snapshot": config.create_unique_fingerprint_sandbox_deployment_snapshot,
                "use_proxy": config.use_proxy,
                "custom_selectors": config.custom_selectors
            },
            "abstraction": abstraction.to_dict() if abstraction else None
        }
        
    except Exception as e:
        logger.error(f"Get configuration error: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Configuration '{config_name}' not found: {str(e)}"
        )
