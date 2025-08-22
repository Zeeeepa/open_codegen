"""
Model mapping system for translating between provider models and Codegen models.
"""

import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ModelMapper:
    """Maps provider models to Codegen models."""
    
    DEFAULT_MAPPINGS = {
        # OpenAI models
        "gpt-5": "codegen-premium",
        "gpt-4.1": "codegen-advanced",
        "o3": "codegen-standard",
        "o4-mini": "codegen-standard",
        
        # Anthropic models
        "claude-sonnet-4": "codegen-premium",
        "claude-sonnet-3.7": "codegen-advanced",
        "claude-sonnet-3.5": "codegen-standard",
        
        # Gemini models
        "gemini-2.5": "codegen-advanced",
        
        # Legacy models (for backward compatibility)
        "gpt-4": "codegen-advanced",
        "gpt-3.5-turbo": "codegen-standard",
        "claude-3-opus-20240229": "codegen-premium",
        "claude-3-sonnet-20240229": "codegen-advanced",
        "claude-3-haiku-20240307": "codegen-standard",
        "gemini-1.5-pro": "codegen-advanced",
        "gemini-pro": "codegen-standard"
    }
    
    def __init__(self, custom_mappings: Optional[Dict[str, str]] = None):
        self.custom_mappings = custom_mappings or {}
        logger.info(f"Initialized ModelMapper with {len(self.custom_mappings)} custom mappings")
    
    def get_codegen_model(self, provider_model: str) -> str:
        """Get the Codegen model for a provider model."""
        # Check custom mappings first
        if provider_model in self.custom_mappings:
            model = self.custom_mappings[provider_model]
            logger.info(f"Using custom mapping for {provider_model} -> {model}")
            return model
        
        # Then check default mappings
        if provider_model in self.DEFAULT_MAPPINGS:
            model = self.DEFAULT_MAPPINGS[provider_model]
            logger.info(f"Using default mapping for {provider_model} -> {model}")
            return model
        
        # Default fallback
        logger.warning(f"No mapping found for {provider_model}, using default model")
        return "codegen-standard"
    
    @classmethod
    def from_environment(cls) -> "ModelMapper":
        """Create a ModelMapper from environment variables."""
        custom_mappings = {}
        mapping_str = os.environ.get("CODEGEN_MODEL_MAPPING", "")
        
        if mapping_str:
            try:
                # Format: "gpt-4:codegen-advanced,gpt-3.5-turbo:codegen-standard"
                pairs = mapping_str.split(",")
                for pair in pairs:
                    provider_model, codegen_model = pair.split(":")
                    custom_mappings[provider_model.strip()] = codegen_model.strip()
                logger.info(f"Loaded {len(custom_mappings)} model mappings from environment")
            except Exception as e:
                logger.warning(f"Failed to parse CODEGEN_MODEL_MAPPING: {e}")
        
        return cls(custom_mappings)


def get_model_mapper() -> ModelMapper:
    """Get model mapper instance from environment."""
    return ModelMapper.from_environment()

