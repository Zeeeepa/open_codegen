"""
Enhanced request transformation utilities for Codegen integration.
Adds support for model mapping and prompt templates.
"""

import logging
from typing import Tuple

from backend.adapter.models import (
    ChatRequest, TextRequest, AnthropicRequest, GeminiRequest
)
from backend.adapter.request_transformer import (
    chat_request_to_prompt, text_request_to_prompt
)
from backend.adapter.anthropic_transformer import (
    anthropic_request_to_prompt
)
from backend.adapter.gemini_transformer import (
    gemini_request_to_prompt
)
from backend.adapter.model_mapper import ModelMapper
from backend.adapter.config import EnhancedCodegenConfig

logger = logging.getLogger(__name__)

class PromptTemplate:
    """Handles prompt template application."""
    
    def __init__(self, config: EnhancedCodegenConfig):
        self.enabled = config.prompt_template_enabled
        self.prefix = config.prompt_template_prefix
        self.suffix = config.prompt_template_suffix
        
        if self.enabled:
            logger.info("Prompt template enabled")
            if self.prefix:
                logger.info(f"Prompt prefix: {self.prefix[:50]}...")
            if self.suffix:
                logger.info(f"Prompt suffix: {self.suffix[:50]}...")
    
    def apply(self, prompt: str) -> str:
        """Apply template to prompt."""
        if not self.enabled:
            return prompt
        
        result = prompt
        
        if self.prefix:
            result = f"{self.prefix}\n\n{result}"
        
        if self.suffix:
            result = f"{result}\n\n{self.suffix}"
        
        logger.info(f"Applied prompt template, new length: {len(result)}")
        return result


def enhanced_chat_request_to_prompt(
    request: ChatRequest,
    model_mapper: ModelMapper,
    prompt_template: PromptTemplate
) -> Tuple[str, str]:
    """
    Convert OpenAI chat request to a prompt string for Codegen SDK.
    Returns both the prompt and the selected Codegen model.
    """
    # Convert request to prompt (using existing logic)
    prompt = chat_request_to_prompt(request)
    
    # Get the Codegen model for the requested model
    codegen_model = model_mapper.get_codegen_model(request.model)
    
    # Apply prompt template
    prompt = prompt_template.apply(prompt)
    
    return prompt, codegen_model


def enhanced_text_request_to_prompt(
    request: TextRequest,
    model_mapper: ModelMapper,
    prompt_template: PromptTemplate
) -> Tuple[str, str]:
    """
    Convert OpenAI text request to a prompt string for Codegen SDK.
    Returns both the prompt and the selected Codegen model.
    """
    # Convert request to prompt (using existing logic)
    prompt = text_request_to_prompt(request)
    
    # Get the Codegen model for the requested model
    codegen_model = model_mapper.get_codegen_model(request.model)
    
    # Apply prompt template
    prompt = prompt_template.apply(prompt)
    
    return prompt, codegen_model


def enhanced_anthropic_request_to_prompt(
    request: AnthropicRequest,
    model_mapper: ModelMapper,
    prompt_template: PromptTemplate
) -> Tuple[str, str]:
    """
    Convert Anthropic request to a prompt string for Codegen SDK.
    Returns both the prompt and the selected Codegen model.
    """
    # Convert request to prompt (using existing logic)
    prompt = anthropic_request_to_prompt(request)
    
    # Get the Codegen model for the requested model
    original_model = request.original_model or request.model
    codegen_model = model_mapper.get_codegen_model(original_model)
    
    # Apply prompt template
    prompt = prompt_template.apply(prompt)
    
    return prompt, codegen_model


def enhanced_gemini_request_to_prompt(
    request: GeminiRequest,
    model_mapper: ModelMapper,
    prompt_template: PromptTemplate
) -> Tuple[str, str]:
    """
    Convert Gemini request to a prompt string for Codegen SDK.
    Returns both the prompt and the selected Codegen model.
    """
    # Convert request to prompt (using existing logic)
    prompt = gemini_request_to_prompt(request)
    
    # Determine the model - Gemini doesn't have a model field in the request
    # so we use a default Gemini model
    codegen_model = model_mapper.get_codegen_model("gemini-pro")
    
    # Apply prompt template
    prompt = prompt_template.apply(prompt)
    
    return prompt, codegen_model


def create_prompt_template(config: EnhancedCodegenConfig) -> PromptTemplate:
    """Create a prompt template from configuration."""
    return PromptTemplate(config)

