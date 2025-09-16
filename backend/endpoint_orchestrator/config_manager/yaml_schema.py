"""
YAML Configuration Schema for AI Endpoint Orchestrator.

Defines the structure and validation for endpoint configurations
supporting both REST APIs and web chat interfaces.
"""

import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class EndpointType(str, Enum):
    """Types of endpoints supported by the orchestrator."""
    REST_API = "rest_api"
    WEB_CHAT = "web_chat"
    HYBRID = "hybrid"


class AuthType(str, Enum):
    """Authentication types for endpoints."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH = "oauth"
    COOKIE_SESSION = "cookie_session"
    CUSTOM = "custom"


@dataclass
class ProxyConfig:
    """Proxy configuration for web chat endpoints."""
    enabled: bool = False
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    type: str = "http"  # http, socks5, etc.


@dataclass
class BrowserConfig:
    """Browser automation configuration."""
    headless: bool = True
    stealth_mode: bool = True
    user_agent: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30
    save_cookies: bool = True
    create_unique_fingerprint: bool = True
    sandbox_deployment: bool = True


@dataclass
class WebChatSelectors:
    """CSS selectors for web chat interface elements."""
    input_field: Optional[str] = None
    send_button: Optional[str] = None
    response_area: Optional[str] = None
    new_chat_button: Optional[str] = None
    model_selector: Optional[str] = None
    login_email: Optional[str] = None
    login_password: Optional[str] = None
    login_submit: Optional[str] = None


@dataclass
class ScalingConfig:
    """Auto-scaling configuration for endpoints."""
    enabled: bool = True
    min_instances: int = 1
    max_instances: int = 10
    max_autoscale_parallel: int = 5
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    cooldown_seconds: int = 300


@dataclass
class RestApiConfig:
    """Configuration for REST API endpoints."""
    base_url: str
    auth_type: AuthType = AuthType.API_KEY
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    max_retries: int = 3
    rate_limit_per_minute: Optional[int] = None


@dataclass
class WebChatConfig:
    """Configuration for web chat endpoints."""
    url: str
    auth_email: Optional[str] = None
    auth_password: Optional[str] = None
    login_url: Optional[str] = None
    selectors: WebChatSelectors = field(default_factory=WebChatSelectors)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    wait_for_response: int = 10
    max_conversation_length: int = 100


@dataclass
class EndpointConfig:
    """Main endpoint configuration supporting both REST API and web chat."""
    name: str
    endpoint_type: EndpointType
    model_name: str
    description: Optional[str] = None
    enabled: bool = True
    priority: int = 1
    
    # Scaling configuration
    scaling: ScalingConfig = field(default_factory=ScalingConfig)
    
    # Type-specific configurations
    rest_api: Optional[RestApiConfig] = None
    web_chat: Optional[WebChatConfig] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.endpoint_type == EndpointType.REST_API and not self.rest_api:
            raise ValueError("REST API configuration required for REST API endpoints")
        if self.endpoint_type == EndpointType.WEB_CHAT and not self.web_chat:
            raise ValueError("Web chat configuration required for web chat endpoints")
        if self.endpoint_type == EndpointType.HYBRID and not (self.rest_api and self.web_chat):
            raise ValueError("Both REST API and web chat configurations required for hybrid endpoints")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EndpointConfig':
        """Create configuration from dictionary."""
        # Handle nested objects
        if 'scaling' in data and isinstance(data['scaling'], dict):
            data['scaling'] = ScalingConfig(**data['scaling'])
        
        if 'rest_api' in data and isinstance(data['rest_api'], dict):
            data['rest_api'] = RestApiConfig(**data['rest_api'])
        
        if 'web_chat' in data and isinstance(data['web_chat'], dict):
            web_chat_data = data['web_chat'].copy()
            
            # Handle nested browser config
            if 'browser' in web_chat_data and isinstance(web_chat_data['browser'], dict):
                web_chat_data['browser'] = BrowserConfig(**web_chat_data['browser'])
            
            # Handle nested proxy config
            if 'proxy' in web_chat_data and isinstance(web_chat_data['proxy'], dict):
                web_chat_data['proxy'] = ProxyConfig(**web_chat_data['proxy'])
            
            # Handle nested selectors
            if 'selectors' in web_chat_data and isinstance(web_chat_data['selectors'], dict):
                web_chat_data['selectors'] = WebChatSelectors(**web_chat_data['selectors'])
            
            data['web_chat'] = WebChatConfig(**web_chat_data)
        
        return cls(**data)


class YAMLConfigManager:
    """Manager for loading and validating YAML endpoint configurations."""
    
    def __init__(self, config_dir: str = "configs/endpoints"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.configs: Dict[str, EndpointConfig] = {}
    
    def load_config(self, file_path: Union[str, Path]) -> EndpointConfig:
        """Load a single YAML configuration file."""
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            # Convert YAML structure to our schema
            config_data = self._convert_yaml_to_config(yaml_data)
            config = EndpointConfig.from_dict(config_data)
            
            logger.info(f"Loaded configuration: {config.name} from {file_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")
            raise
    
    def load_all_configs(self) -> Dict[str, EndpointConfig]:
        """Load all YAML configuration files from the config directory."""
        configs = {}
        
        for yaml_file in self.config_dir.glob("*.yaml"):
            try:
                config = self.load_config(yaml_file)
                configs[config.name] = config
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
        
        for yml_file in self.config_dir.glob("*.yml"):
            try:
                config = self.load_config(yml_file)
                configs[config.name] = config
            except Exception as e:
                logger.error(f"Failed to load {yml_file}: {e}")
        
        self.configs = configs
        logger.info(f"Loaded {len(configs)} endpoint configurations")
        return configs
    
    def save_config(self, config: EndpointConfig, file_path: Optional[Union[str, Path]] = None) -> Path:
        """Save an endpoint configuration to YAML file."""
        if file_path is None:
            file_path = self.config_dir / f"{config.name.lower().replace(' ', '_')}.yaml"
        else:
            file_path = Path(file_path)
        
        # Convert config to YAML-friendly format
        yaml_data = self._convert_config_to_yaml(config)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, indent=2)
            
            logger.info(f"Saved configuration: {config.name} to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {file_path}: {e}")
            raise
    
    def _convert_yaml_to_config(self, yaml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert YAML data to EndpointConfig format."""
        config_data = {}
        
        # Basic fields
        config_data['name'] = yaml_data.get('name', 'Unnamed Endpoint')
        config_data['model_name'] = yaml_data.get('name', 'unknown-model')
        config_data['description'] = yaml_data.get('description')
        config_data['enabled'] = yaml_data.get('enabled', True)
        config_data['priority'] = yaml_data.get('priority', 1)
        
        # Determine endpoint type based on presence of URL or API configuration
        if 'url' in yaml_data or 'URL' in yaml_data:
            config_data['endpoint_type'] = EndpointType.WEB_CHAT
            config_data['web_chat'] = self._convert_webchat_yaml(yaml_data)
        elif 'api_url' in yaml_data or 'base_url' in yaml_data:
            config_data['endpoint_type'] = EndpointType.REST_API
            config_data['rest_api'] = self._convert_restapi_yaml(yaml_data)
        else:
            # Default to web chat if URL is present
            config_data['endpoint_type'] = EndpointType.WEB_CHAT
            config_data['web_chat'] = self._convert_webchat_yaml(yaml_data)
        
        # Scaling configuration
        scaling_config = {}
        if 'maxautoscaleparallel' in yaml_data:
            scaling_config['max_autoscale_parallel'] = int(yaml_data['maxautoscaleparallel'])
            scaling_config['max_instances'] = int(yaml_data['maxautoscaleparallel'])
        
        config_data['scaling'] = scaling_config
        
        return config_data
    
    def _convert_webchat_yaml(self, yaml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert YAML data to WebChatConfig format."""
        web_chat = {}
        
        # URL
        web_chat['url'] = yaml_data.get('url') or yaml_data.get('URL', '')
        
        # Authentication
        web_chat['auth_email'] = yaml_data.get('authemail')
        web_chat['auth_password'] = yaml_data.get('authpassword')
        
        # Browser configuration
        browser_config = {
            'save_cookies': yaml_data.get('savecookiesforfutureuse', 'yes').lower() == 'yes',
            'create_unique_fingerprint': yaml_data.get('createuniquefingerprintsandboxdeploymentsnapshot', 'yes').lower() == 'yes',
            'sandbox_deployment': yaml_data.get('createuniquefingerprintsandboxdeploymentsnapshot', 'yes').lower() == 'yes'
        }
        web_chat['browser'] = browser_config
        
        # Proxy configuration
        proxy_config = {
            'enabled': yaml_data.get('useproxy', 'no').lower() == 'yes'
        }
        web_chat['proxy'] = proxy_config
        
        return web_chat
    
    def _convert_restapi_yaml(self, yaml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert YAML data to RestApiConfig format."""
        rest_api = {}
        
        rest_api['base_url'] = yaml_data.get('api_url') or yaml_data.get('base_url', '')
        rest_api['api_key'] = yaml_data.get('api_key')
        rest_api['bearer_token'] = yaml_data.get('bearer_token')
        rest_api['timeout'] = yaml_data.get('timeout', 30)
        rest_api['max_retries'] = yaml_data.get('max_retries', 3)
        
        return rest_api
    
    def _convert_config_to_yaml(self, config: EndpointConfig) -> Dict[str, Any]:
        """Convert EndpointConfig to YAML-friendly format."""
        yaml_data = {
            'name': config.name,
            'description': config.description,
            'enabled': config.enabled,
            'priority': config.priority
        }
        
        if config.endpoint_type == EndpointType.WEB_CHAT and config.web_chat:
            yaml_data['URL'] = config.web_chat.url
            yaml_data['authemail'] = config.web_chat.auth_email
            yaml_data['authpassword'] = config.web_chat.auth_password
            yaml_data['maxautoscaleparallel'] = str(config.scaling.max_autoscale_parallel)
            yaml_data['savecookiesforfutureuse'] = 'yes' if config.web_chat.browser.save_cookies else 'no'
            yaml_data['createuniquefingerprintsandboxdeploymentsnapshot'] = 'yes' if config.web_chat.browser.create_unique_fingerprint else 'no'
            yaml_data['useproxy'] = 'yes' if config.web_chat.proxy.enabled else 'no'
        
        elif config.endpoint_type == EndpointType.REST_API and config.rest_api:
            yaml_data['api_url'] = config.rest_api.base_url
            yaml_data['api_key'] = config.rest_api.api_key
            yaml_data['bearer_token'] = config.rest_api.bearer_token
            yaml_data['timeout'] = config.rest_api.timeout
            yaml_data['max_retries'] = config.rest_api.max_retries
        
        return yaml_data
    
    def validate_config(self, config: EndpointConfig) -> List[str]:
        """Validate an endpoint configuration and return list of errors."""
        errors = []
        
        if not config.name:
            errors.append("Endpoint name is required")
        
        if not config.model_name:
            errors.append("Model name is required")
        
        if config.endpoint_type == EndpointType.WEB_CHAT:
            if not config.web_chat:
                errors.append("Web chat configuration is required for web chat endpoints")
            elif not config.web_chat.url:
                errors.append("URL is required for web chat endpoints")
        
        elif config.endpoint_type == EndpointType.REST_API:
            if not config.rest_api:
                errors.append("REST API configuration is required for REST API endpoints")
            elif not config.rest_api.base_url:
                errors.append("Base URL is required for REST API endpoints")
        
        return errors


# Example usage and factory functions
def create_zai_config(name: str, email: str, password: str, max_parallel: int = 20) -> EndpointConfig:
    """Create a Z.AI endpoint configuration."""
    return EndpointConfig(
        name=name,
        endpoint_type=EndpointType.WEB_CHAT,
        model_name=f"zai-{name.lower()}",
        description="Z.AI Web Chat Interface",
        web_chat=WebChatConfig(
            url="https://chat.z.ai",
            auth_email=email,
            auth_password=password,
            browser=BrowserConfig(
                save_cookies=True,
                create_unique_fingerprint=True,
                sandbox_deployment=True
            ),
            proxy=ProxyConfig(enabled=False)
        ),
        scaling=ScalingConfig(
            max_autoscale_parallel=max_parallel,
            max_instances=max_parallel
        )
    )


def create_deepseek_config(name: str, email: str, password: str, max_parallel: int = 20) -> EndpointConfig:
    """Create a DeepSeek endpoint configuration."""
    return EndpointConfig(
        name=name,
        endpoint_type=EndpointType.WEB_CHAT,
        model_name=f"deepseek-{name.lower()}",
        description="DeepSeek Web Chat Interface",
        web_chat=WebChatConfig(
            url="https://chat.deepseek.com",
            auth_email=email,
            auth_password=password,
            browser=BrowserConfig(
                save_cookies=True,
                create_unique_fingerprint=True,
                sandbox_deployment=True
            ),
            proxy=ProxyConfig(enabled=False)
        ),
        scaling=ScalingConfig(
            max_autoscale_parallel=max_parallel,
            max_instances=max_parallel
        )
    )


def create_openai_config(name: str, api_key: str) -> EndpointConfig:
    """Create an OpenAI REST API endpoint configuration."""
    return EndpointConfig(
        name=name,
        endpoint_type=EndpointType.REST_API,
        model_name=f"openai-{name.lower()}",
        description="OpenAI REST API",
        rest_api=RestApiConfig(
            base_url="https://api.openai.com/v1",
            auth_type=AuthType.BEARER_TOKEN,
            bearer_token=api_key,
            timeout=30,
            max_retries=3
        )
    )
