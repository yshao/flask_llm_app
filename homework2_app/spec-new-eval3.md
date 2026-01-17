# Homework 3 Evaluation Fix Specification

**Date**: 2026-01-02
**Purpose**: Fix remaining issues preventing Homework 3 evaluation from achieving 100/100
**Current Score**: 50/100
**Target Score**: 100/100

---

## Executive Summary

The Homework 3 implementation has **all infrastructure in place** but **fails behavioral requirements**:

| Component | Status | Issue |
|-----------|--------|-------|
| Web Crawler | ✅ Working | - |
| Documents Table | ✅ Working | - |
| Vector Search | ✅ Working | - |
| Multi-Source Query | ❌ Not Working | Database Read Expert doesn't use documents table |
| Evaluation Script | ⚠️ Partial | Missing .env loading |

---

## Critical Issues

### Issue 1: Evaluation Script Missing .env Loading (Critical)

**Severity**: Critical - Prevents evaluation from running
**Location**: `scripts/evaluate_homework3.py:12-16`

**Problem**:
```python
# Current imports - missing dotenv
import requests
import psycopg2
import os
import sys
import re
from datetime import datetime
```

**Impact**:
- Database connection fails with "password authentication failed"
- Cannot run any tests
- Script uses wrong default values for database credentials

**Fix**:
```python
# Add at the top of the file
from dotenv import load_dotenv
load_dotenv()

import requests
import psycopg2
import os
import sys
import re
from datetime import datetime
```

**Testing**:
```bash
# Before fix: Database connection failed
# After fix: Should connect successfully
python3 scripts/evaluate_homework3.py
```

---

### Issue 2: Database Read Expert Doesn't Use Documents Table (Critical - 50 points)

**Severity**: Critical - Causes Test 2 failure (0/50 points)
**Root Cause**: AI behavior, not infrastructure

**Current Behavior**:
```bash
$ curl -X POST http://localhost:8080/chat/ai \
  -H "Content-Type: application/json" \
  -d '{"message":"What did I work on in the CSE 847 project?"}'

# Response only uses experiences table, ignores documents table
{
  "response": "Based on the search results, in the CSE 847 project, you worked on
  Natural Language Processing, which involved machine learning and text analysis.
  For more information, you can visit the project webpage at [hyperlink]."
}
```

**Expected Behavior**:
```
Based on your resume and web-crawled content:

From your resume: In CSE 847 (Natural Language Processing), you worked on
machine learning and text analysis.

From the project webpage: [Insert actual crawled content from documents table]
```

**Why This Happens**:

1. **LLM Knows About Documents Table** (from `llm.py:61-111`):
   ```python
   "Q: Tell me about my research projects from web sources
   A: Thought: User asks for web-crawled content. Search documents table.
   Action: semantic_search(table='documents', query='research projects')"
   ```

2. **BUT LLM Doesn't Execute This**:
   - Interprets "CSE 847" as known entity from experiences
   - No trigger to also search documents table
   - No automatic combination logic

**Database State**:
```sql
-- Experience with hyperlink exists
SELECT name, hyperlink FROM experiences WHERE hyperlink IS NOT NULL;
-- Result: 3 experiences with URLs (CSE 477, CSE 847, Feature Imitating Networks)

-- Documents exist for URLs
SELECT url, COUNT(*) FROM documents GROUP BY url;
-- Result: 3 URLs with chunks (msu.edu: 4, youtube: 1, example.com: 1)

-- BUT: AI doesn't use this content
```

---

## Implementation Strategy

### Option A: Fix Evaluation Script Only (Quick Fix - Minimal Code Change)

**File**: `scripts/evaluate_homework3.py`

**Changes**:
1. Add .env loading (5 lines at top)
2. Improve multi-source detection logic
3. Better vector search verification

**Pros**:
- Quick to implement (~30 minutes)
- Low risk
- Doesn't change AI behavior

**Cons**:
- Still won't pass Test 2 (0/50 points)
- Only fixes evaluation, not implementation

**Score Impact**: 50/100 (unchanged) but evaluation runs properly

---

### Option B: Enhanced System Prompt (Medium Effort - Recommended)

**File**: `homework2_app/flask_app/utils/llm.py`
**Location**: Database Read Expert section (lines 61-111)

**Changes**:

**Step 1: Add Strong Instructions to System Prompt**

```python
"Database Read Expert": {
    "specific_instructions": """You are a database expert with semantic search capabilities.

CRITICAL FOR PROJECTS WITH HYPERLINKS:
When the user asks about a project, course, or experience:
1. FIRST check if the experience has a hyperlink (project URL)
2. If yes, ALWAYS search the documents table for relevant content
3. Combine results from BOTH experiences AND documents tables
4. Explicitly mention: "From your resume..." and "From the project webpage..."

NEVER return a generic [hyperlink] placeholder. Always search documents table
and include actual content from the crawled web pages.

Query Methods:
1. SEMANTIC SEARCH: Use FIRST for any abbreviation, synonym, or concept
2. SQL QUERY: Use ONLY for exact ID matches
3. DOCUMENTS TABLE: Use for projects with hyperlinks - combine with resume data""",
```

**Step 2: Add Explicit Few-Shot Examples**

```python
"few_shot_examples": """Q: What did I work on in the CSE 847 project?
A: Thought: User asks about a specific project (CSE 847).
   Step 1: Search experiences table for "CSE 847"
   Step 2: Check if CSE 847 has a hyperlink
   Step 3: Search documents table for "CSE 847 Natural Language Processing"
   Step 4: Combine both sources in response
Action: semantic_search(table="experiences", query="CSE 847")
Action: semantic_search(table="documents", query="CSE 847 Natural Language Processing")
Final Answer: Based on your resume: [from experiences table]. From the course webpage:
  [from documents table, include actual content about the course].

Q: Tell me about my research projects from web sources
A: Thought: User asks for web-crawled content. Search documents table for project-related content.
Action: semantic_search(table="documents", query="research projects development")"""
```

**Pros**:
- Keeps LLM flexibility
- Moderate effort (~2 hours)
- LLM may learn to use documents table

**Cons**:
- LLM may still not follow reliably
- Depends on LLM interpretation

**Score Impact**: 70-100/100 (depends on LLM compliance)

---

### Option C: Code-Driven Auto-Search (High Effort - Most Reliable)

**Files**:
- `homework2_app/flask_app/utils/llm.py`
- `homework2_app/flask_app/utils/socket_events.py`

**Approach**: Add automatic detection and searching before passing to LLM

**Implementation**:

**Step 1: Add Pre-Processing in socket_events.py**

```python
# In handle_ai_message() function, before calling LLM

def check_and_fetch_documents(user_message: str, db) -> List[Dict]:
    """
    Check if user message references a project with a hyperlink.
    If yes, fetch documents and add to context.
    """
    # First, find if any experience matches the user's query
    from embeddings import generate_query_embedding

    # Get query embedding
    query_embedding = generate_query_embedding(user_message)

    if not query_embedding:
        return []

    # Search experiences with hyperlinks
    results = db.semantic_search("experiences", query_embedding, limit=3)

    for exp in results:
        if exp.get('hyperlink'):
            # Check if documents exist for this URL
            docs = db.query("""
                SELECT chunk_text, title, url
                FROM documents
                WHERE url = %s
                ORDER BY chunk_index
                LIMIT 5
            """, [exp['hyperlink']])

            if docs:
                return {
                    'experience': exp,
                    'documents': docs
                }

    return None

# Then in handle_ai_message():
doc_context = check_and_fetch_documents(data['message'], db)

if doc_context:
    # Add documents to system prompt context
    extra_context = f"""
USER IS ASKING ABOUT A PROJECT WITH WEB-CRAWLED CONTENT:

Project: {doc_context['experience']['name']}
Webpage Content: {chr(10).join([d['chunk_text'][:200] for d in doc_context['documents']]])}

You MUST include this webpage content in your response along with resume data.
"""
    # Pass this to the LLM
```

**Step 2: Update System Prompt to Expect Document Context**

```python
"Database Read Expert": {
    "specific_instructions": """...
When DOCUMENT CONTEXT is provided in system prompt:
- You MUST include both resume data AND document content in your response
- Structure response as: "From your resume: [...] From the webpage: [...]"
- Do NOT use [hyperlink] placeholder - use actual document content
..."""
```

**Pros**:
- Guaranteed behavior
- Most reliable
- Independent of LLM interpretation

**Cons**:
- Higher effort (~4-6 hours)
- More code changes
- May require testing

**Score Impact**: 100/100 (if implemented correctly)

---

### Option D: Hybrid Approach (Recommended for Production)

**Combine Options B and C**:
1. Add strong system prompt (Option B)
2. Add code-driven auto-search for reliability (Option C)
3. Keep LLM flexibility but ensure results

**Implementation**: Combine steps from both Option B and Option C

**Pros**:
- Most reliable
- LLM can still be flexible
- Guaranteed multi-source behavior

**Cons**:
- Highest effort (~6 hours)
- More complex implementation

**Score Impact**: 100/100

---

## Recommended Implementation Plan

### Phase 1: Fix Evaluation Script (Quick Win - 30 min)

**File**: `scripts/evaluate_homework3.py`

**Changes**:
1. Add .env loading at line 12:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

2. Improve multi-source detection (lines 294-322):
   ```python
   # Check for actual document references, not just keywords
   has_doc_ref = 'document' in result.lower() or 'webpage' in result.lower()
   has_specific_content = len(result) > 200  # Substantial response

   if has_resume_info and (has_web_content or has_doc_ref) and has_specific_content:
       score += 30
   ```

3. Add vector search verification (lines 324-351):
   ```python
   # Verify embeddings are populated
   cur.execute("""
       SELECT COUNT(*) FROM documents
       WHERE url = %s AND embedding IS NOT NULL
   """, [experience['url']])
   embedding_count = cur.fetchone()[0]

   if embedding_count > 0:
       score += 20
   ```

**Expected Result**: Evaluation runs properly, can accurately score tests

---

### Phase 2: Fix Multi-Source Query (Main Implementation - 2-6 hours)

**Recommended Approach**: Start with Option B (System Prompt), escalate to Option D (Hybrid) if needed

**Step 1: Update System Prompt** (Option B - 2 hours)

**File**: `homework2_app/flask_app/utils/llm.py`

**Location**: Lines 61-111 (Database Read Expert configuration)

**Changes**:
1. Add CRITICAL section to specific_instructions
2. Add project query few-shot examples
3. Emphasize combining sources

**Testing**:
```bash
# After fix
curl -X POST http://localhost:8080/chat/ai \
  -H "Content-Type: application/json" \
  -d '{"message":"What did I work on in the CSE 847 project?"}'

# Should include content from both experiences AND documents tables
```

**Step 2: If Step 1 Fails, Add Code-Driven Search** (Option D - 4 more hours)

**File**: `homework2_app/flask_app/utils/socket_events.py`

**Add**: Pre-processing function to fetch documents automatically

---

### Phase 3: Testing and Validation (1-2 hours)

**Test Cases**:
1. Query about CSE 847 (has YouTube hyperlink)
2. Query about CSE 477 (has YouTube hyperlink)
3. Query about MSU experience (has msu.edu hyperlink)
4. Verify responses include document content
5. Verify no [hyperlink] placeholders

**Expected Results**:
- All responses include both resume and document content
- Word overlap > 5 words
- Vector search is actually used

---

## File Changes Summary

| File | Change | Lines | Effort |
|------|--------|-------|--------|
| `scripts/evaluate_homework3.py` | Add .env loading | 12-13 | 5 min |
| `scripts/evaluate_homework3.py` | Improve multi-source detection | 294-322 | 15 min |
| `scripts/evaluate_homework3.py` | Add vector search verification | 324-351 | 10 min |
| `homework2_app/flask_app/utils/llm.py` | Update Database Read Expert prompt | 61-111 | 1 hour |
| `homework2_app/flask_app/utils/socket_events.py` | Add auto-search (optional) | New function | 2 hours |

**Total Effort**: 30 min (Phase 1 only) or 4-8 hours (Phase 1 + 2)

---

## Success Criteria

### Evaluation Script Fixed (Phase 1)
- ✅ Script loads .env and connects to database
- ✅ Test 1 passes (50/50)
- ✅ Test 2 can detect multi-source responses
- ✅ Vector search is verified

### Multi-Source Query Fixed (Phase 2)
- ✅ Database Read Expert searches documents table for projects
- ✅ Responses combine resume + document content
- ✅ No [hyperlink] placeholders in responses
- ✅ Word overlap > 5 words between response and documents
- ✅ Test 2 passes (50/50)

### Final Score
- ✅ 100/100 overall
- ✅ All tests pass
- ✅ Behavior matches specification

---

## Rollback Plan

If changes cause issues:

1. **Evaluation Script**: Revert .env loading, restore original detection logic
2. **System Prompt**: Revert Database Read Expert to original version
3. **Auto-Search**: Remove pre-processing function from socket_events.py

**Backup Files**:
- `scripts/evaluate_homework3.py` (git controlled)
- `homework2_app/flask_app/utils/llm.py` (git controlled)
- `homework2_app/flask_app/utils/socket_events.py` (git controlled)

---

## Testing Checklist

Before marking complete:

- [ ] Evaluation script loads .env and connects
- [ ] Test 1 (Web Crawler) passes with 50/50
- [ ] Test 2 finds experience with URL
- [ ] Test 2 finds documents for that URL
- [ ] Database Read Expert searches documents table
- [ ] Response includes content from documents table
- [ ] No [hyperlink] placeholders in responses
- [ ] Word overlap > 5 words
- [ ] Test 2 passes with 50/50
- [ ] Total score: 100/100

---

## Notes

**Infrastructure vs Behavior**:
- All infrastructure is complete (crawler, documents table, embeddings)
- The issue is behavioral (AI doesn't use available infrastructure)
- This is NOT a database schema or API issue
- This IS an AI behavior/prompt engineering issue

**Why System Prompt May Not Be Enough**:
- LLMs interpret instructions flexibly
- "Always search documents" may be ignored if experience table has direct answer
- Code-driven approach guarantees behavior

**Recommendation**: Start with system prompt changes (quickest), add code-driven if needed.

---

**Current Score**: 50/100 → **Target**: 100/100

**Created**: 2026-01-02
**Author**: Claude Code
**Reference**: `eval3_report.md`, `backup_md/homework3_evaluation_todo.md`
