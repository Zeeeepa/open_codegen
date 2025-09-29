"""TalkAI Provider - Stub implementation"""
import asyncio
import logging
from typing import Dict, Any
from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)

class TalkAIProvider(BaseProvider):
    async def initialize(self):
        self.initialized = True
        self.stats["initialized_at"] = asyncio.get_event_loop().time()
        logger.info("✅ TalkAI provider initialized (stub)")
    
    async def process_request(self, webchat_request: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            return self._create_error_response("Provider not initialized")
        start_time = self._record_request_start()
        try:
            message = webchat_request.get("message", "")
            response_content = f"[TALKAI STUB] Response to: {message}"
            self._record_request_success(start_time)
            return self._create_success_response(response_content, {"model": "talkai", "provider": "talkai"})
        except Exception as e:
            error_msg = f"TalkAI request failed: {str(e)}"
            self._record_request_failure(error_msg)
            return self._create_error_response(error_msg)
    
    async def health_check(self) -> bool:
        return self.initialized
