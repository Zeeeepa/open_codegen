# ... existing imports ...

# Add new import for context retrieval
try:
    from codegen_integration import CodegenClient, get_agent_response_for_context
    CONTEXT_RETRIEVAL_AVAILABLE = True
except ImportError:
    CONTEXT_RETRIEVAL_AVAILABLE = False
    print("⚠️ Context retrieval not available. Install codegen_integration module.")

# ... existing code ...
