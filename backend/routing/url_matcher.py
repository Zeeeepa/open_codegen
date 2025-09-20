"""
URL Matcher - Intelligent URL pattern matching for automatic service detection
"""
import re
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class URLMatcher:
    """
    Matches URLs to known AI services and determines service types
    """
    
    def __init__(self):
        # Service patterns with metadata
        self.service_patterns = {
            # OpenAI
            'openai': {
                'patterns': [
                    r'.*chat\.openai\.com.*',
                    r'.*api\.openai\.com.*'
                ],
                'type': 'web_chat' if 'chat' in r'.*chat\.openai\.com.*' else 'rest_api',
                'priority': 85,
                'templates': ['openai_web', 'openai_api']
            },
            
            # DeepSeek
            'deepseek': {
                'patterns': [
                    r'.*chat\.deepseek\.com.*',
                    r'.*api\.deepseek\.com.*'
                ],
                'type': 'web_chat',
                'priority': 80,
                'templates': ['deepseek_web', 'deepseek_api']
            },
            
            # Z.ai
            'zai': {
                'patterns': [
                    r'.*chat\.z\.ai.*',
                    r'.*z\.ai.*'
                ],
                'type': 'web_chat',
                'priority': 100,  # Highest priority as requested
                'templates': ['zai_web']
            },
            
            # Google AI Studio / Gemini
            'google_ai': {
                'patterns': [
                    r'.*aistudio\.google\.com.*',
                    r'.*gemini\.google\.com.*',
                    r'.*generativelanguage\.googleapis\.com.*'
                ],
                'type': 'web_chat',
                'priority': 75,
                'templates': ['google_ai_studio', 'gemini_web']
            },
            
            # Mistral
            'mistral': {
                'patterns': [
                    r'.*chat\.mistral\.ai.*',
                    r'.*api\.mistral\.ai.*'
                ],
                'type': 'web_chat',
                'priority': 70,
                'templates': ['mistral_web', 'mistral_api']
            },
            
            # Bolt.new
            'bolt': {
                'patterns': [
                    r'.*bolt\.new.*',
                    r'.*www\.bolt\.new.*'
                ],
                'type': 'web_chat',
                'priority': 65,
                'templates': ['bolt_web']
            },
            
            # Claude/Anthropic
            'claude': {
                'patterns': [
                    r'.*claude\.ai.*',
                    r'.*api\.anthropic\.com.*'
                ],
                'type': 'web_chat',
                'priority': 85,
                'templates': ['claude_web', 'anthropic_api']
            },
            
            # Codegen
            'codegen': {
                'patterns': [
                    r'.*codegen.*\.modal\.run.*',
                    r'.*api\.codegen\.com.*'
                ],
                'type': 'rest_api',
                'priority': 90,  # High priority as requested
                'templates': ['codegen_api']
            }
        }
        
        # Compile regex patterns for performance
        self.compiled_patterns = {}
        for service, config in self.service_patterns.items():
            self.compiled_patterns[service] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in config['patterns']
            ]
    
    def matches_known_service(self, url: str) -> bool:
        """
        Check if URL matches any known AI service
        """
        service_info = self.identify_service(url)
        return service_info is not None
    
    def identify_service(self, url: str) -> Optional[Dict[str, any]]:
        """
        Identify which AI service a URL belongs to
        """
        try:
            for service_name, patterns in self.compiled_patterns.items():
                for pattern in patterns:
                    if pattern.match(url):
                        service_config = self.service_patterns[service_name].copy()
                        service_config['service_name'] = service_name
                        service_config['matched_url'] = url
                        return service_config
            
            return None
            
        except Exception as e:
            logger.error(f"Error identifying service for URL {url}: {e}")
            return None
    
    def get_service_type(self, url: str) -> Optional[str]:
        """
        Get the service type (web_chat, rest_api) for a URL
        """
        service_info = self.identify_service(url)
        if service_info:
            # Determine type based on URL patterns
            if 'api.' in url or '/api/' in url:
                return 'rest_api'
            elif 'chat.' in url or '/chat' in url:
                return 'web_chat'
            else:
                return service_info.get('type', 'web_chat')
        return None
    
    def get_suggested_priority(self, url: str) -> int:
        """
        Get suggested priority for a service based on URL
        """
        service_info = self.identify_service(url)
        return service_info.get('priority', 50) if service_info else 50
    
    def get_service_templates(self, url: str) -> List[str]:
        """
        Get available templates for a service
        """
        service_info = self.identify_service(url)
        return service_info.get('templates', []) if service_info else []
    
    def extract_domain_info(self, url: str) -> Dict[str, str]:
        """
        Extract domain information from URL
        """
        try:
            parsed = urlparse(url)
            return {
                'scheme': parsed.scheme,
                'domain': parsed.netloc,
                'path': parsed.path,
                'full_url': url
            }
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
            return {}
    
    def suggest_endpoint_name(self, url: str) -> str:
        """
        Suggest a name for an endpoint based on URL
        """
        service_info = self.identify_service(url)
        if service_info:
            service_name = service_info['service_name']
            service_type = service_info['type']
            
            # Create name like "zai-web" or "deepseek-api"
            type_suffix = 'web' if service_type == 'web_chat' else 'api'
            return f"{service_name}-{type_suffix}"
        
        # Fallback to domain-based naming
        try:
            domain = urlparse(url).netloc
            # Remove common prefixes and suffixes
            domain = domain.replace('www.', '').replace('api.', '').replace('chat.', '')
            domain = domain.split('.')[0]  # Get main domain part
            return f"{domain}-endpoint"
        except:
            return "custom-endpoint"
    
    def is_api_endpoint(self, url: str) -> bool:
        """
        Determine if URL is likely an API endpoint
        """
        api_indicators = [
            '/api/',
            '/v1/',
            '/v2/',
            'api.',
            '.json',
            '/completions',
            '/chat/completions'
        ]
        
        return any(indicator in url.lower() for indicator in api_indicators)
    
    def is_web_chat(self, url: str) -> bool:
        """
        Determine if URL is likely a web chat interface
        """
        chat_indicators = [
            'chat.',
            '/chat',
            '/conversation',
            '/c/',
            'claude.ai',
            'chat.openai.com',
            'chat.deepseek.com'
        ]
        
        return any(indicator in url.lower() for indicator in chat_indicators)
    
    def get_all_known_services(self) -> Dict[str, Dict]:
        """
        Get all known service configurations
        """
        return self.service_patterns.copy()
    
    def add_custom_pattern(
        self, 
        service_name: str, 
        patterns: List[str], 
        service_type: str = 'web_chat',
        priority: int = 50
    ):
        """
        Add custom service pattern
        """
        self.service_patterns[service_name] = {
            'patterns': patterns,
            'type': service_type,
            'priority': priority,
            'templates': [f"{service_name}_custom"]
        }
        
        # Compile new patterns
        self.compiled_patterns[service_name] = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in patterns
        ]
        
        logger.info(f"Added custom service pattern: {service_name}")
