"""
AI Assistant for endpoint configuration and management.
Provides natural language interface for setting up AI endpoints.
"""
import logging
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class AIEndpointAssistant:
    """
    AI assistant for helping users configure and manage AI endpoints.
    
    Provides natural language interface for endpoint setup, troubleshooting,
    and configuration recommendations based on user requirements.
    """
    
    def __init__(self):
        self.provider_templates = self._load_provider_templates()
        self.common_patterns = self._load_common_patterns()
    
    async def process_message(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process user message and provide AI assistance.
        
        Args:
            message: User's natural language message
            context: Context including user_id, existing endpoints, etc.
            
        Returns:
            Dictionary with response, suggested config, and actions
        """
        try:
            # Analyze the user's intent
            intent = self._analyze_intent(message)
            
            # Generate response based on intent
            if intent == "create_endpoint":
                return await self._handle_create_endpoint(message, context)
            elif intent == "troubleshoot":
                return await self._handle_troubleshooting(message, context)
            elif intent == "list_providers":
                return await self._handle_list_providers(message, context)
            elif intent == "help":
                return await self._handle_help_request(message, context)
            else:
                return await self._handle_general_query(message, context)
        
        except Exception as e:
            logger.error(f"Error processing AI assistant message: {e}")
            return {
                "response": "I encountered an error processing your request. Please try again or contact support.",
                "suggested_config": None,
                "actions": ["retry"]
            }
    
    def _analyze_intent(self, message: str) -> str:
        """Analyze user message to determine intent."""
        message_lower = message.lower()
        
        # Keywords for different intents
        create_keywords = ["create", "add", "setup", "configure", "new endpoint"]
        troubleshoot_keywords = ["error", "not working", "failed", "problem", "issue"]
        list_keywords = ["list", "show", "what providers", "available"]
        help_keywords = ["help", "how to", "guide", "tutorial"]
        
        if any(keyword in message_lower for keyword in create_keywords):
            return "create_endpoint"
        elif any(keyword in message_lower for keyword in troubleshoot_keywords):
            return "troubleshoot"
        elif any(keyword in message_lower for keyword in list_keywords):
            return "list_providers"
        elif any(keyword in message_lower for keyword in help_keywords):
            return "help"
        else:
            return "general"
    
    async def _handle_create_endpoint(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle endpoint creation requests."""
        # Extract provider information from message
        provider_info = self._extract_provider_info(message)
        
        if not provider_info:
            return {
                "response": """I can help you create a new AI endpoint! I support these provider types:

**REST API** - Standard API endpoints (OpenAI, Anthropic, etc.)
**Web Chat** - Browser-based interfaces (ChatGPT web, Claude web)
**API Token** - Custom token-based authentication

Which type would you like to set up? You can say something like:
- "Create an OpenAI REST API endpoint"
- "Set up ChatGPT web chat"
- "Add a custom API token endpoint"
""",
                "suggested_config": None,
                "actions": ["specify_provider_type"]
            }
        
        # Generate configuration based on detected provider
        suggested_config = self._generate_config_suggestion(provider_info)
        
        return {
            "response": f"""Great! I can help you set up a {provider_info['name']} endpoint.

Here's what I've prepared for you:

**Provider Type**: {provider_info['type']}
**Configuration**: {json.dumps(suggested_config, indent=2)}

Would you like me to create this endpoint, or would you like to modify any settings first?
""",
            "suggested_config": suggested_config,
            "actions": ["create_endpoint", "modify_config"]
        }
    
    async def _handle_troubleshooting(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle troubleshooting requests."""
        existing_endpoints = context.get("existing_endpoints", [])
        
        if not existing_endpoints:
            return {
                "response": """I'd be happy to help troubleshoot! However, I don't see any existing endpoints in your account.

If you're having trouble creating an endpoint, please let me know:
1. What type of provider are you trying to set up?
2. What error message are you seeing?
3. What steps have you already tried?
""",
                "suggested_config": None,
                "actions": ["provide_more_details"]
            }
        
        # Analyze common issues
        troubleshooting_tips = self._generate_troubleshooting_tips(message, existing_endpoints)
        
        return {
            "response": f"""I can help troubleshoot your endpoint issues! Here are some common solutions:

{troubleshooting_tips}

If none of these help, please share:
- The specific error message you're seeing
- Which endpoint is having issues
- When the problem started occurring
""",
            "suggested_config": None,
            "actions": ["test_endpoint", "check_logs", "provide_more_details"]
        }
    
    async def _handle_list_providers(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle requests to list available providers."""
        provider_list = """Here are the AI providers I can help you set up:

**REST API Providers:**
• OpenAI (GPT-3.5, GPT-4)
• Anthropic (Claude)
• Google (Gemini)
• Custom REST APIs

**Web Chat Providers:**
• ChatGPT Web Interface
• Claude Web Interface
• Custom web chat interfaces

**API Token Providers:**
• Custom authentication systems
• OAuth-based APIs
• Token refresh mechanisms

Which provider would you like to configure? Just let me know and I'll guide you through the setup!
"""
        
        return {
            "response": provider_list,
            "suggested_config": None,
            "actions": ["select_provider"]
        }
    
    async def _handle_help_request(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle general help requests."""
        help_text = """I'm your AI endpoint management assistant! Here's what I can help you with:

**🚀 Creating Endpoints**
- Set up REST API endpoints (OpenAI, Anthropic, etc.)
- Configure web chat interfaces
- Set up custom authentication

**🔧 Managing Endpoints**
- Start and stop endpoints
- Test endpoint connectivity
- Monitor performance

**🛠️ Troubleshooting**
- Diagnose connection issues
- Fix authentication problems
- Optimize performance

**💬 Just ask me naturally!**
- "Create an OpenAI endpoint"
- "My Claude endpoint isn't working"
- "Show me all available providers"
- "How do I set up ChatGPT web?"

What would you like to do?
"""
        
        return {
            "response": help_text,
            "suggested_config": None,
            "actions": ["ask_question"]
        }
    
    async def _handle_general_query(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle general queries that don't fit specific intents."""
        return {
            "response": """I'm here to help you manage AI endpoints! I can assist with:

• Creating new endpoints for various AI providers
• Troubleshooting connection issues
• Configuring authentication
• Testing endpoint performance

Could you be more specific about what you'd like to do? For example:
- "Create a new OpenAI endpoint"
- "Help me fix my Claude connection"
- "Show me available providers"
""",
            "suggested_config": None,
            "actions": ["be_more_specific"]
        }
    
    def _extract_provider_info(self, message: str) -> Optional[Dict[str, str]]:
        """Extract provider information from user message."""
        message_lower = message.lower()
        
        # Provider detection patterns
        providers = {
            "openai": {"name": "OpenAI", "type": "REST_API"},
            "gpt": {"name": "OpenAI", "type": "REST_API"},
            "anthropic": {"name": "Anthropic", "type": "REST_API"},
            "claude": {"name": "Anthropic", "type": "REST_API"},
            "google": {"name": "Google", "type": "REST_API"},
            "gemini": {"name": "Google", "type": "REST_API"},
            "chatgpt web": {"name": "ChatGPT Web", "type": "WEB_CHAT"},
            "claude web": {"name": "Claude Web", "type": "WEB_CHAT"},
            "web chat": {"name": "Web Chat", "type": "WEB_CHAT"},
            "custom api": {"name": "Custom API", "type": "API_TOKEN"},
            "token": {"name": "Token-based API", "type": "API_TOKEN"}
        }
        
        for keyword, info in providers.items():
            if keyword in message_lower:
                return info
        
        return None
    
    def _generate_config_suggestion(self, provider_info: Dict[str, str]) -> Dict[str, Any]:
        """Generate configuration suggestion based on provider."""
        provider_type = provider_info["type"]
        provider_name = provider_info["name"]
        
        if provider_type == "REST_API":
            if "openai" in provider_name.lower():
                return {
                    "api_base_url": "https://api.openai.com",
                    "auth_type": "api_key",
                    "api_key": "[YOUR_OPENAI_API_KEY]",
                    "timeout": 30,
                    "max_retries": 3
                }
            elif "anthropic" in provider_name.lower():
                return {
                    "api_base_url": "https://api.anthropic.com",
                    "auth_type": "api_key",
                    "api_key": "[YOUR_ANTHROPIC_API_KEY]",
                    "timeout": 30,
                    "max_retries": 3
                }
            elif "google" in provider_name.lower():
                return {
                    "api_base_url": "https://generativelanguage.googleapis.com",
                    "auth_type": "api_key",
                    "api_key": "[YOUR_GOOGLE_API_KEY]",
                    "timeout": 30,
                    "max_retries": 3
                }
        
        elif provider_type == "WEB_CHAT":
            return {
                "url": "https://chat.openai.com" if "chatgpt" in provider_name.lower() else "https://claude.ai",
                "username": "[YOUR_USERNAME]",
                "password": "[YOUR_PASSWORD]",
                "input_selector": "#message-input",
                "send_button_selector": "[data-testid='send-button']",
                "response_selector": ".message-content",
                "wait_for_response": 10,
                "use_stealth": True
            }
        
        elif provider_type == "API_TOKEN":
            return {
                "api_base_url": "[API_BASE_URL]",
                "auth_type": "bearer_token",
                "bearer_token": "[YOUR_TOKEN]",
                "timeout": 30,
                "custom_headers": {}
            }
        
        return {}
    
    def _generate_troubleshooting_tips(
        self, 
        message: str, 
        existing_endpoints: List[Dict[str, Any]]
    ) -> str:
        """Generate troubleshooting tips based on message and endpoints."""
        tips = []
        
        # Common troubleshooting tips
        if "authentication" in message.lower() or "auth" in message.lower():
            tips.append("🔑 **Authentication Issues:**\n   - Verify your API key is correct and active\n   - Check if the key has the required permissions")
        
        if "connection" in message.lower() or "timeout" in message.lower():
            tips.append("🌐 **Connection Issues:**\n   - Check your internet connection\n   - Verify the API endpoint URL is correct\n   - Try increasing the timeout value")
        
        if "rate limit" in message.lower() or "429" in message.lower():
            tips.append("⏱️ **Rate Limiting:**\n   - Reduce request frequency\n   - Check your API plan limits\n   - Implement exponential backoff")
        
        if not tips:
            tips.append("🔍 **General Troubleshooting:**\n   - Test the endpoint with a simple message\n   - Check the endpoint status in the dashboard\n   - Review the error logs for specific details")
        
        return "\n\n".join(tips)
    
    def _load_provider_templates(self) -> Dict[str, Any]:
        """Load provider configuration templates."""
        # This would typically load from a configuration file
        return {
            "openai": {
                "type": "REST_API",
                "config": {
                    "api_base_url": "https://api.openai.com",
                    "auth_type": "api_key"
                }
            },
            "anthropic": {
                "type": "REST_API", 
                "config": {
                    "api_base_url": "https://api.anthropic.com",
                    "auth_type": "api_key"
                }
            }
        }
    
    def _load_common_patterns(self) -> Dict[str, Any]:
        """Load common configuration patterns."""
        return {
            "rest_api_defaults": {
                "timeout": 30,
                "max_retries": 3,
                "headers": {"Content-Type": "application/json"}
            },
            "web_chat_defaults": {
                "wait_for_response": 10,
                "use_stealth": True
            }
        }
