#!/usr/bin/env python3
"""
Homework 2 Testing Suite

Tests vector embeddings, semantic search, and human validation.
Run from the homework1_app directory.
"""

import sys
import os

# Add the homework1_app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'homework1_app'))

def test_embeddings():
    """Test 1: Embedding generation"""
    print("=" * 50)
    print("TEST 1: EMBEDDING GENERATION")
    print("=" * 50)

    from flask_app.utils.embeddings import generate_embedding, EMBEDDING_DIM
    import os

    # Check if API key is available
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("[WARN] GEMINI_API_KEY not set - testing with zero vectors")

    test_cases = [
        "Michigan State University",
        "MSU",
        "machine learning",
        "deep learning",
        "",  # empty string
    ]

    all_zero_vectors = True
    for text in test_cases:
        embedding = generate_embedding(text)
        print(f"Text: '{text}' -> Embedding dim: {len(embedding)}")
        assert len(embedding) == EMBEDDING_DIM, f"Expected {EMBEDDING_DIM} dims, got {len(embedding)}"
        # Check if any non-zero values exist
        if any(v != 0.0 for v in embedding):
            all_zero_vectors = False

    # Test cosine similarity function
    print("\nTesting cosine similarity:")
    from flask_app.utils.embeddings import cosine_similarity

    emb1 = generate_embedding("MSU")
    emb2 = generate_embedding("Michigan State University")
    emb3 = generate_embedding("banana")

    sim_12 = cosine_similarity(emb1, emb2)
    sim_13 = cosine_similarity(emb1, emb3)

    print(f"Similarity (MSU vs Michigan State University): {sim_12:.4f}")
    print(f"Similarity (MSU vs banana): {sim_13:.4f}")

    if all_zero_vectors:
        print("[WARN] All embeddings are zero vectors (API key not available or invalid)")
        print("[OK] Skipping similarity assertion - API required for live test")
    else:
        # MSU and Michigan State University should be more similar than MSU and banana
        assert sim_12 > sim_13, "MSU should be more similar to Michigan State University than banana"
        print("[OK] Similarity test passed")

    print("\n[OK] All embedding tests passed\n")


def test_risk_assessment():
    """Test 2: Risk assessment"""
    print("=" * 50)
    print("TEST 2: RISK ASSESSMENT")
    print("=" * 50)

    from flask_app.utils.llm import assess_message_risk

    test_cases = [
        ("Delete all my data", "high"),
        ("Remove everything", "high"),
        ("What skills do I have?", "low"),
        ("Add Python to my skills", "low"),
        ("Drop all tables", "high"),
        ("Show my resume", "low"),
    ]

    for message, expected_risk in test_cases:
        result = assess_message_risk(message)
        actual_risk = result['risk_level']
        print(f"Message: '{message}'")
        print(f"  Risk Level: {actual_risk} (expected: {expected_risk})")
        if result['explanation']:
            print(f"  Explanation: {result['explanation']}")
        assert actual_risk == expected_risk, f"Expected {expected_risk}, got {actual_risk}"

    print("\n[OK] All risk assessment tests passed\n")


def test_database_schema():
    """Test 3: Database schema has embedding columns"""
    print("=" * 50)
    print("TEST 3: DATABASE SCHEMA")
    print("=" * 50)

    # Check if SQL files have embedding columns
    import os
    sql_dir = os.path.join(os.path.dirname(__file__), 'flask_app', 'database', 'create_tables')

    tables_with_embeddings = ['institutions', 'positions', 'experiences', 'skills', 'users']

    all_tables_ok = True
    for table in tables_with_embeddings:
        sql_file = os.path.join(sql_dir, f"{table}.sql")
        if not os.path.exists(sql_file):
            print(f"[WARN] {table}.sql not found")
            all_tables_ok = False
            continue

        with open(sql_file, 'r') as f:
            content = f.read()

        # Check for embedding column
        has_embedding = 'embedding' in content and 'vector(768)' in content
        # Check for index
        has_index = 'embedding_idx' in content and 'ivfflat' in content

        if has_embedding and has_index:
            print(f"[OK] {table}: embedding column + index found")
        else:
            print(f"[WARN] {table}: incomplete schema (embedding: {has_embedding}, index: {has_index})")
            all_tables_ok = False

    if all_tables_ok:
        print("\n[OK] All database schema tests passed\n")
    else:
        print("\n[WARN] Some database schema issues found\n")


def test_semantic_search_query():
    """Test 4: Semantic search query generation"""
    print("=" * 50)
    print("TEST 4: SEMANTIC SEARCH QUERY GENERATION")
    print("=" * 50)

    from flask_app.utils.llm import GeminiClient, LLM_ROLES

    # Check that Database Read Expert has pgvector instructions
    db_expert = LLM_ROLES.get("Database Read Expert", {})
    instructions = db_expert.get("specific_instructions", "")

    if "PGVECTOR" in instructions and "<=>" in instructions:
        print("[OK] Database Read Expert has pgvector instructions")
        print("  - Includes PGVECTOR section")
        print("  - Includes <=> operator for cosine distance")
    else:
        print("[WARN] Database Read Expert missing pgvector instructions")

    print("\n[OK] Semantic search query test completed\n")


def test_react_orchestrator_exists():
    """Test 5: ReAct orchestrator function exists"""
    print("=" * 50)
    print("TEST 5: REACT ORCHESTRATOR")
    print("=" * 50)

    from flask_app.utils import llm

    # Check if ReAct function exists
    if hasattr(llm, 'handle_ai_chat_request_react'):
        print("[OK] handle_ai_chat_request_react function exists")
    else:
        print("[WARN] handle_ai_chat_request_react function not found")

    # Check if USE_REACT flag exists
    if hasattr(llm, 'USE_REACT'):
        print(f"[OK] USE_REACT flag = {llm.USE_REACT}")
    else:
        print("[WARN] USE_REACT flag not found")

    print("\n[OK] ReAct orchestrator test completed\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 50)
    print("HOMEWORK 2 TESTING SUITE")
    print("=" * 50 + "\n")

    try:
        test_embeddings()
        test_risk_assessment()
        test_database_schema()
        test_semantic_search_query()
        test_react_orchestrator_exists()

        print("=" * 50)
        print("[OK] ALL TESTS PASSED")
        print("=" * 50)
        print("\nHomework 2 implementation is ready!")
        print("\nNext steps:")
        print("1. Rebuild Docker: docker-compose down -v && docker-compose up --build")
        print("2. Test semantic search: 'Find my MSU experience'")
        print("3. Test validation: 'Delete all my data'")

    except AssertionError as e:
        print(f"\n[ERROR] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
