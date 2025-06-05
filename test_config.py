#!/usr/bin/env python3
"""
Test script to validate configuration loading from .env file
"""

import os
import sys
from openai_codegen_adapter.config import get_codegen_config, get_server_config, validate_config

def test_config_loading():
    """Test that configuration loads correctly from .env file"""
    print("🔧 Testing Configuration Loading")
    print("=" * 50)
    
    # Test Codegen config
    codegen_config = get_codegen_config()
    print(f"✅ Codegen Config Loaded:")
    print(f"   Org ID: {codegen_config.org_id}")
    print(f"   API Token: {'***' + codegen_config.api_token[-4:] if codegen_config.api_token else 'Not set'}")
    print(f"   Base URL: {codegen_config.base_url}")
    print(f"   Timeout: {codegen_config.default_timeout}s")
    
    # Test Server config
    server_config = get_server_config()
    print(f"\n✅ Server Config Loaded:")
    print(f"   Host: {server_config.host}")
    print(f"   Port: {server_config.port}")
    print(f"   Log Level: {server_config.log_level}")
    print(f"   CORS Origins: {server_config.cors_origins}")
    
    # Validate config
    print(f"\n🔍 Configuration Validation:")
    is_valid = validate_config()
    if is_valid:
        print("✅ Configuration is valid and complete!")
        return True
    else:
        print("❌ Configuration is incomplete!")
        return False

def test_environment_variables():
    """Test that environment variables are properly set"""
    print("\n🌍 Testing Environment Variables")
    print("=" * 50)
    
    # Check if .env file exists
    if os.path.exists(".env"):
        print("✅ .env file found")
        with open(".env", "r") as f:
            env_content = f.read()
            if "CODEGEN_ORG_ID" in env_content:
                print("✅ CODEGEN_ORG_ID found in .env")
            if "CODEGEN_API_TOKEN" in env_content:
                print("✅ CODEGEN_API_TOKEN found in .env")
    else:
        print("❌ .env file not found")
        return False
    
    # Test that config can load the values
    try:
        codegen_config = get_codegen_config()
        if codegen_config.org_id:
            print(f"✅ CODEGEN_ORG_ID loaded: {codegen_config.org_id}")
        if codegen_config.api_token:
            print(f"✅ CODEGEN_API_TOKEN loaded: ***{codegen_config.api_token[-4:]}")
        return bool(codegen_config.org_id and codegen_config.api_token)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False

def main():
    """Run all configuration tests"""
    print("🧪 OpenAI Codegen Adapter - Configuration Testing")
    print("=" * 60)
    
    # Test environment variables
    env_test = test_environment_variables()
    
    # Test config loading
    config_test = test_config_loading()
    
    print("\n📊 Test Results Summary")
    print("=" * 60)
    print(f"Environment Variables: {'✅ PASS' if env_test else '❌ FAIL'}")
    print(f"Configuration Loading: {'✅ PASS' if config_test else '❌ FAIL'}")
    
    if env_test and config_test:
        print("\n🎉 All configuration tests passed!")
        print("🚀 Ready to start the server!")
        return True
    else:
        print("\n⚠️  Some configuration tests failed!")
        print("💡 Check your .env file and environment variables")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
