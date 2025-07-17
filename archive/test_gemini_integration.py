#!/usr/bin/env python3
"""
Test script to verify Gemini API integration with Sage healthcare system.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend source to Python path
backend_path = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

from integrations.gemini_client import create_gemini_client
from agents.chain_of_thought_engine import ChainOfThoughtEngine
from models.core import UserInput, ProcessingContext, AnalyzedInput


async def test_gemini_connection():
    """Test basic Gemini API connection."""
    print("🧪 Testing Gemini API Connection...")
    
    try:
        # Create Gemini client
        gemini_client = create_gemini_client()
        
        if not gemini_client:
            print("❌ Failed to create Gemini client")
            return False
        
        # Test connection
        result = await gemini_client.test_connection()
        
        if result["status"] == "success":
            print(f"✅ Gemini connection successful!")
            print(f"   Model: {result['model']}")
            print(f"   Response preview: {result['response_preview']}")
            return True
        else:
            print(f"❌ Gemini connection failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gemini connection: {e}")
        return False


async def test_healthcare_response():
    """Test healthcare response generation with Gemini."""
    print("\n🏥 Testing Healthcare Response Generation...")
    
    try:
        # Create chain-of-thought engine
        engine = ChainOfThoughtEngine()
        
        # Create test context
        user_input = UserInput(
            user_id="test_user",
            session_id="test_session",
            content="What are the symptoms of diabetes and how is it diagnosed?",
            input_type="text"
        )
        
        analyzed_input = AnalyzedInput(
            text="What are the symptoms of diabetes and how is it diagnosed?",
            intent="medical_question",
            medical_entities=["diabetes", "symptoms", "diagnosis"],
            urgency_level=3,
            confidence=0.9,
            emotional_context="inquiry"
        )
        
        context = ProcessingContext(
            user_input=user_input,
            analyzed_input=analyzed_input
        )
        
        # Generate response
        print("   Generating healthcare response...")
        response, reasoning_steps = await engine.generate_response(context)
        
        print(f"✅ Healthcare response generated successfully!")
        print(f"   Model used: {response.response_metadata.get('model_provider', 'unknown')}:{response.response_metadata.get('model_used', 'unknown')}")
        print(f"   Confidence level: {response.confidence_level:.2f}")
        print(f"   Reasoning steps: {len(reasoning_steps)}")
        print(f"   Response length: {len(response.content)} characters")
        print(f"   Medical disclaimer: {'✅' if response.medical_disclaimer else '❌'}")
        
        # Show first 200 characters of response
        preview = response.content[:200] + "..." if len(response.content) > 200 else response.content
        print(f"   Response preview: {preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing healthcare response: {e}")
        return False


async def test_model_routing():
    """Test intelligent model routing between OpenAI and Gemini."""
    print("\n🔀 Testing Model Routing...")
    
    try:
        engine = ChainOfThoughtEngine()
        
        # Test different complexity levels
        test_cases = [
            {
                "query": "What is aspirin?",
                "complexity": "simple",
                "entities": ["aspirin"]
            },
            {
                "query": "Explain the pathophysiology of heart failure and treatment options",
                "complexity": "complex", 
                "entities": ["heart failure", "pathophysiology", "treatment"]
            },
            {
                "query": "I'm having chest pain and difficulty breathing - what should I do?",
                "complexity": "critical",
                "entities": ["chest pain", "breathing", "emergency"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"   Test {i}: {test_case['complexity']} query")
            
            # Assess complexity
            user_input = UserInput(
                user_id="test_user",
                session_id="test_session", 
                content=test_case["query"],
                input_type="text"
            )
            
            analyzed_input = AnalyzedInput(
                text=test_case["query"],
                intent="medical_question",
                medical_entities=test_case["entities"],
                urgency_level=8 if test_case["complexity"] == "critical" else 5,
                confidence=0.9
            )
            
            context = ProcessingContext(
                user_input=user_input,
                analyzed_input=analyzed_input
            )
            
            # Check model selection
            complexity = engine._assess_query_complexity(context)
            model_provider, model_name = engine._select_model(complexity)
            
            print(f"      Complexity: {complexity}")
            print(f"      Selected: {model_provider}:{model_name}")
        
        print("✅ Model routing test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing model routing: {e}")
        return False


async def main():
    """Run all Gemini integration tests."""
    print("🚀 Sage - Gemini Integration Test Suite")
    print("=" * 50)
    
    # Check environment variables
    print("🔧 Checking Configuration...")
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"   Gemini API Key: {'✅ Set' if gemini_key else '❌ Missing'}")
    print(f"   OpenAI API Key: {'✅ Set' if openai_key else '❌ Missing'}")
    
    if not gemini_key and not openai_key:
        print("❌ No API keys found. Please set GEMINI_API_KEY or OPENAI_API_KEY")
        return
    
    # Run tests
    tests = [
        ("Gemini Connection", test_gemini_connection),
        ("Healthcare Response", test_healthcare_response),
        ("Model Routing", test_model_routing)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Gemini integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")


if __name__ == "__main__":
    asyncio.run(main())