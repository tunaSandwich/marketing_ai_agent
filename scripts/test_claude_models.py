#!/usr/bin/env python3
"""Test different Claude model names to find working ones."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.llm.client import ClaudeClient
from src.utils.config import LLMConfig

load_dotenv()

def test_model(model_name: str):
    """Test a specific Claude model."""
    print(f"\n🧪 Testing model: {model_name}")
    
    try:
        config = LLMConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=model_name,
            max_tokens=50,
            temperature=0.7,
        )
        
        client = ClaudeClient(config)
        
        # Try health check
        is_healthy = client.health_check()
        
        if is_healthy:
            print(f"   ✅ {model_name} - WORKING")
            return True
        else:
            print(f"   ❌ {model_name} - Health check failed")
            return False
            
    except Exception as e:
        print(f"   ❌ {model_name} - Error: {e}")
        return False

def main():
    """Test multiple Claude model names."""
    print("="*60)
    print("CLAUDE MODEL COMPATIBILITY TEST")
    print("="*60)
    
    # List of model names to try
    models_to_test = [
        "claude-3-haiku-20240307",
        "claude-3-sonnet-20240229", 
        "claude-3-opus-20240229",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet",
        "claude-3-haiku",
        "claude-3-sonnet",
        "claude-3-opus",
    ]
    
    working_models = []
    
    for model in models_to_test:
        if test_model(model):
            working_models.append(model)
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    if working_models:
        print(f"\n✅ Working models ({len(working_models)}):")
        for model in working_models:
            print(f"   - {model}")
        
        print(f"\n💡 Recommended model: {working_models[0]}")
    else:
        print("\n❌ No working models found!")
        print("   Check your ANTHROPIC_API_KEY")

if __name__ == "__main__":
    main()