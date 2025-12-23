#!/usr/bin/env python3
"""
Test orchestrator response to see what Gemini is actually generating.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add flask_app to path
sys.path.insert(0, os.path.dirname(__file__))

from flask_app.utils.llm import GeminiClient, LLM_ROLES

def test_orchestrator():
    """Test what the Orchestrator AI returns."""

    # Create Gemini client with explicit parameters
    gemini = GeminiClient(
        model="gemini-2.5-flash",
        max_tokens=4000,
        temperature=0.7
    )

    # Test message that should require database query
    test_message = "show all positions"

    # Use the Orchestrator role
    role_config = LLM_ROLES['Orchestrator']

    # Build prompt
    prompt = f"""You are a {role_config['role']} with expertise in {role_config['domain']}.

Instructions:
{role_config['specific_instructions']}

Context:
{role_config['background_context']}

Examples:
{role_config['few_shot_examples']}

Request:
{test_message}
"""

    print("="*60)
    print("Testing Orchestrator Response")
    print("="*60)
    print(f"\nTest Message: {test_message}\n")
    print("Sending to Gemini...")

    # Send message to Gemini
    result = gemini.send_message(
        message=test_message,
        system_prompt=prompt
    )

    if result['success']:
        print("\n" + "="*60)
        print("RAW ORCHESTRATOR RESPONSE:")
        print("="*60)
        print(result['response'])
        print("="*60)

        # Try to parse it
        try:
            import ast
            parsed = ast.literal_eval(result['response'])
            print("\n[OK] Successfully parsed as Python list!")
            print(f"Number of function calls: {len(parsed)}")
            for i, call in enumerate(parsed, 1):
                print(f"  {i}. {call}")
        except Exception as e:
            print(f"\n[ERROR] Failed to parse: {e}")
            print(f"Error type: {type(e).__name__}")
    else:
        print(f"\n[ERROR] Gemini API error: {result.get('error')}")

if __name__ == "__main__":
    test_orchestrator()
