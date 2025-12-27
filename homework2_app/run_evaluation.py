#!/usr/bin/env python3
"""
Homework 2 Live Evaluation - Tests semantic search functionality

This script tests the actual semantic search functionality against the running Flask app.
"""

import os
import sys
import requests
import json
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.local')

# Configuration
API_URL = 'http://127.0.0.1:8080/chat/ai'

def get_response_text(result):
    """Safely extract response text from result"""
    if result.get('success'):
        return result.get('response') or ''
    return result.get('error', 'No response')

def send_chat_request(message, session_id='test_session'):
    """Send a chat request to the Flask app"""
    try:
        response = requests.post(API_URL, json={
            'message': message,
            'session_id': session_id
        }, timeout=120)
        return response.json()
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'response': None
        }

def test_msu_semantic_search():
    """Test 1: Semantic Search with Abbreviations (MSU)"""
    print("\n" + "=" * 60)
    print("TEST 1: Semantic Search - 'Find my MSU experience'")
    print("=" * 60)

    result = send_chat_request("Find my MSU experience", session_id='test_msu')
    response_text = get_response_text(result)

    print(f"Response: {response_text[:500]}")

    # Check for full name expansion
    full_name_found = "Michigan State University" in response_text
    # Check for relevant experience information
    experience_found = any(word in response_text.lower() for word in ['experience', 'work', 'position', 'job', 'teaching', 'taught'])

    print(f"\n✓ Full name expansion found: {full_name_found}")
    print(f"✓ Experience information found: {experience_found}")

    if full_name_found and experience_found:
        print("\n✅ TEST 1 PASSED (25/25)")
        return 25
    elif experience_found:
        print("\n⚠️  TEST 1 PARTIAL (10/25) - Has experience but missing full name expansion")
        return 10
    else:
        print("\n❌ TEST 1 FAILED (0/25)")
        return 0

def test_ai_skills_query():
    """Test 2: Complex Semantic Query (AI Skills)"""
    print("\n" + "=" * 60)
    print("TEST 2: Semantic Search - 'What AI skills do I have?'")
    print("=" * 60)

    result = send_chat_request("What AI skills do I have?", session_id='test_ai_skills')
    response_text = get_response_text(result).lower()

    print(f"Response: {response_text[:500]}")

    # Count AI-related terms
    ai_terms = [
        'machine learning', 'ml', 'deep learning', 'neural',
        'nlp', 'natural language', 'ai', 'artificial intelligence',
        'tensorflow', 'pytorch', 'computer vision', 'reinforcement'
    ]

    found_terms = [term for term in ai_terms if term in response_text]

    print(f"\n✓ AI-related terms found: {found_terms}")
    print(f"✓ Number of terms: {len(found_terms)}")

    if len(found_terms) >= 3:
        print("\n✅ TEST 2 PASSED (25/25)")
        return 25
    elif len(found_terms) >= 1:
        print(f"\n⚠️  TEST 2 PARTIAL ({len(found_terms) * 5}/25) - Found some AI terms")
        return len(found_terms) * 5
    else:
        print("\n❌ TEST 2 FAILED (0/25)")
        return 0

def test_human_validation():
    """Test 3: Human Validation Workflow"""
    print("\n" + "=" * 60)
    print("TEST 3: Human Validation - 'Delete all my experiences'")
    print("=" * 60)

    # Step 1: Send dangerous request
    result1 = send_chat_request("Delete all my experiences", session_id='test_validation')
    response1_text = get_response_text(result1)

    print(f"Response 1: {response1_text[:300]}")

    # Check for confirmation request
    confirmation_found = any(word in response1_text.lower() for word in ['confirm', 'proceed', 'yes', 'warning', 'dangerous'])

    print(f"\n✓ Confirmation requested: {confirmation_found}")

    if not confirmation_found:
        print("\n❌ TEST 3 STEP 1 FAILED - No confirmation requested")
        return 0

    # Step 2: Send "no" to cancel
    result2 = send_chat_request("no", session_id='test_validation')
    response2_text = get_response_text(result2)

    print(f"Response 2: {response2_text[:300]}")

    # Check for cancellation
    cancelled_found = any(word in response2_text.lower() for word in ['cancel', 'aborted', 'declined', 'action cancelled'])

    print(f"✓ Cancellation confirmed: {cancelled_found}")

    if confirmation_found and cancelled_found:
        print("\n✅ TEST 3 PASSED (25/25)")
        return 25
    elif confirmation_found:
        print("\n⚠️  TEST 3 PARTIAL (15/25) - Confirmation requested but cancellation unclear")
        return 15
    else:
        print("\n❌ TEST 3 FAILED (0/25)")
        return 0

def test_database_schema():
    """Test 4: Database Schema Verification (Static Check)"""
    print("\n" + "=" * 60)
    print("TEST 4: Database Schema Verification")
    print("=" * 60)

    sql_dir = 'flask_app/database/create_tables'
    tables = ['institutions', 'experiences', 'skills', 'positions', 'users']

    total_points = 0
    max_points = 25  # 3 pts per table for vector column, 2 pts for index

    for table in tables:
        sql_file = f'{sql_dir}/{table}.sql'
        try:
            with open(sql_file, 'r') as f:
                content = f.read()

            has_vector = 'embedding' in content and 'vector(768)' in content
            has_index = 'embedding_idx' in content and 'ivfflat' in content

            if has_vector:
                print(f"✓ {table}: Has embedding vector column")
                total_points += 3
            else:
                print(f"✗ {table}: Missing embedding vector column")

            if has_index:
                print(f"✓ {table}: Has ivfflat index")
                total_points += 2
            else:
                print(f"✗ {table}: Missing ivfflat index")

        except FileNotFoundError:
            print(f"✗ {table}: SQL file not found")

    print(f"\nScore: {total_points}/25")

    if total_points >= 25:
        print("✅ TEST 4 PASSED (25/25)")
        return 25
    else:
        print(f"❌ TEST 4 FAILED ({total_points}/25)")
        return total_points

def main():
    """Run all tests"""
    print("\nWaiting for Flask app to be ready...")
    time.sleep(2)

    scores = {}

    try:
        # Test 4 first (static check, doesn't need API)
        scores['Test 4: Schema'] = test_database_schema()

        # Then run live tests
        scores['Test 1: MSU Search'] = test_msu_semantic_search()
        scores['Test 2: AI Skills'] = test_ai_skills_query()
        scores['Test 3: Validation'] = test_human_validation()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Final Summary
    print("\n" + "=" * 60)
    print("FINAL SCORE SUMMARY")
    print("=" * 60)

    total_score = 0
    for test_name, score in scores.items():
        status = "✅ PASSED" if score >= 25 else "⚠️  PARTIAL" if score > 0 else "❌ FAILED"
        print(f"{test_name}: {score}/25 {status}")
        total_score += score

    print("=" * 60)
    print(f"TOTAL SCORE: {total_score}/100 ({total_score}%)")
    print("=" * 60)

    if total_score >= 100:
        print("\n🎉 PERFECT SCORE! All tests passed!")
    elif total_score >= 75:
        print("\n✓ Good score! Most functionality working.")
    elif total_score >= 50:
        print("\n⚠️  Partial success. Some fixes needed.")
    else:
        print("\n❌ Multiple issues detected. Major fixes needed.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
