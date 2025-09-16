"""
AI-Assisted YAML Configuration Parser and Validator
Uses Codegen API for intelligent validation and web interface abstraction
"""

import yaml
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class InterfaceElement(Enum):
    """Standard web chat interface elements"""
    TEXT_INPUT = "text_input"
    SEND_BUTTON = "send_button"
    RESPONSE_AREA = "response_area"
    NEW_CONVERSATION = "new_conversation"

class ButtonState(Enum):
    """Send button states"""
    DEFAULT = "default"
    BUSY = "busy"
    DISABLED = "disabled"

@dataclass
class WebInterfaceAbstraction:
    """Abstract representation of a web chat interface"""
    name: str
    url: str
    elements: Dict[InterfaceElement, Dict[str, Any]]
    auth_method: str
    session_persistence: bool
    fingerprint_required: bool
    proxy_support: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert enum keys to strings
        result['elements'] = {elem.value: data for elem, data in self.elements.items()}
        return result

@dataclass
class YAMLConfig:
    """Parsed YAML configuration"""
    name: str
    url: str
    auth_email: Optional[str] = None
    auth_password: Optional[str] = None
    max_autoscale_parallel: int = 1
    save_cookies_for_future_use: bool = True
    create_unique_fingerprint_sandbox_deployment_snapshot: bool = True
    use_proxy: bool = False
    custom_selectors: Optional[Dict[str, str]] = None
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'YAMLConfig':
        """Parse YAML content into configuration object"""
        try:
            data = yaml.safe_load(yaml_content)
            
            # Handle different YAML formats and normalize keys
            normalized_data = {}
            for key, value in data.items():
                # Normalize key names
                key_lower = key.lower().replace(' ', '_').replace('-', '_')
                
                # Map common variations
                key_mapping = {
                    'url': 'url',
                    'name': 'name',
                    'authemail': 'auth_email',
                    'auth_email': 'auth_email',
                    'authpassword': 'auth_password',
                    'auth_password': 'auth_password',
                    'maxautoscaleparallel': 'max_autoscale_parallel',
                    'max_autoscale_parallel': 'max_autoscale_parallel',
                    'savecookiesforfutureuse': 'save_cookies_for_future_use',
                    'save_cookies_for_future_use': 'save_cookies_for_future_use',
                    'createuniquefingerprintsandboxdeploymentsnapshot': 'create_unique_fingerprint_sandbox_deployment_snapshot',
                    'create_unique_fingerprint_sandbox_deployment_snapshot': 'create_unique_fingerprint_sandbox_deployment_snapshot',
                    'useproxy': 'use_proxy',
                    'use_proxy': 'use_proxy',
                    'custom_selectors': 'custom_selectors'
                }
                
                mapped_key = key_mapping.get(key_lower, key_lower)
                
                # Convert string boolean values
                if isinstance(value, str):
                    if value.lower() in ['yes', 'true', '1']:
                        value = True
                    elif value.lower() in ['no', 'false', '0']:
                        value = False
                    elif value.isdigit():
                        value = int(value)
                
                normalized_data[mapped_key] = value
            
            return cls(**normalized_data)
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except TypeError as e:
            raise ValueError(f"Invalid configuration structure: {e}")

class AIAssistedYAMLValidator:
    """AI-powered YAML validator using Codegen API"""
    
    def __init__(self, codegen_api_url: str, codegen_token: str):
        self.codegen_api_url = codegen_api_url.rstrip('/')
        self.codegen_token = codegen_token
        self.session = None
        
        # Default interface methodologies for different providers
        self.default_methodologies = {
            'z.ai': {
                'selectors': {
                    'text_input': 'textarea[placeholder*="message"], input[type="text"]',
                    'send_button': 'button[type="submit"], button:contains("Send")',
                    'response_area': '.message-content, .response-text, .chat-message',
                    'new_conversation': 'button:contains("New"), .new-chat, .start-new'
                },
                'interaction_methods': [
                    'direct_api_intercept',
                    'dom_manipulation',
                    'event_simulation',
                    'websocket_monitoring'
                ]
            },
            'mistral': {
                'selectors': {
                    'text_input': 'textarea, input[type="text"]',
                    'send_button': 'button[type="submit"], .send-btn',
                    'response_area': '.message, .response, .chat-content',
                    'new_conversation': '.new-chat, button:contains("New")'
                },
                'interaction_methods': [
                    'dom_manipulation',
                    'direct_api_intercept',
                    'event_simulation',
                    'form_submission'
                ]
            },
            'deepseek': {
                'selectors': {
                    'text_input': 'textarea[placeholder*="Ask"], input.chat-input',
                    'send_button': 'button.send-button, button[aria-label*="Send"]',
                    'response_area': '.message-content, .ai-response',
                    'new_conversation': '.new-conversation, button:contains("New Chat")'
                },
                'interaction_methods': [
                    'direct_api_intercept',
                    'websocket_monitoring',
                    'dom_manipulation',
                    'event_simulation'
                ]
            },
            'claude': {
                'selectors': {
                    'text_input': 'textarea[placeholder*="Talk"], .chat-input textarea',
                    'send_button': 'button[aria-label*="Send"], .send-button',
                    'response_area': '.message-content, .claude-response',
                    'new_conversation': 'button:contains("New conversation")'
                },
                'interaction_methods': [
                    'direct_api_intercept',
                    'dom_manipulation',
                    'websocket_monitoring',
                    'event_simulation'
                ]
            },
            'default': {
                'selectors': {
                    'text_input': 'textarea, input[type="text"], .chat-input',
                    'send_button': 'button[type="submit"], .send, .submit, button:contains("Send")',
                    'response_area': '.message, .response, .chat-message, .ai-response',
                    'new_conversation': '.new-chat, .new-conversation, button:contains("New")'
                },
                'interaction_methods': [
                    'dom_manipulation',
                    'direct_api_intercept',
                    'event_simulation',
                    'form_submission'
                ]
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def validate_with_ai(self, config: YAMLConfig) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Use Codegen API to validate configuration and suggest improvements"""
        
        validation_prompt = f"""
        Please validate this AI endpoint configuration and provide suggestions:
        
        Configuration:
        - Name: {config.name}
        - URL: {config.url}
        - Authentication: {'Email/Password' if config.auth_email else 'None'}
        - Max Parallel: {config.max_autoscale_parallel}
        - Save Cookies: {config.save_cookies_for_future_use}
        - Unique Fingerprint: {config.create_unique_fingerprint_sandbox_deployment_snapshot}
        - Use Proxy: {config.use_proxy}
        
        Please check:
        1. Is the URL format valid and accessible?
        2. Are the authentication requirements appropriate?
        3. Is the scaling configuration reasonable?
        4. Are there any security concerns?
        5. Suggest optimal selectors for web interface elements
        
        Respond with JSON format:
        {{
            "valid": true/false,
            "issues": ["list of issues"],
            "suggestions": {{
                "selectors": {{"text_input": "selector", "send_button": "selector", ...}},
                "optimizations": ["list of optimizations"],
                "security_recommendations": ["list of security tips"]
            }}
        }}
        """
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = {
                'Authorization': f'Bearer {self.codegen_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messages': [
                    {
                        'role': 'user',
                        'content': validation_prompt
                    }
                ],
                'model': 'gpt-4',
                'temperature': 0.1
            }
            
            async with self.session.post(
                f'{self.codegen_api_url}/v1/chat/completions',
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    ai_response = result['choices'][0]['message']['content']
                    
                    # Try to parse JSON response
                    try:
                        validation_result = json.loads(ai_response)
                        return (
                            validation_result.get('valid', False),
                            validation_result.get('issues', []),
                            validation_result.get('suggestions', {})
                        )
                    except json.JSONDecodeError:
                        # Fallback to text parsing
                        return self._parse_text_response(ai_response)
                else:
                    logger.error(f"Codegen API error: {response.status}")
                    return False, [f"API validation failed: {response.status}"], {}
                    
        except Exception as e:
            logger.error(f"AI validation error: {e}")
            return False, [f"Validation error: {str(e)}"], {}
    
    def _parse_text_response(self, response: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Fallback text parsing for AI responses"""
        issues = []
        suggestions = {}
        
        # Simple text parsing logic
        valid = "valid: true" in response.lower() or "configuration is valid" in response.lower()
        
        # Extract issues (basic pattern matching)
        if "issues:" in response.lower():
            issues_section = response.lower().split("issues:")[1].split("suggestions:")[0]
            issues = [line.strip("- ").strip() for line in issues_section.split('\n') if line.strip()]
        
        return valid, issues, suggestions
    
    def detect_provider_type(self, url: str) -> str:
        """Detect provider type from URL"""
        url_lower = url.lower()
        
        if 'z.ai' in url_lower or 'zai' in url_lower:
            return 'z.ai'
        elif 'mistral' in url_lower:
            return 'mistral'
        elif 'deepseek' in url_lower:
            return 'deepseek'
        elif 'claude' in url_lower or 'anthropic' in url_lower:
            return 'claude'
        else:
            return 'default'
    
    def create_web_interface_abstraction(self, config: YAMLConfig, ai_suggestions: Dict[str, Any] = None) -> WebInterfaceAbstraction:
        """Create web interface abstraction with AI-suggested selectors"""
        
        provider_type = self.detect_provider_type(config.url)
        default_methodology = self.default_methodologies.get(provider_type, self.default_methodologies['default'])
        
        # Use AI suggestions if available, otherwise use defaults
        selectors = ai_suggestions.get('selectors', {}) if ai_suggestions else {}
        if not selectors:
            selectors = default_methodology['selectors']
        
        # Create interface elements with states and behaviors
        elements = {
            InterfaceElement.TEXT_INPUT: {
                'selector': selectors.get('text_input', default_methodology['selectors']['text_input']),
                'type': 'textarea',
                'placeholder': 'Type your message...',
                'required': True,
                'validation': 'non_empty'
            },
            InterfaceElement.SEND_BUTTON: {
                'selector': selectors.get('send_button', default_methodology['selectors']['send_button']),
                'type': 'button',
                'states': {
                    ButtonState.DEFAULT.value: {
                        'enabled': True,
                        'text': 'Send',
                        'class': 'send-button'
                    },
                    ButtonState.BUSY.value: {
                        'enabled': False,
                        'text': 'Sending...',
                        'class': 'send-button busy'
                    },
                    ButtonState.DISABLED.value: {
                        'enabled': False,
                        'text': 'Send',
                        'class': 'send-button disabled'
                    }
                }
            },
            InterfaceElement.RESPONSE_AREA: {
                'selector': selectors.get('response_area', default_methodology['selectors']['response_area']),
                'type': 'div',
                'scrollable': True,
                'auto_scroll': True,
                'content_type': 'html'
            },
            InterfaceElement.NEW_CONVERSATION: {
                'selector': selectors.get('new_conversation', default_methodology['selectors']['new_conversation']),
                'type': 'button',
                'action': 'clear_session',
                'confirmation': True
            }
        }
        
        return WebInterfaceAbstraction(
            name=config.name,
            url=config.url,
            elements=elements,
            auth_method='email_password' if config.auth_email else 'none',
            session_persistence=config.save_cookies_for_future_use,
            fingerprint_required=config.create_unique_fingerprint_sandbox_deployment_snapshot,
            proxy_support=config.use_proxy
        )
    
    async def validate_and_create_abstraction(self, yaml_content: str) -> Tuple[bool, YAMLConfig, WebInterfaceAbstraction, List[str]]:
        """Complete validation and abstraction creation pipeline"""
        
        try:
            # Parse YAML
            config = YAMLConfig.from_yaml(yaml_content)
            
            # AI-assisted validation
            is_valid, issues, suggestions = await self.validate_with_ai(config)
            
            # Create web interface abstraction
            abstraction = self.create_web_interface_abstraction(config, suggestions)
            
            return is_valid, config, abstraction, issues
            
        except Exception as e:
            logger.error(f"Validation pipeline error: {e}")
            return False, None, None, [str(e)]

class YAMLConfigManager:
    """Manager for YAML configurations and abstractions"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.abstractions_dir = self.config_dir / "abstractions"
        self.abstractions_dir.mkdir(exist_ok=True)
    
    def save_config(self, config: YAMLConfig, filename: str = None) -> str:
        """Save YAML configuration to file"""
        if not filename:
            filename = f"{config.name.lower().replace(' ', '_')}.yaml"
        
        config_path = self.config_dir / filename
        
        config_dict = asdict(config)
        # Remove None values
        config_dict = {k: v for k, v in config_dict.items() if v is not None}
        
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
        
        return str(config_path)
    
    def save_abstraction(self, abstraction: WebInterfaceAbstraction, filename: str = None) -> str:
        """Save web interface abstraction to JSON file"""
        if not filename:
            filename = f"{abstraction.name.lower().replace(' ', '_')}_abstraction.json"
        
        abstraction_path = self.abstractions_dir / filename
        
        with open(abstraction_path, 'w') as f:
            json.dump(abstraction.to_dict(), f, indent=2)
        
        return str(abstraction_path)
    
    def load_config(self, filename: str) -> YAMLConfig:
        """Load YAML configuration from file"""
        config_path = self.config_dir / filename
        
        with open(config_path, 'r') as f:
            yaml_content = f.read()
        
        return YAMLConfig.from_yaml(yaml_content)
    
    def load_abstraction(self, filename: str) -> WebInterfaceAbstraction:
        """Load web interface abstraction from JSON file"""
        abstraction_path = self.abstractions_dir / filename
        
        with open(abstraction_path, 'r') as f:
            data = json.load(f)
        
        # Convert string keys back to enums
        elements = {}
        for elem_str, elem_data in data['elements'].items():
            elem_enum = InterfaceElement(elem_str)
            elements[elem_enum] = elem_data
        
        data['elements'] = elements
        
        return WebInterfaceAbstraction(**data)
    
    def list_configs(self) -> List[str]:
        """List all available configurations"""
        return [f.name for f in self.config_dir.glob("*.yaml")]
    
    def list_abstractions(self) -> List[str]:
        """List all available abstractions"""
        return [f.name for f in self.abstractions_dir.glob("*_abstraction.json")]

# Example usage and testing
async def main():
    """Example usage of the AI-assisted YAML validator"""
    
    # Example YAML configurations
    zai_config = """
name: Zaitest1integration
URL: chat.z.ai
authemail: 'emailforlogin'
authpassword: 'passwordlogin'
maxautoscaleparallel: '20'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: yes
useproxy: no
"""
    
    mistral_config = """
name: testmistral1
URL: chat.mistral.ai
authemail: 'emailforlogin'
authpassword: 'passwordlogin'
maxautoscaleparallel: '3'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: yes
useproxy: no
"""
    
    # Initialize validator (replace with actual Codegen API credentials)
    async with AIAssistedYAMLValidator(
        codegen_api_url="https://codegen-sh--rest-api.modal.run",
        codegen_token="your-token-here"
    ) as validator:
        
        # Validate and create abstractions
        for name, yaml_content in [("Z.ai", zai_config), ("Mistral", mistral_config)]:
            print(f"\n=== Validating {name} Configuration ===")
            
            is_valid, config, abstraction, issues = await validator.validate_and_create_abstraction(yaml_content)
            
            print(f"Valid: {is_valid}")
            if issues:
                print(f"Issues: {issues}")
            
            if config and abstraction:
                print(f"Configuration: {config.name} -> {config.url}")
                print(f"Abstraction created with {len(abstraction.elements)} elements")
                
                # Save configurations
                manager = YAMLConfigManager()
                config_path = manager.save_config(config)
                abstraction_path = manager.save_abstraction(abstraction)
                
                print(f"Saved config: {config_path}")
                print(f"Saved abstraction: {abstraction_path}")

if __name__ == "__main__":
    asyncio.run(main())
