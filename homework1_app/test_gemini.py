#!/usr/bin/env python3
"""
Test script for Gemini API configuration
Tests the Gemini chatbot functionality independently of Flask app
"""

import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

def test_gemini_config():
    """Test Gemini API configuration and connectivity"""

    print("="*60)
    print("Gemini API Configuration Test")
    print("="*60)

    # Get configuration from environment
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    max_tokens = int(os.getenv('GEMINI_MAX_TOKENS', 4000))
    temperature = float(os.getenv('GEMINI_TEMPERATURE', 0.7))

    # Display configuration
    print(f"\nConfiguration:")
    print(f"  API Key: {'*' * 20}{api_key[-10:] if api_key else 'NOT SET'}")
    print(f"  Model: {model_name}")
    print(f"  Max Tokens: {max_tokens}")
    print(f"  Temperature: {temperature}")
    print()

    # Validate API key
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not set in .env file")
        return False

    # Configure Gemini
    try:
        genai.configure(api_key=api_key)
        print("[OK] API key configured successfully")
    except Exception as e:
        print(f"[ERROR] configuring API key: {str(e)}")
        return False

    # Initialize model
    try:
        model = genai.GenerativeModel(model_name)
        print(f"[OK] Model '{model_name}' initialized successfully")
    except Exception as e:
        print(f"[ERROR] initializing model: {str(e)}")
        print(f"\nPossible issue: Model name '{model_name}' may not exist")
        print(f"Valid model names include: gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash-exp")
        return False

    return True


def test_simple_chat():
    """Test a simple chat interaction"""

    print("\n" + "="*60)
    print("Simple Chat Test")
    print("="*60)

    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    max_tokens = int(os.getenv('GEMINI_MAX_TOKENS', 4000))
    temperature = float(os.getenv('GEMINI_TEMPERATURE', 0.7))

    try:
        # Configure and initialize
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        # Generation config
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }

        # Test message
        test_message = "Say 'Hello! Gemini is working correctly.' in exactly those words."
        print(f"\nSending test message: '{test_message}'")
        print("\nWaiting for response...")

        # Generate response
        response = model.generate_content(
            test_message,
            generation_config=generation_config
        )

        # Display response
        print(f"\n[OK] Response received:")
        print(f"{'─'*60}")
        print(response.text)
        print(f"{'─'*60}")

        return True

    except Exception as e:
        print(f"\n[ERROR] during chat test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_database_query_generation():
    """Test generating SQL queries like the Database Read Expert"""

    print("\n" + "="*60)
    print("Database Query Generation Test")
    print("="*60)

    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        # Simulate Database Read Expert prompt
        schema = """
Database schema with tables:
- users(role,email,password)
- institutions(inst_id,type,name,department,address,city,state,zip)
- positions(position_id,inst_id,title,responsibilities,start_date,end_date)
- experiences(experience_id,position_id,name,description,hyperlink,start_date,end_date)
- skills(skill_id,experience_id,name,skill_level)
"""

        prompt = f"""You are a Database Read Expert with expertise in PostgreSQL database queries.

Instructions:
Use database schema provided to answer question below. Respond with only SQL query code. Do not include explanations or markdown formatting.

Context:
{schema}

Examples:
Q: How long did he work at MSU?
A: SELECT start_date, end_date FROM positions WHERE inst_id = (SELECT inst_id FROM institutions WHERE name LIKE '%MSU%');

Q: What skills does he have?
A: SELECT DISTINCT name FROM skills ORDER BY name;

Request:
Show all positions
"""

        print("\nGenerating SQL query for: 'Show all positions'")
        print("\nWaiting for response...")

        response = model.generate_content(prompt)

        print(f"\n[OK] Generated SQL Query:")
        print(f"{'─'*60}")
        print(response.text)
        print(f"{'─'*60}")

        return True

    except Exception as e:
        print(f"\n[ERROR] during query generation test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""

    print("\n" + "GEMINI CHATBOT TEST SUITE".center(60))
    print()

    # Test 1: Configuration
    if not test_gemini_config():
        print("\n[ERROR] Configuration test failed. Aborting remaining tests.")
        sys.exit(1)

    # Test 2: Simple chat
    if not test_simple_chat():
        print("\n[ERROR] Simple chat test failed.")
        sys.exit(1)

    # Test 3: Database query generation
    if not test_database_query_generation():
        print("\n[ERROR] Database query generation test failed.")
        sys.exit(1)

    # All tests passed
    print("\n" + "="*60)
    print("[OK] ALL TESTS PASSED!")
    print("="*60)
    print("\nGemini API is configured correctly and working as expected.")
    print("The chatbot should work properly in the Flask application.\n")


if __name__ == "__main__":
    main()
