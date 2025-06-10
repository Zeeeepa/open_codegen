#!/usr/bin/env python3
"""
Code Validation Test Suite
Validates the implementation without requiring a running server.
Tests code structure, imports, and model definitions.
"""

import sys
import importlib
import inspect
from typing import List, Dict, Any

class CodeValidator:
    def __init__(self):
        self.results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results."""
        result = {
            "test": test_name,
            "status": status,
            "details": details
        }
        self.results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name} - {status} {details}")
    
    def test_imports(self):
        """Test that all modules can be imported."""
        modules_to_test = [
            "openai_codegen_adapter.models",
            "openai_codegen_adapter.server",
            "openai_codegen_adapter.anthropic_transformer",
            "openai_codegen_adapter.gemini_transformer",
            "openai_codegen_adapter.codegen_client"
        ]
        
        failed_imports = []
        for module_name in modules_to_test:
            try:
                importlib.import_module(module_name)
            except Exception as e:
                failed_imports.append(f"{module_name}: {e}")
        
        if failed_imports:
            self.log_test("Module Imports", "FAIL", f"Failed: {', '.join(failed_imports)}")
            return False
        else:
            self.log_test("Module Imports", "PASS", f"All {len(modules_to_test)} modules imported successfully")
            return True
    
    def test_anthropic_models(self):
        """Test Anthropic model definitions."""
        try:
            from openai_codegen_adapter.models import (
                AnthropicRequest, AnthropicResponse, AnthropicMessage,
                AnthropicContentBlock, AnthropicResponseContent, AnthropicUsage
            )
            
            # Test AnthropicRequest has all required fields
            request_fields = AnthropicRequest.model_fields.keys()  # Updated for Pydantic v2
            required_fields = {
                'model', 'max_tokens', 'messages', 'temperature', 'top_p', 'top_k',
                'system', 'stop_sequences', 'stream', 'metadata'
            }
            
            missing_fields = required_fields - set(request_fields)
            if missing_fields:
                self.log_test("Anthropic Models", "FAIL", f"Missing fields: {missing_fields}")
                return False
            
            # Test content block support
            content_block_fields = AnthropicContentBlock.model_fields.keys()  # Updated for Pydantic v2
            if 'type' not in content_block_fields or 'text' not in content_block_fields:
                self.log_test("Anthropic Models", "FAIL", "Content block missing required fields")
                return False
            
            self.log_test("Anthropic Models", "PASS", "All required fields present")
            return True
            
        except Exception as e:
            self.log_test("Anthropic Models", "FAIL", str(e))
            return False
    
    def test_google_models(self):
        """Test Google Vertex AI model definitions."""
        try:
            from openai_codegen_adapter.models import (
                GeminiRequest, GeminiResponse, GeminiContent, GeminiPart,
                GeminiGenerationConfig, GeminiSafetySetting, GeminiTool
            )
            
            # Test GeminiRequest has all required fields
            request_fields = GeminiRequest.model_fields.keys()  # Updated for Pydantic v2
            required_fields = {
                'contents', 'systemInstruction', 'generationConfig', 'safetySettings',
                'tools', 'toolConfig', 'cachedContent', 'labels'
            }
            
            missing_fields = required_fields - set(request_fields)
            if missing_fields:
                self.log_test("Google Models", "FAIL", f"Missing fields: {missing_fields}")
                return False
            
            # Test multimodal part support
            part_fields = GeminiPart.model_fields.keys()  # Updated for Pydantic v2
            multimodal_fields = {'text', 'inlineData', 'fileData', 'functionCall', 'functionResponse'}
            if not multimodal_fields.intersection(set(part_fields)):
                self.log_test("Google Models", "FAIL", "Part missing multimodal support")
                return False
            
            self.log_test("Google Models", "PASS", "All required fields present")
            return True
            
        except Exception as e:
            self.log_test("Google Models", "FAIL", str(e))
            return False
    
    def test_openai_models(self):
        """Test OpenAI model definitions."""
        try:
            from openai_codegen_adapter.models import (
                ChatRequest, ChatResponse, EmbeddingRequest,
                AudioTranscriptionRequest, ImageGenerationRequest
            )
            
            # Test that all OpenAI models exist
            models = [
                ChatRequest, ChatResponse, EmbeddingRequest,
                AudioTranscriptionRequest, ImageGenerationRequest
            ]
            
            for model in models:
                if not hasattr(model, 'model_fields'):  # Updated for Pydantic v2
                    self.log_test("OpenAI Models", "FAIL", f"{model.__name__} not a valid Pydantic model")
                    return False
            
            self.log_test("OpenAI Models", "PASS", "All OpenAI models defined correctly")
            return True
            
        except Exception as e:
            self.log_test("OpenAI Models", "FAIL", str(e))
            return False
    
    def test_transformers(self):
        """Test transformer functions."""
        try:
            from openai_codegen_adapter.anthropic_transformer import (
                anthropic_request_to_prompt, create_anthropic_response,
                extract_anthropic_generation_params
            )
            from openai_codegen_adapter.gemini_transformer import (
                gemini_request_to_prompt, create_gemini_response,
                extract_gemini_generation_params
            )
            
            # Test that functions are callable
            functions = [
                anthropic_request_to_prompt, create_anthropic_response,
                extract_anthropic_generation_params, gemini_request_to_prompt,
                create_gemini_response, extract_gemini_generation_params
            ]
            
            for func in functions:
                if not callable(func):
                    self.log_test("Transformers", "FAIL", f"{func.__name__} not callable")
                    return False
            
            self.log_test("Transformers", "PASS", "All transformer functions available")
            return True
            
        except Exception as e:
            self.log_test("Transformers", "FAIL", str(e))
            return False
    
    def test_server_endpoints(self):
        """Test server endpoint definitions."""
        try:
            from openai_codegen_adapter.server import app
            
            # Get all routes
            routes = []
            for route in app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    for method in route.methods:
                        if method != 'HEAD':  # Skip HEAD methods
                            routes.append(f"{method} {route.path}")
            
            # Expected endpoints
            expected_endpoints = [
                "GET /health",
                "GET /v1/models",
                "POST /v1/chat/completions",
                "POST /v1/completions",
                "POST /v1/embeddings",
                "POST /v1/audio/transcriptions",
                "POST /v1/audio/translations",
                "POST /v1/images/generations",
                "POST /v1/messages",
                "POST /v1/models/{model}:generateContent",
                "POST /v1/models/{model}:streamGenerateContent"
            ]
            
            missing_endpoints = []
            for endpoint in expected_endpoints:
                # Check if endpoint exists (allowing for path parameters)
                found = False
                endpoint_method = endpoint.split()[0]
                endpoint_path = endpoint.split()[1]
                
                for route in routes:
                    route_method = route.split()[0]
                    route_path = route.split()[1]
                    
                    # Handle path parameters like {model}
                    if endpoint_method == route_method:
                        if endpoint_path == route_path or \
                           ('{model}' in endpoint_path and endpoint_path.replace('{model}', '') in route_path):
                            found = True
                            break
                
                if not found:
                    missing_endpoints.append(endpoint)
            
            if missing_endpoints:
                self.log_test("Server Endpoints", "FAIL", f"Missing: {missing_endpoints}")
                return False
            
            self.log_test("Server Endpoints", "PASS", f"All {len(expected_endpoints)} endpoints defined")
            return True
            
        except Exception as e:
            self.log_test("Server Endpoints", "FAIL", str(e))
            return False
    
    def test_compatibility_tests_exist(self):
        """Test that compatibility test files exist."""
        import os
        
        test_files = [
            "test_anthropic_sdk_compatibility.py",
            "test_google_sdk_compatibility.py",
            "test_comprehensive_api.py"
        ]
        
        missing_files = []
        for test_file in test_files:
            if not os.path.exists(test_file):
                missing_files.append(test_file)
        
        if missing_files:
            self.log_test("Compatibility Tests", "FAIL", f"Missing: {missing_files}")
            return False
        
        self.log_test("Compatibility Tests", "PASS", f"All {len(test_files)} test files exist")
        return True
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("🔍 Code Validation Test Suite")
        print("Validating implementation structure and compatibility")
        print("=" * 60)
        
        tests = [
            self.test_imports,
            self.test_anthropic_models,
            self.test_google_models,
            self.test_openai_models,
            self.test_transformers,
            self.test_server_endpoints,
            self.test_compatibility_tests_exist
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                failed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Code Validation Summary")
        print("=" * 60)
        
        total_tests = passed + failed
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed, failed, total_tests

def main():
    """Main validation runner."""
    print("🧪 OpenAI Codegen Adapter - Code Validation")
    print("Validating full Anthropic and Google API compatibility implementation")
    print()
    
    validator = CodeValidator()
    
    try:
        passed, failed, total = validator.run_all_tests()
        
        if failed == 0:
            print("\n🎉 All validation tests passed! Implementation is structurally sound.")
            print("\n📋 Next Steps:")
            print("1. Set CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables")
            print("2. Start the server: python -m openai_codegen_adapter.main")
            print("3. Run compatibility tests:")
            print("   - python test_anthropic_sdk_compatibility.py")
            print("   - python test_google_sdk_compatibility.py")
            print("   - python test_comprehensive_api.py")
            sys.exit(0)
        else:
            print(f"\n⚠️  {failed} validation tests failed. Fix issues before proceeding.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Validation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Validation failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
