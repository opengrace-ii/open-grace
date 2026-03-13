#!/usr/bin/env python3
"""
Test script to verify Gemini API integration works.
Run this to test your Gemini API key before using agents.
"""

import os
import sys

# Add the project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from open_grace.model_router.clients import GeminiClient, ModelProvider

def test_gemini():
    """Test Gemini API connection."""
    
    # Get API key from environment or prompt
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        print("\nTo set your API key:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        print("\nGet your API key from: https://makersuite.google.com/app/apikey")
        return False
    
    print(f"✓ Found GEMINI_API_KEY (starts with: {api_key[:8]}...)")
    
    try:
        # Create Gemini client
        print("\n🔄 Creating Gemini client...")
        client = GeminiClient(api_key=api_key)
        
        # Test simple generation
        print("🔄 Testing simple generation...")
        response = client.generate(
            prompt="What is 2 + 2? Answer with just the number.",
            system="You are a helpful assistant."
        )
        
        print(f"\n✅ SUCCESS! Gemini API is working")
        print(f"   Model: {response.model}")
        print(f"   Response: {response.content.strip()}")
        print(f"   Latency: {response.latency_ms:.0f}ms")
        
        # Test chat
        print("\n🔄 Testing chat mode...")
        chat_response = client.chat([
            {"role": "user", "content": "Hello! What can you help me with?"}
        ])
        
        print(f"✅ Chat mode working!")
        print(f"   Response: {chat_response.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check your API key is correct")
        print("  2. Ensure you have billing enabled on Google AI Studio")
        print("  3. Check your internet connection")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Open Grace - Gemini API Test")
    print("=" * 60)
    
    success = test_gemini()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Gemini API is ready to use with Open Grace agents!")
        print("\nNext steps:")
        print("  1. Start the API server: uvicorn open_grace.api.server:app --reload")
        print("  2. Open the dashboard and create a task")
        print("  3. Agents will use Gemini for AI reasoning")
    else:
        print("❌ Gemini API test failed")
        print("\nPlease fix the issues above and try again.")
    print("=" * 60)