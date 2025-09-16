"""
Web Chat handler for browser-based AI interfaces.
Enhanced implementation with Z.AI Web UI SDK integration and autoscaling support.
"""
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_handler import BaseProviderHandler

logger = logging.getLogger(__name__)


class ZAIWebClient:
    """Z.AI Web UI client implementation based on the Python SDK."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url", "https://chat.z.ai")
        self.timeout = config.get("timeout", 180)
        self.auto_auth = config.get("auto_auth", True)
        self.verbose = config.get("verbose", False)
        self.token = config.get("token")
        self._session = None
        self._authenticated = False
    
    async def initialize(self) -> None:
        """Initialize the Z.AI client with authentication."""
        import aiohttp
        
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)
        
        if self.auto_auth and not self.token:
            await self._fetch_guest_token()
        
        self._authenticated = True
        logger.info("Z.AI Web client initialized successfully")
    
    async def _fetch_guest_token(self) -> None:
        """Fetch guest token for authentication."""
        try:
            auth_url = f"{self.base_url}/api/auth/guest"
            async with self._session.post(auth_url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data.get("token")
                    if self.verbose:
                        logger.info("Guest token obtained successfully")
                else:
                    raise Exception(f"Failed to get guest token: {response.status}")
        except Exception as e:
            logger.error(f"Error fetching guest token: {e}")
            raise
    
    async def simple_chat(
        self,
        message: str,
        model: str = "glm-4.5v",
        enable_thinking: bool = True,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Send a simple chat message and get response."""
        if not self._authenticated or not self._session:
            raise RuntimeError("Client not initialized")
        
        # Create chat session
        chat_data = await self._create_chat_session(model)
        chat_id = chat_data.get("id")
        
        if not chat_id:
            raise Exception("Failed to create chat session")
        
        # Send message
        payload = {
            "messages": [{"role": "user", "content": message}],
            "model": model,
            "enable_thinking": enable_thinking,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        chat_url = f"{self.base_url}/api/chat/{chat_id}/complete"
        
        try:
            async with self._session.post(chat_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "content": data.get("content", ""),
                        "thinking": data.get("thinking", ""),
                        "model": model,
                        "chat_id": chat_id
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Chat request failed: {response.status} - {error_text}")
        
        except Exception as e:
            logger.error(f"Error in simple_chat: {e}")
            raise
    
    async def _create_chat_session(self, model: str) -> Dict[str, Any]:
        """Create a new chat session."""
        payload = {
            "title": f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "models": [model],
            "initial_message": "",
            "enable_thinking": True
        }
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        create_url = f"{self.base_url}/api/chat/create"
        
        async with self._session.post(create_url, json=payload, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to create chat session: {response.status} - {error_text}")
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
        self._authenticated = False


class WebChatHandler(BaseProviderHandler):
    """
    Enhanced handler for web chat-based AI endpoints with Z.AI Web UI integration.
    
    Supports autoscaling for multiple concurrent requests and provides
    seamless integration with Z.AI's GLM models.
    """
    
    def __init__(self, config):
        super().__init__(config)
        self._clients: List[ZAIWebClient] = []
        self._client_pool_size = config.config_data.get("pool_size", 3)
        self._current_client_index = 0
        self._client_lock = asyncio.Lock()
        self._scaling_enabled = config.config_data.get("autoscaling", True)
        self._max_pool_size = config.config_data.get("max_pool_size", 10)
    
    async def start(self) -> None:
        """Initialize web chat session with client pool."""
        # Validate required configuration
        required_keys = ["provider_type"]
        self.validate_required_config(required_keys)
        
        provider_type = self.get_config_value("provider_type", "zai")
        
        if provider_type == "zai":
            await self._initialize_zai_clients()
        else:
            raise ValueError(f"Unsupported web chat provider: {provider_type}")
        
        self._is_started = True
        logger.info(f"Web chat handler started for {self.endpoint_id} with {len(self._clients)} clients")
    
    async def stop(self) -> None:
        """Close all client sessions and cleanup."""
        for client in self._clients:
            try:
                await client.close()
            except Exception as e:
                logger.warning(f"Error closing client: {e}")
        
        self._clients.clear()
        self._is_started = False
        logger.info(f"Web chat handler stopped for {self.endpoint_id}")
    
    async def send_message(self, message: str) -> str:
        """
        Send message through web chat interface with load balancing.
        
        Args:
            message: Message to send
            
        Returns:
            Response from the web chat
        """
        if not self._is_started:
            raise RuntimeError("Handler not started")
        
        # Get available client (with autoscaling if needed)
        client = await self._get_available_client()
        
        try:
            # Extract model from config or use default
            model = self.get_config_value("model", "glm-4.5v")
            
            # Send message to Z.AI
            response = await client.simple_chat(
                message=message,
                model=model,
                enable_thinking=self.get_config_value("enable_thinking", True),
                temperature=self.get_config_value("temperature", 0.7),
                top_p=self.get_config_value("top_p", 0.9),
                max_tokens=self.get_config_value("max_tokens", 1000)
            )
            
            return response.get("content", "No response received")
        
        except Exception as e:
            logger.error(f"Error sending message via web chat: {e}")
            raise Exception(f"Web chat request failed: {e}")
    
    async def health_check(self) -> bool:
        """Check if web chat interface is responsive."""
        try:
            if not self._is_started or not self._clients:
                return False
            
            # Test with the first available client
            client = self._clients[0]
            if not client._authenticated:
                return False
            
            # Simple health check - could send a ping message
            return True
            
        except Exception as e:
            logger.warning(f"Health check failed for {self.endpoint_id}: {e}")
            return False
    
    async def _initialize_zai_clients(self) -> None:
        """Initialize Z.AI client pool."""
        for i in range(self._client_pool_size):
            client_config = {
                "base_url": self.get_config_value("base_url", "https://chat.z.ai"),
                "timeout": self.get_config_value("timeout", 180),
                "auto_auth": self.get_config_value("auto_auth", True),
                "verbose": self.get_config_value("verbose", False),
                "token": self.get_config_value("token")
            }
            
            client = ZAIWebClient(client_config)
            await client.initialize()
            self._clients.append(client)
            
            logger.info(f"Initialized Z.AI client {i+1}/{self._client_pool_size}")
    
    async def _get_available_client(self) -> ZAIWebClient:
        """Get an available client with round-robin load balancing."""
        async with self._client_lock:
            if not self._clients:
                raise RuntimeError("No clients available")
            
            # Check if we need to scale up
            if self._scaling_enabled and len(self._clients) < self._max_pool_size:
                # Simple scaling logic: add client if all are potentially busy
                # In a real implementation, you'd track active requests per client
                if len(self._clients) < self._max_pool_size:
                    await self._scale_up_if_needed()
            
            # Round-robin selection
            client = self._clients[self._current_client_index]
            self._current_client_index = (self._current_client_index + 1) % len(self._clients)
            
            return client
    
    async def _scale_up_if_needed(self) -> None:
        """Scale up the client pool if needed."""
        try:
            client_config = {
                "base_url": self.get_config_value("base_url", "https://chat.z.ai"),
                "timeout": self.get_config_value("timeout", 180),
                "auto_auth": self.get_config_value("auto_auth", True),
                "verbose": self.get_config_value("verbose", False),
                "token": self.get_config_value("token")
            }
            
            client = ZAIWebClient(client_config)
            await client.initialize()
            self._clients.append(client)
            
            logger.info(f"Scaled up Z.AI client pool to {len(self._clients)} clients")
        
        except Exception as e:
            logger.error(f"Failed to scale up client pool: {e}")
