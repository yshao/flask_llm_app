# Author: Prof. MM Ghassemi <ghassem3@msu.edu>
# Homework 2: Vector Embeddings Service

"""
Vector embeddings service using Google Gemini API.

Generates 768-dimensional embeddings for text content to enable
semantic similarity search across database records.
"""

import os
import time
import random
import google.generativeai as genai

# Gemini's text-embedding-004 produces 768-dimensional vectors
EMBEDDING_DIM = 768


def generate_embedding(text: str, max_retries: int = 3) -> list:
    """
    Generate embedding for text using Gemini API with retry logic.

    This function converts text into a 768-dimensional vector representation
    that captures semantic meaning, enabling similarity-based searches.

    Args:
        text: Text string to embed
        max_retries: Maximum number of retry attempts for transient failures

    Returns:
        List of 768 floats representing the embedding vector.
        Returns None if text is empty or all retries fail.
    """
    if not text or not text.strip():
        print("[embeddings] Warning: Empty text provided")
        return None

    for attempt in range(max_retries):
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("[embeddings] Warning: GEMINI_API_KEY not set")
                return None

            # Configure Gemini API (only once)
            genai.configure(api_key=api_key)

            # Generate embedding
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text.strip(),
                task_type="retrieval_document"
            )

            embedding = result['embedding']
            print(f"[embeddings] Generated {len(embedding)}-dim embedding for '{text[:50]}...'")
            return embedding

        except Exception as e:
            error_msg = str(e).lower()

            # Check for rate limit or quota errors
            if any(kw in error_msg for kw in ['quota', 'limit', '429', 'rate']):
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"[embeddings] Rate limit hit, waiting {wait_time:.1f}s before retry {attempt+1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[embeddings] Error: Rate limit - all {max_retries} retries exhausted")

            # For other errors, log and return None (don't retry)
            print(f"[embeddings] Error generating embedding: {e}")
            return None

    # All retries exhausted
    print(f"[embeddings] Failed after {max_retries} attempts for '{text[:50]}...'")
    return None


def generate_query_embedding(text: str, max_retries: int = 3) -> list:
    """
    Generate embedding for a search query with retry logic.

    Uses 'retrieval_query' task type which is optimized for
    search/query text rather than document content.

    Args:
        text: Query text to embed
        max_retries: Maximum number of retry attempts

    Returns:
        List of 768 floats representing the embedding vector.
        Returns None if text is empty or all retries fail.
    """
    if not text or not text.strip():
        print("[embeddings] Warning: Empty query text provided")
        return None

    for attempt in range(max_retries):
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("[embeddings] Warning: GEMINI_API_KEY not set")
                return None

            genai.configure(api_key=api_key)
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text.strip(),
                task_type="retrieval_query"
            )

            embedding = result['embedding']
            print(f"[embeddings] Generated {len(embedding)}-dim query embedding for '{text[:50]}...'")
            return embedding

        except Exception as e:
            error_msg = str(e).lower()

            if any(kw in error_msg for kw in ['quota', 'limit', '429', 'rate']):
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"[embeddings] Rate limit hit, waiting {wait_time:.1f}s before retry")
                    time.sleep(wait_time)
                    continue

            print(f"[embeddings] Error generating query embedding: {e}")
            return None

    return None


def cosine_similarity(embedding1: list, embedding2: list) -> float:
    """
    Calculate cosine similarity between two embeddings.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        Float between -1 and 1, where 1 is identical.
    """
    import math

    if len(embedding1) != len(embedding2):
        raise ValueError(f"Embedding dimensions must match: {len(embedding1)} vs {len(embedding2)}")

    dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
    magnitude1 = math.sqrt(sum(a * a for a in embedding1))
    magnitude2 = math.sqrt(sum(b * b for b in embedding2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)
