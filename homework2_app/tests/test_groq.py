#!/usr/bin/env python3
"""
Test script for Groq API configuration
Tests the Groq chatbot functionality independently of Flask app
"""

import os
import sys
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

def test_groq_config():
    """Test Groq API configuration and connectivity"""

    print("="*60)
    print("Groq API Configuration Test")
    print("="*60)

    # Get configuration from environment
    api_key = os.getenv('GROQ_API_KEY')
    model_name = os.getenv('GROQ_MODEL', 'Llama-4-Maverick-17B-128E')
    max_tokens = int(os.getenv('GROQ_MAX_TOKENS', 4000))
    temperature = float(os.getenv('GROQ_TEMPERATURE', 0.7))

    # Display configuration
    print(f"\nConfiguration:")
    print(f"  API Key: {'*' * 20}{api_key[-10:] if api_key else 'NOT SET'}")
    print(f"  Model: {model_name}")
    print(f"  Max Tokens: {max_tokens}")
    print(f"  Temperature: {temperature}")
    print()

    # Validate API key
    if not api_key:
        print("[ERROR] GROQ_API_KEY not set in .env file")
        return False

    # Configure Groq
    try:
        client = Groq(api_key=api_key)
        print("[OK] API key configured successfully")
    except Exception as e:
        print(f"[ERROR] configuring API key: {str(e)}")
        return False

    # Test model initialization (Groq doesn't initialize upfront)
    print(f"[OK] Model '{model_name}' will be used for requests")

    return True


def test_simple_chat():
    """Test a simple chat interaction"""

    print("\n" + "="*60)
    print("Simple Chat Test")
    print("="*60)

    api_key = os.getenv('GROQ_API_KEY')
    model_name = os.getenv('GROQ_MODEL', 'Llama-4-Maverick-17B-128E')
    max_tokens = int(os.getenv('GROQ_MAX_TOKENS', 4000))
    temperature = float(os.getenv('GROQ_TEMPERATURE', 0.7))

    try:
        # Configure and initialize
        client = Groq(api_key=api_key)

        # Test message
        test_message = "Say 'Hello! Groq is working correctly.' in exactly those words."
        print(f"\nSending test message: '{test_message}'")
        print("\nWaiting for response...")

        # Generate response
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": test_message}],
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Display response
        print(f"\n[OK] Response received:")
        print(f"{'─'*60}")
        print(response.choices[0].message.content)
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

    api_key = os.getenv('GROQ_API_KEY')
    model_name = os.getenv('GROQ_MODEL', 'Llama-4-Maverick-17B-128E')

    try:
        client = Groq(api_key=api_key)

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

        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )

        print(f"\n[OK] Generated SQL Query:")
        print(f"{'─'*60}")
        print(response.choices[0].message.content)
        print(f"{'─'*60}")

        return True

    except Exception as e:
        print(f"\n[ERROR] during query generation test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""

    print("\n" + "GROQ CHATBOT TEST SUITE".center(60))
    print()

    # Test 1: Configuration
    if not test_groq_config():
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
    print("\nGroq API is configured correctly and working as expected.")
    print("The chatbot should work properly in the Flask application.\n")


if __name__ == "__main__":
    main()
