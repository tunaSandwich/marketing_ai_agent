#!/usr/bin/env python3
"""Debug model configuration to find where old model is coming from."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

def debug_model_config():
    """Debug all model configuration paths."""
    print("="*60)
    print("MODEL CONFIGURATION DEBUG")
    print("="*60)
    
    print("\n1️⃣ Centralized model config:")
    try:
        from src.models import get_default_model, ClaudeModel
        print(f"   Default model: {get_default_model()}")
        print(f"   Available models: {[m.value for m in ClaudeModel]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2️⃣ Settings object:")
    try:
        from src.utils.config import get_settings
        settings = get_settings()
        print(f"   LLM model from settings: {settings.llm.model}")
        print(f"   LLM API key set: {bool(settings.llm.api_key)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n3️⃣ Direct LLMConfig creation:")
    try:
        from src.utils.config import LLMConfig
        config1 = LLMConfig(api_key="test")
        print(f"   Default LLMConfig model: {config1.model}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        
    print("\n4️⃣ LLMConfig with explicit model:")
    try:
        from src.utils.config import LLMConfig
        from src.models import get_default_model
        config2 = LLMConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY", "test"),
            model=get_default_model()
        )
        print(f"   Explicit LLMConfig model: {config2.model}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        
    print("\n5️⃣ ClaudeClient with config:")
    try:
        from src.llm.client import ClaudeClient
        from src.utils.config import LLMConfig
        from src.models import get_default_model
        
        config = LLMConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY", "test"),
            model=get_default_model()
        )
        client = ClaudeClient(config)
        print(f"   ClaudeClient model: {client._config.model}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n6️⃣ Full engagement manager config path:")
    try:
        from src.reddit.engagement import RedditEngagementManager
        from src.utils.config import RedditConfig, LLMConfig
        from src.brand.loader import BrandLoader
        from src.models import get_default_model
        
        llm_config = LLMConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY", "test_key"),
            model=get_default_model(),
            max_tokens=300,
            temperature=0.9,
        )
        
        print(f"   Before engagement manager: {llm_config.model}")
        
        # Don't actually create the full manager, just check the config
        print(f"   LLM config model: {llm_config.model}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    debug_model_config()