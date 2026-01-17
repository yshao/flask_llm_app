#!/usr/bin/env python3
"""
Test script for web crawler functionality.
Tests the WebCrawlerAgent and documents table integration.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_web_crawler():
    """Test the web crawler with a simple URL."""
    from flask import Flask
    from flask_app.utils.database import database
    from flask_app.utils.a2a_protocol import A2AProtocol, A2AMessage
    from flask_app.utils.web_crawler import WebCrawlerAgent
    from flask_app.utils.llm import GeminiClient

    # Create Flask app for context
    app = Flask(__name__)
    app.config['DATABASE_NAME'] = os.getenv('DATABASE_NAME')
    app.config['DATABASE_HOST'] = os.getenv('DATABASE_HOST')
    app.config['DATABASE_USER'] = os.getenv('DATABASE_USER')
    app.config['DATABASE_PORT'] = int(os.getenv('DATABASE_PORT', 5432))
    app.config['DATABASE_PASSWORD'] = os.getenv('DATABASE_PASSWORD')
    app.config['ENCRYPTION_ONEWAY_SALT'] = os.getenv('ENCRYPTION_ONEWAY_SALT')
    app.config['ENCRYPTION_ONEWAY_N'] = int(os.getenv('ENCRYPTION_ONEWAY_N', 32))
    app.config['ENCRYPTION_ONEWAY_R'] = int(os.getenv('ENCRYPTION_ONEWAY_R', 9))
    app.config['ENCRYPTION_ONEWAY_P'] = int(os.getenv('ENCRYPTION_ONEWAY_P', 1))
    app.config['ENCRYPTION_REVERSIBLE_KEY'] = os.getenv('ENCRYPTION_REVERSIBLE_KEY')

    with app.app_context():
        # Test 1: Verify documents table exists
        print("=" * 60)
        print("Test 1: Verify documents table exists")
        print("=" * 60)
        db = database()
        result = db.query("SELECT COUNT(*) as count FROM documents")
        print(f"✅ Documents table exists. Current records: {result[0]['count']}\n")

        # Test 2: Test A2A Protocol message creation
        print("=" * 60)
        print("Test 2: Test A2A Protocol message creation")
        print("=" * 60)
        a2a = A2AProtocol()
        msg_id = a2a.send_request(
            sender="test_client",
            recipient="web_crawler_agent",
            action="crawl_url",
            params={"url": "https://example.com"}
        )
        print(f"✅ A2A message created with ID: {msg_id}\n")

        # Test 3: Test WebCrawlerAgent initialization
        print("=" * 60)
        print("Test 3: Test WebCrawlerAgent initialization")
        print("=" * 60)
        crawler = WebCrawlerAgent(a2a, llm_client=None)
        print(f"✅ WebCrawlerAgent initialized with agent_id: {crawler.agent_id}")
        print(f"   Chunk size: {crawler.chunk_size} words\n")

        # Test 4: Test crawling a simple URL (without LLM client for faster testing)
        print("=" * 60)
        print("Test 4: Test crawling a URL (example.com)")
        print("=" * 60)

        # Create test message
        message = A2AMessage(
            sender="test_client",
            recipient="web_crawler_agent",
            action="crawl_url",
            params={"url": "https://example.com"}
        )

        # Handle the request
        response = crawler.handle_a2a_request(message)

        # Check response
        print(f"Response action: {response.action}")
        if response.action == "response":
            result = response.params.get("result", {})
            if isinstance(result, dict):
                if result.get("status") == "success":
                    print(f"✅ Web crawl successful!")
                    print(f"   URL: {result.get('url')}")
                    print(f"   Title: {result.get('title')}")
                    print(f"   Chunks created: {result.get('chunks_created')}")
                else:
                    print(f"❌ Web crawl failed: {result.get('error')}")
            else:
                print(f"Response: {result}")

        # Test 5: Verify documents were stored
        print("\n" + "=" * 60)
        print("Test 5: Verify documents were stored in database")
        print("=" * 60)
        result = db.query("SELECT COUNT(*) as count FROM documents")
        new_count = result[0]['count']
        print(f"✅ Total documents in database: {new_count}")

        if new_count > 0:
            # Show first few documents
            docs = db.query("SELECT document_id, url, title, chunk_index, LENGTH(chunk_text) as text_length FROM documents ORDER BY document_id DESC LIMIT 5")
            print("\nRecent documents:")
            for doc in docs:
                print(f"  - ID {doc['document_id']}: {doc['title'][:50]}... ({doc['text_length']} chars, chunk {doc['chunk_index']})")

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

if __name__ == '__main__':
    try:
        test_web_crawler()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
