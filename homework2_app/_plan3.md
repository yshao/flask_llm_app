# Homework 3 Implementation Plan: Web Crawling & Document Storage

**Date**: 2025-12-27
**Current Base**: homework2_app (ReAct + Semantic Search + A2A Protocol complete)
**Target**: homework3_app (Add web crawling + documents table for integrated web content)

---

## Executive Summary

Homework 3 extends the ReAct-based AI agent system by adding:
1. **Web Crawling Agent** - Fetches, cleans, chunks, and stores web content
2. **Documents Table** - Stores web-crawled content with 768-dim embeddings for semantic search
3.  **Orchestrator Enhancement** - Triggers web crawling when URLs exist in experiences table
4. **Database Read Expert Update** - Integrates documents table into semantic search

---

## Current State: homework2_app

### Infrastructure Already in Place

**Core Components:**
- **ReAct Pattern** (llm.py) with semantic_search and sql_query tools
- **768-dim Embeddings** using Gemini text-embedding-004 model
- **A2A Protocol** (a2a_protocol.py) - Complete implementation
- **Semantic Search** - pgvector with IVFFlat indexes on all tables
- **Database** - PostgreSQL with pgvector extension

**Database Schema with Embeddings:**
- `institutions(inst_id, name, type, department, address, city, state, zip, embedding)`
- `positions(position_id, inst_id, title, responsibilities, start_date, end_date, embedding)`
- `experiences(experience_id, position_id, name, description, start_date, end_date, embedding)`
- `skills(skill_id, experience_id, name, type, level, embedding)`
- `users(user_id, email, role, embedding)`

---

## Implementation Plan

### Phase 1: Documents Table Creation

#### File: `homework2_app/flask_app/database/create_tables/documents.sql`

```sql
CREATE TABLE IF NOT EXISTS documents (
    document_id   SERIAL PRIMARY KEY,
    url           varchar(500) NOT NULL,
    title         varchar(500) NOT NULL,
    chunk_text    text NOT NULL,
    chunk_index   integer NOT NULL,
    embedding     vector(768) DEFAULT NULL,
    created_at    timestamp DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (url) REFERENCES experiences(hyperlink)
);

CREATE INDEX IF NOT EXISTS documents_embedding_idx
ON documents USING ivfflat (embedding vector_cosine_ops);
```

**Why vector(768)?**
- Matches homework2's Gemini text-embedding-004 model output
- Consistent with all other embedding columns
- Enables semantic search between resume data and web content

#### File: `homework2_app/flask_app/database/create_tables/experiences.sql`

**Add UNIQUE constraint to hyperlink column:**
```sql
-- Add hyperlink column with UNIQUE constraint
ALTER TABLE experiences ADD COLUMN IF NOT EXISTS hyperlink varchar(500) UNIQUE DEFAULT NULL;
```

---

### Phase 2: Initial Data Setup

#### File: `homework2_app/flask_app/database/initial_data/documents.csv`

```csv
document_id,url,title,chunk_text,chunk_index,embedding,created_at
```

---

### Phase 3: Web Crawling Agent

#### File: `homework2_app/flask_app/utils/web_crawler.py`

```python
"""
Web Crawling Agent for analyzing web content from URLs.

Accepts A2A protocol requests, stores processed content in documents table.
"""

import requests
from bs4 import BeautifulSoup
from .a2a_protocol import A2AProtocol, A2AMessage
from .embeddings import generate_embedding
from .database import database


class WebCrawlerAgent:
    """Web crawler that accepts A2A protocol requests."""

    def __init__(self, a2a_protocol: A2AProtocol = None, llm_client=None):
        self.a2a_protocol = a2a_protocol or A2AProtocol()
        self.agent_id = "web_crawler_agent"
        self.llm = llm_client  # LLM client for text cleaning
        self.chunk_size = 800  # Words per chunk

    def handle_a2a_request(self, message: A2AMessage) -> A2AMessage:
        """Handle incoming A2A protocol requests."""
        if message.action == "crawl_url":
            url = message.params.get("url")
            result = self._crawl_url(url)
            return self.a2a_protocol.send_response(
                message.message_id,
                self.agent_id,
                message.sender,
                result
            )
        return self.a2a_protocol.send_response(
            message.message_id,
            self.agent_id,
            message.sender,
            {"status": "error", "error": "Unknown action"}
        )

    def _crawl_url(self, url: str) -> dict:
        """
        Crawl a web page, clean content, chunk it, and store with embeddings.

        Args:
            url: The URL to crawl

        Returns:
            dict with url, title, chunks_created, status
        """
        try:
            # Fetch web page
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'lxml')
            title = soup.title.string if soup.title else "No title"

            # Remove non-content elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()

            # Extract raw text
            raw_text = soup.get_text(separator=' ', strip=True)

            # Clean text with LLM (remove nav, ads, etc.)
            cleaned_text = self._clean_text_with_llm(raw_text)

            # Segment into chunks
            chunks = self._segment_text(cleaned_text)

            # Generate embeddings and store in database
            db = database()
            for i, chunk in enumerate(chunks):
                embedding = generate_embedding(chunk)
                db.insertRows('documents', [{
                    'url': url,
                    'title': title,
                    'chunk_text': chunk,
                    'chunk_index': i,
                    'embedding': 768-dim vector
                }])

            return {
                "url": url,
                "title": title,
                "chunks_created": len(chunks),
                "status": "success"
            }

        except requests.exceptions.Timeout:
            return {"url": url, "error": "Request timeout", "status": "error"}
        except requests.exceptions.RequestException as e:
            return {"url": url, "error": str(e), "status": "error"}
        except Exception as e:
            return {"url": url, "error": str(e), "status": "error"}

    def _clean_text_with_llm(self, text: str) -> str:
        """Use LLM to clean web content."""
        if self.llm:
            prompt = f"""Clean this web content, removing navigation,
ads, and irrelevant text. Return only the main content.

{text[:3000]}"""
            return self.llm.generate(prompt)
        return text

    def _segment_text(self, text: str) -> list:
        """Segment text into 500-1000 character chunks."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks
```

---

### Phase 4: Update Database Module

#### File: `homework2_app/flask_app/utils/database.py`

**Add 'documents' to tables list:**
```python
self.tables = ['users', 'institutions', 'positions', 'experiences', 'skills', 'documents']
```

**Add embedding generation for documents in insertRows():**
```python
elif table == 'documents':
    for row in data:
        text = f"{row.get('title', '')} {row.get('chunk_text', '')}"
        row['embedding'] = generate_embedding(text.strip())
```

---

### Phase 5: Enhance ReAct Orchestrator

#### File: `homework2_app/flask_app/utils/llm.py`

**Add imports:**
```python
from .web_crawler import WebCrawlerAgent
from .a2a_protocol import A2AProtocol, A2AMessage
```

**Add crawl_web to REACT_TOOLS:**
```python
"crawl_web": {
    "description": "Crawl a URL to extract detailed information from web pages. Use when user asks about specific project details, company info, or content from URLs in the experiences table.",
    "parameters": "url (str: the URL to crawl)"
}
```

**Add crawl_web action handling in ReAct loop:**
```python
elif action_name == "crawl_web":
    # Extract URL from action_input
    url_match = re.search(r'url\s*[:=]\s*[\'"]([^\'\"]+)[\'"]', action_input, re.IGNORECASE)

    if url_match:
        url = url_match.group(1)
    else:
        observation = "Error: No URL provided for crawl_web action."
        observations.append(f"Observation: {observation}")
        iteration += 1
        continue

    # Initialize A2A protocol and web crawler
    a2a = A2AProtocol()
    crawler = WebCrawlerAgent(a2a, llm_client)

    # Create A2A message
    message = A2AMessage(
        sender="orchestrator",
        recipient="web_crawler_agent",
        action="crawl_url",
        params={"url": url}
    )

    # Send request to crawler via A2A protocol
    response = crawler.handle_a2a_request(message)

    # Extract result from response
    if response.action == "response":
        result = response.params.get("result", {})
        if result.get("status") == "success":
            observation = f"Web crawl completed: {result.get('title')} - {result.get('chunks_created')} chunks created"
        else:
            observation = f"Web crawl failed: {result.get('error')}"
    else:
        observation = f"Error: Unexpected response from web crawler: {response.action}"

    observations.append(f"Observation: {observation}")
    iteration += 1
```

---

### Phase 6: Update Database Read Expert Role

#### File: `homework2_app/flask_app/utils/llm.py`

**Update DATABASE_READ_EXPERT background_context:**
```python
DOCUMENTS TABLE (web-crawled content):
- Schema: documents (document_id, url, title, chunk_text, chunk_index, embedding)
- Use for detailed project info from web sources
- Join with experiences: SELECT d.* FROM documents d JOIN experiences e ON d.url = e.hyperlink
- Semantic search: SELECT chunk_text FROM documents ORDER BY embedding <=> '[vector]' LIMIT 5
- When to use: User asks for details about projects with URLs or external sources
```

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `database/create_tables/documents.sql` | Create | Table with 768-dim embeddings |
| `database/create_tables/experiences.sql` | Modify | Add UNIQUE constraint to hyperlink |
| `database/initial_data/documents.csv` | Create | Empty file with headers |
| `utils/web_crawler.py` | Create | WebCrawlerAgent class |
| `utils/database.py` | Modify | Add 'documents' to tables, add embeddings for documents |

---

## Implementation Order

**Step 1: Database** (documents.sql + experiences.sql + documents.csv)

**Step 2: Web Crawler** (web_crawler.py)

**Step 3: Database Module** (database.py updates)

**Step 4: Orchestrator** (llm.py enhancements - imports, crawl_web tool, action handling)

**Step 5: Database Read Expert** (llm.py - update role with documents table info)

---

## Testing Strategy

**Test 1: A2A Protocol**
```python
from flask_app.utils.a2a_protocol import A2AProtocol, A2AMessage
a2a = A2AProtocol()
msg_id = a2a.send_request(
    sender="orchestrator",
    recipient="web_crawler_agent",
    action="crawl_url",
    params={"url": "https://msu.edu"}
)
assert msg_id is not None
```

**Test 2: Documents Table**
```sql
SELECT column_name FROM information_schema.columns WHERE table_name = 'documents';
-- Should see: document_id, url, title, chunk_text, chunk_index, embedding, created_at
```

**Test 3: Web Crawler**
```python
from flask_app.utils.web_crawler import WebCrawlerAgent
crawler = WebCrawlerAgent()
result = crawler._crawl_url("https://msu.edu")
assert result["status"] == "success"
assert result["chunks_created"] > 0
```

**Test 4: Integration - User Query: "Tell me about your research projects from the web"**
- Should: Query positions table for research experience
- Should find URL in experiences table
- Should trigger crawl_web action
- Should retrieve web content from documents table
- Should combine with database results

---

## Key Integration Points

**1. Documents Table:**
- Uses 768-dim embeddings (matches homework2)
- Foreign key to experiences.hyperlink (must be UNIQUE)
- IVFFlat index on embeddings for fast search

**2. A2A Protocol:**
- Web crawler receives "crawl_url" action via A2A message
- Returns result in response.params["result"]
- Orchestrator uses A2AProtocol for agent communication

**3. Orchestrator Enhancement:**
- crawl_web action must parse URL from action_input
- Must initialize A2AProtocol and WebCrawlerAgent
- Must handle response extraction properly

**4. Database Read Expert:**
- Needs to know about documents table structure
- Needs to understand how to join documents with experiences
- Should use semantic search for documents table

---

## Dependencies

- Already present: `requests`, `beautifulsoup4` in requirements.txt

---

## Notes

**Compatibility:**
- Uses 768-dim embeddings (matches homework2)
- Leverages existing semantic_search infrastructure
- Integrates with existing A2A Protocol without breaking changes

**Complexity:** Medium

**Estimated Time:** 2-3 hours for full implementation

---
