# Author: AI Agent Benchmark System - Homework 2
#
# Web Crawling Agent for analyzing web content from URLs.
#
# This module provides:
# - URL crawling with HTML parsing
# - Content extraction and cleaning
# - Text segmentation into chunks
# - Vector embedding generation for semantic search
# - A2A protocol integration for agent communication

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from .a2a_protocol import A2AProtocol, A2AMessage
from .embeddings import generate_embedding
from .database import database


#==================================================
# WEB CRAWLER AGENT
#==================================================

class WebCrawlerAgent:
    """
    Web crawler that accepts A2A protocol requests.

    This agent can:
    - Fetch web pages from URLs
    - Clean content using LLM (optional)
    - Segment text into chunks
    - Generate embeddings for each chunk
    - Store chunks in documents table
    """

    def __init__(self, a2a_protocol: Optional[A2AProtocol] = None, llm_client=None):
        """
        Initialize the Web Crawler Agent.

        Args:
            a2a_protocol: A2AProtocol instance for agent communication
            llm_client: Optional LLM client for text cleaning
        """
        self.a2a_protocol = a2a_protocol or A2AProtocol()
        self.agent_id = "web_crawler_agent"
        self.llm = llm_client  # LLM client for text cleaning
        self.chunk_size = 800  # Words per chunk

    def handle_a2a_request(self, message: A2AMessage) -> A2AMessage:
        """
        Handle incoming A2A protocol requests.

        Args:
            message: A2AMessage containing the request

        Returns:
            A2AMessage containing the response
        """
        if message.action == "crawl_url":
            url = message.params.get("url")
            if not url:
                return self.a2a_protocol.send_response(
                    message.message_id,
                    self.agent_id,
                    message.sender,
                    None,
                    error="No URL provided"
                )

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
            None,
            error="Unknown action"
        )

    #==================================================
    # CRAWLING METHODS
    #==================================================
    def _crawl_url(self, url: str) -> Dict[str, Any]:
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
            soup = BeautifulSoup(response.text, 'html.parser')
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
            chunks_stored = 0
            for i, chunk in enumerate(chunks):
                embedding = generate_embedding(chunk)
                if embedding:
                    # Format embedding for PostgreSQL
                    embedding_str = f"[{','.join(map(str, embedding))}]"
                else:
                    # Store with NULL embedding if generation fails
                    embedding_str = None

                # Insert using correct format: columns list, parameters list
                db.insertRows(
                    table='documents',
                    columns=['url', 'title', 'chunk_text', 'chunk_index', 'embedding'],
                    parameters=[[url, title, chunk, i, embedding_str]]
                )
                chunks_stored += 1

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

    #==================================================
    # TEXT PROCESSING METHODS
    #==================================================
    def _clean_text_with_llm(self, text: str) -> str:
        """
        Use LLM to clean web content.

        Args:
            text: Raw text from web page

        Returns:
            Cleaned text with navigation, ads, and irrelevant content removed
        """
        if self.llm:
            # Truncate to avoid overwhelming the LLM
            text_sample = text[:3000] if len(text) > 3000 else text
            prompt = f"""Clean this web content, removing navigation,
ads, and irrelevant text. Return only the main content.

{text_sample}"""
            try:
                cleaned = self.llm.generate(prompt)
                return cleaned if cleaned else text
            except Exception as e:
                print(f"[web_crawler] LLM cleaning failed: {e}, using original text")
                return text
        return text

    def _segment_text(self, text: str) -> list:
        """
        Segment text into chunks of approximately chunk_size words.

        Args:
            text: Text to segment

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
        return chunks
