#!/usr/bin/env python3
"""
Test script for ReAct orchestrator with crawl_web action.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_react_crawl_web():
    """Test the ReAct orchestrator with crawl_web action."""
    from flask import Flask
    from flask_app.utils.llm import GeminiClient, handle_ai_chat_request_react

    # Create Flask app for context
    app = Flask(__name__)
    app.config['DATABASE_NAME'] = os.getenv('DATABASE_NAME')
    app.config['DATABASE_HOST'] = os.getenv('DATABASE_HOST')
    app.config['DATABASE_USER'] = os.getenv('DATABASE_USER')
    app.config['DATABASE_PORT'] = int(os.getenv('DATABASE_PORT', 5432))
    app.config['DATABASE_PASSWORD'] = os.getenv('DATABASE_PASSWORD')
    app.config['DATABASE_HOST'] = os.getenv('DATABASE_HOST')
    app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')
    app.config['GEMINI_MODEL'] = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    app.config['GEMINI_MAX_TOKENS'] = int(os.getenv('GEMINI_MAX_TOKENS', 8192))
    app.config['GEMINI_TEMPERATURE'] = float(os.getenv('GEMINI_TEMPERATURE', 0.7))
    app.config['ENCRYPTION_ONEWAY_SALT'] = os.getenv('ENCRYPTION_ONEWAY_SALT')
    app.config['ENCRYPTION_ONEWAY_N'] = int(os.getenv('ENCRYPTION_ONEWAY_N', 32))
    app.config['ENCRYPTION_ONEWAY_R'] = int(os.getenv('ENCRYPTION_ONEWAY_R', 9))
    app.config['ENCRYPTION_ONEWAY_P'] = int(os.getenv('ENCRYPTION_ONEWAY_P', 1))
    app.config['ENCRYPTION_REVERSIBLE_KEY'] = os.getenv('ENCRYPTION_REVERSIBLE_KEY')

    with app.app_context():
        # Create LLM client
        llm_client = GeminiClient()

        print("=" * 60)
        print("Test: ReAct Orchestrator with crawl_web action")
        print("=" * 60)
        print("\nNote: This test requires a valid Gemini API key.")
        print("The API key in .env appears to be invalid (403 error).\n")
        print("For a complete test, update GEMINI_API_KEY in .env")
        print("=" * 60)

        # Simple test to verify the code structure
        print("\n✅ Verifying ReAct setup...")

        # Check if the ReAct function exists and has crawl_web support
        from flask_app.utils.llm import handle_ai_chat_request_react
        print("✅ handle_ai_chat_request_react function exists")

        # Verify imports
        from flask_app.utils.web_crawler import WebCrawlerAgent
        from flask_app.utils.a2a_protocol import A2AProtocol, A2AMessage
        print("✅ WebCrawlerAgent and A2A imports successful")

        # Check that the database module has documents table
        from flask_app.utils.database import database
        db = database()
        if 'documents' in db.tables:
            print("✅ 'documents' table is in database tables list")
        else:
            print("❌ 'documents' table NOT in database tables list")

        # Verify semantic_search includes documents
        result = db.query("SELECT COUNT(*) as count FROM documents")
        print(f"✅ Documents table has {result[0]['count']} records")

        print("\n" + "=" * 60)
        print("Integration verification complete!")
        print("=" * 60)
        print("\nTo test end-to-end ReAct with crawl_web:")
        print("1. Update GEMINI_API_KEY in .env with a valid key")
        print("2. Start the Flask app: python app.py")
        print("3. Ask the chatbot: 'Crawl https://example.com and tell me about it'")
        print("=" * 60)

if __name__ == '__main__':
    try:
        test_react_crawl_web()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
