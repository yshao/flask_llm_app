# Author: Prof. MM Ghassemi <ghassem3@msu.edu>
# Homework 1: Multi-Expert AI Agent System

import os
import time
from typing import Dict, List, Optional
from flask import current_app, session, jsonify
from flask_app import socketio
from .socket_events import process_and_emit_message
from .a2a_protocol import A2AProtocol, A2AMessage
from .web_crawler import WebCrawlerAgent
import google.generativeai as genai
import ast
import re
import json

import sys
# Master prompt template for role-based expert system
USE_REACT = True
MASTER_PROMPT_TEMPLATE = """
You are a {{role}} with expertise in {{domain}}.

Instructions:
{{specific_instructions}}

Context:
{{background_context}}

Examples:
{{few_shot_examples}}

Request:
{{request}}
"""

# Default role configurations (will be replaced by database call)
LLM_ROLES = {
    "Database Read Expert": {
        "role": "Database Read Expert",
        "domain": "PostgreSQL database queries with pgvector semantic search",
        "specific_instructions": """Use database schema provided to answer questions. You have TWO query methods:

1. SEMANTIC SEARCH (pgvector): For abbreviations, synonyms, concept-based queries
   - Use the <=> operator for cosine similarity
   - Format: SELECT *, 1 - (embedding <=> '[query_vector]')/2 as similarity FROM table ORDER BY embedding <=> '[query_vector]' LIMIT 5
   - Always try semantic search first for ambiguous terms

2. EXACT MATCH: For specific IDs or exact values known

IMPORTANT: Always prefer semantic_search when user uses abbreviations (e.g., "MSU") or general concepts (e.g., "AI skills").""",
        "few_shot_examples": """Q: Find my MSU experience
A: Thought: User asks about MSU. This is likely an abbreviation. Use semantic search to find similar institution names.
Action: semantic_search(table="institutions", query="MSU")

Q: What AI skills do I have?
A: Thought: User asks about AI skills. Use semantic search to find semantically related skills.
Action: semantic_search(table="skills", query="artificial intelligence machine learning")

Q: Tell me about my research projects from web sources
A: Thought: User asks for web-crawled content. Search documents table for project-related content.
Action: semantic_search(table="documents", query="research projects")""",
        "background_context": """Database schema with pgvector support:
- institutions(inst_id, name, type, department, address, city, state, zip, embedding)
- positions(position_id, inst_id, title, responsibilities, start_date, end_date, embedding)
- experiences(experience_id, position_id, name, description, start_date, end_date, hyperlink, embedding)
- skills(skill_id, experience_id, name, type, level, embedding)
- users(user_id, email, role, embedding)
- documents(document_id, url, title, chunk_text, chunk_index, embedding, created_at)

DOCUMENTS TABLE (web-crawled content):
- Stores chunks of web pages with 768-dim embeddings for semantic search
- Join with experiences: SELECT d.* FROM documents d JOIN experiences e ON d.url = e.hyperlink
- Semantic search: SELECT chunk_text FROM documents ORDER BY embedding <=> '[vector]' LIMIT 5
- When to use: User asks for details about projects with URLs or external sources

All tables have 768-dim embedding columns. Use <=> operator for cosine distance."""
    },
    "Database Write Expert": {
        "role": "Database Write Expert",
        "domain": "PostgreSQL database modifications and Python database operations",
        "specific_instructions": "Use database schema provided to generate Python code that will modify database. Respond with only Python code using db.insertRows, db.query, or other database methods. Do not include explanations or markdown formatting.",
        "few_shot_examples": "Q: Add Python skill to first experience\nA: exp_id = db.query('SELECT exp_id FROM experiences ORDER BY start_date ASC LIMIT 1')[0]['exp_id'];\ndb.insertRows('skills', ['experience_id', 'name', 'type', 'level'], [exp_id, 'Python', 'Technical', 'Intermediate']);",
        "background_context": "Database schema and available methods: db.query(sql, params), db.insertRows(table, columns, parameters), db.getResumeData()"
    },
    "Content Expert": {
        "role": "Content Expert",
        "domain": "Current page content analysis and contextual responses",
        "specific_instructions": "Analyze provided page content and answer questions based on what's displayed. Reference specific information from the page when relevant. Provide clear, conversational responses.",
        "few_shot_examples": "",
        "background_context": "Page content will be dynamically provided including title, URL, and cleaned HTML content"
    },
    "Orchestrator": {
        "role": "Orchestrator AI",
        "domain": "Multi-expert coordination and task analysis",
        "specific_instructions": "Analyze user question and respond with a list of function calls to handle_ai_chat_request. Each call should specify role and message parameters. Format as a Python list of strings.",
        "few_shot_examples": "Q: Check if he has React skills and add to first experience if missing\nA: ['handle_ai_chat_request(role='Database Read Expert', message='Check for React skills in experiences and skills'), 'handle_ai_chat_request(role='Database Write Expert', message='Add React skill to first experience if missing')]",
        "background_context": "Available experts: Database Read Expert (SQL queries), Database Write Expert (Python database operations), Content Expert (page analysis)"
    }
}


class GeminiClient:
    """Client for interacting with Google's Gemini API with role-based expert support"""

    def __init__(self, api_key: Optional[str] = None, model: str = None,
                 max_tokens: int = None, temperature: float = None):
        """Initialize Gemini client

        Args:
            api_key: Google API key. If not provided, will try to get from environment variable GEMINI_API_KEY
            model: Gemini model to use. If not provided, will use config default
            max_tokens: Maximum tokens in response. If not provided, will use config default
            temperature: Response randomness (0.0-1.0). If not provided, will use config default
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass api_key parameter.")

        # Configure Gemini with API key
        genai.configure(api_key=self.api_key)

        # Get configuration values
        self.model_name       = model       or current_app.config.get('GEMINI_MODEL')
        self.max_tokens        = max_tokens  or current_app.config.get('GEMINI_MAX_TOKENS')
        self.temperature        = temperature or current_app.config.get('GEMINI_TEMPERATURE')

        # Initialize the model
        self.model = genai.GenerativeModel(self.model_name)

        # Configure generation parameters
        self.generation_config = {
            "max_output_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

    def _build_prompt_from_template(self, role_config: dict, request: str) -> str:
        """Build parameterized prompt from role configuration.

        Args:
            role_config: Dictionary containing role configuration
            request: The user's request to process

        Returns:
            Formatted prompt string with role context
        """
        prompt_parts = []

        # Add role and domain
        prompt_parts.append(f"You are a {role_config['role']} with expertise in {role_config['domain']}.")

        # Add instructions if available
        if role_config.get('specific_instructions'):
            prompt_parts.append(f"\nInstructions:\n{role_config['specific_instructions']}")

        # Add context if available
        if role_config.get('background_context'):
            prompt_parts.append(f"\nContext:\n{role_config['background_context']}")

        # Add examples if available
        if role_config.get('few_shot_examples'):
            prompt_parts.append(f"\nExamples:\n{role_config['few_shot_examples']}")

        # Add request
        prompt_parts.append(f"\nRequest:\n{request}")

        return '\n'.join(prompt_parts)

    def send_message(self, message: str, conversation_history: Optional[List[Dict]] = None,
                    system_prompt: Optional[str] = None, role: Optional[str] = None) -> Dict:
        """Send a message to Gemini and get a response

        Args:
            message: The user's message
            conversation_history: List of previous messages in conversation
            system_prompt: Custom system prompt to define AI behavior (optional)

        Returns:
            Dictionary containing response and metadata
        """
        if conversation_history is None:
            conversation_history = []

        try:
            # Role-based prompt generation
            if role and role in LLM_ROLES:
                role_config = LLM_ROLES[role]
                system_prompt = self._build_prompt_from_template(role_config, message)

            # Build conversation context
            full_prompt = ""

            # Add system prompt if provided
            if system_prompt:
                full_prompt += f"System: {system_prompt}\n\n"

            # Add conversation history
            for msg in conversation_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    full_prompt += f"User: {content}\n"
                elif role == "assistant":
                    full_prompt += f"Assistant: {content}\n"

            # Add current user message
            full_prompt += f"User: {message}\nAssistant: "

            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=self.generation_config
            )

            # Extract assistant's response
            assistant_message = response.text

            return {
                "success": True,
                "response": assistant_message,
                "usage": {},  # Gemini doesn't provide detailed usage info in the same way
                "model": self.model_name
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Gemini API error: {str(e)}",
                "response": "I'm sorry, I'm having trouble right now. Please try again later."
            }


def handle_ai_chat_request(llm_client: GeminiClient, message: str, system_prompt: str = None,
                         room: str = 'main', page_content: dict = None, role: str = None, emit_to_socket: bool = True):
    """
    Handle AI chat requests with LLM and broadcast responses via SocketIO.

    Args:
        llm_client: Pre-configured LLM client instance
        message: The user's message to send to LLM
        system_prompt: Custom system prompt to define AI behavior (optional)
        room: Chat room to emit AI response to (default: 'main')
        page_content: Dictionary containing page content information (optional)
        role: Expert role to use (Database Read Expert, Database Write Expert, etc.)
        emit_to_socket: Whether to emit the response to Socket.IO (default: True, set False for nested calls)

    Returns:
        Response: JSON response with LLM reply or error message
    """
    try:
        # Get conversation history from session if available
        conversation_history = session.get('chat_history', [])
        system_prompt = system_prompt or current_app.config.get('GEMINI_SYSTEM_PROMPT')

        # Add page content to context for Content Expert
        if role == 'Content Expert' and page_content:
            message_with_context = f"Page Title: {page_content.get('title', 'Unknown')}\nPage URL: {page_content.get('url', '')}\nPage Content:\n{page_content.get('content', '')}\n\nUser Question: {message}"
        else:
            message_with_context = message

        result = llm_client.send_message(message_with_context, conversation_history, system_prompt=system_prompt, role=role)

        if result["success"]:
            # update conversation history
            conversation_history.append({"role": "user", "content": message})
            conversation_history.append({"role": "assistant", "content": result["response"]})
            max_history = current_app.config.get('GEMINI_MAX_CONVERSATION_HISTORY')
            if len(conversation_history) > max_history:
                conversation_history = conversation_history[-max_history:]
            session['chat_history'] = conversation_history

            # Use centralized message processing for AI responses (only if not a nested call)
            if emit_to_socket:
                process_and_emit_message(socketio, result["response"], 'ai', room)

        return jsonify(result)

    except Exception as e:
        print(f"Error in handle_ai_chat_request: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "response": f"An error occurred: {str(e)}"
        }), 500


def assess_message_risk(message: str) -> dict:
    """
    Assess if a message contains potentially dangerous operations.

    Args:
        message: User's message to assess

    Returns:
        dict with risk_level ('high', 'low') and explanation
    """
    dangerous_keywords = ['delete', 'remove', 'clear', 'drop', 'destroy', 'truncate']
    message_lower = message.lower()

    found_keywords = [kw for kw in dangerous_keywords if kw in message_lower]

    if found_keywords:
        return {
            'risk_level': 'high',
            'explanation': f"This request contains potentially dangerous operations: {', '.join(found_keywords)}. This action may modify or delete data.",
            'keywords_found': found_keywords
        }
    else:
        return {
            'risk_level': 'low',
            'explanation': 'This request appears safe to process.',
            'keywords_found': []
        }


def handle_ai_chat_request_react(llm_client: GeminiClient, message: str,
                                 room: str = 'main', page_content: dict = None) -> dict:
    """
    ReAct pattern orchestrator for multi-step reasoning with semantic search.

    This implements the ReAct (Reasoning + Acting) pattern where the LLM:
    1. Thinks about what to do
    2. Selects an action (tool)
    3. Observes the result
    4. Repeats until it can provide a Final Answer

    Args:
        llm_client: Gemini LLM client
        message: User's question
        room: SocketIO room for emitting messages
        page_content: Current page context (not used in current implementation)

    Returns:
        dict with success, response, and reasoning trace
    """
    MAX_ITERATIONS = 10
    from .database import database
    from .embeddings import generate_query_embedding

    db = database()

    # Tool execution functions
    def execute_semantic_search(db, table, query):
        """Execute semantic search using pgvector"""
        try:
            embedding = generate_query_embedding(query)
            if not embedding:
                return "Error: Failed to generate query embedding"
            results = db.semantic_search(table, embedding, limit=5, threshold=0.3)
            return json.dumps({"results": results, "count": len(results)})
        except Exception as e:
            return f"Error: {str(e)}"

    def execute_sql_query(db, sql):
        """Execute SQL query"""
        try:
            results = db.query(sql)
            return json.dumps({"results": results, "count": len(results)})
        except Exception as e:
            return f"Error: {str(e)}"

    # ReAct tools available to the agent
    REACT_TOOLS = {
        "semantic_search": {
            "description": "Search for semantically similar records using vector embeddings. Use when user uses abbreviations, synonyms, or concepts that may have different wording in the database.",
            "parameters": "table (str: 'institutions', 'experiences', 'skills', 'positions', 'users', 'documents'), query (str: text to search for)",
        },
        "sql_query": {
            "description": "Execute a SQL query on the database. Use for exact lookups when you know specific values.",
            "parameters": "sql (str: valid SQL query)",
        },
        "crawl_web": {
            "description": "Crawl a URL to extract detailed information from web pages. Use when user asks about specific project details, company info, or content from URLs in the experiences table.",
            "parameters": "url (str: the URL to crawl)",
        }
    }

    # Build ReAct prompt
    def build_react_prompt(question, observations):
        tools_desc = "\n".join([
            f"- {name}: {tool['description']}\n  Parameters: {tool['parameters']}"
            for name, tool in REACT_TOOLS.items()
        ])

        prompt = f"""You are a helpful AI assistant that answers questions about a resume database.

Available Tools:
{tools_desc}

Database Schema:
- institutions(inst_id, name, type, department, address, city, state, zip, embedding)
- positions(position_id, inst_id, title, responsibilities, start_date, end_date, embedding)
- experiences(experience_id, position_id, name, description, start_date, end_date, hyperlink, embedding)
- skills(skill_id, experience_id, name, type, level, embedding)
- users(user_id, email, role, embedding)
- documents(document_id, url, title, chunk_text, chunk_index, embedding, created_at)

IMPORTANT: All tables have embedding columns for semantic search. Use semantic_search for:
- Abbreviations (e.g., "MSU" → "Michigan State University")
- Synonyms and related terms
- Concept-based queries (e.g., "AI skills" → "machine learning", "deep learning")

Use sql_query only when you need exact matches or have specific IDs.

Instructions:
1. Start with "Thought:" to reason about what to do
2. Use "Action:" followed by tool name and parameters
3. Wait for "Observation:" with tool results
4. Continue reasoning until you can answer
5. Use "Final Answer:" when ready to respond

Question: {question}

"""
        if observations:
            prompt += "\n".join(observations) + "\n"

        return prompt

    # ReAct loop
    observations = []
    iteration = 0

    while iteration < MAX_ITERATIONS:
        # Build prompt with current context
        prompt = build_react_prompt(message, observations)

        # Get LLM response
        result = llm_client.send_message(prompt, conversation_history=[])

        if not result.get("success"):
            return {
                "success": False,
                "response": f"LLM error: {result.get('error', 'Unknown error')}"
            }

        response_text = result["response"].strip()
        print(f"\n[ReAct Iteration {iteration + 1}]")
        print(f"LLM Response:\n{response_text}\n")

        # Check for Final Answer
        if "Final Answer:" in response_text or "FINAL ANSWER:" in response_text:
            final_answer = re.split(r'Final Answer:|FINAL ANSWER:', response_text, maxsplit=1)[-1].strip()
            # Emit to socket
            process_and_emit_message(socketio, final_answer, 'ai', room)

            return {
                "success": True,
                "response": final_answer,
                "iterations": iteration + 1
            }

        # Parse Action
        action_match = re.search(r'Action:\s*(\w+)', response_text, re.IGNORECASE)
        if not action_match:
            observations.append(f"Observation: No valid action found. Please specify an Action.")
            iteration += 1
            continue

        action_name = action_match.group(1).lower()

        # Extract action input - try multiple patterns
        action_input = ""
        input_patterns = [
            r'Action Input:\s*(.+?)(?:\nThought:|\nAction:|$)',
            r'Action:\s*\w+\s*\[(.+?)\]',
            r'Action:\s*\w+\s*\((.+?)\)',
            r'Parameters:\s*\{(.+?)\}',  # Match Parameters: {key: value, key: value}
        ]

        for pattern in input_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                action_input = match.group(1).strip()
                break

        # Execute action
        if action_name == "semantic_search":
            # Try to parse parameters in multiple formats
            table = None
            query = None

            # Format 1: table='X', query='Y'
            table_match = re.search(r'table\s*[:=]\s*[\'"]?(\w+)[\'"]?', action_input, re.IGNORECASE)
            query_match = re.search(r'query\s*[:=]\s*[\'"]([^\'\"]+)[\'"]', action_input, re.IGNORECASE)

            # Format 2: 'table': 'X', 'query': 'Y' (dict-style)
            if not table_match:
                table_match = re.search(r'[\'"]table[\'"]\s*:\s*[\'"]?(\w+)[\'"]?', action_input, re.IGNORECASE)
            if not query_match:
                query_match = re.search(r'[\'"]query[\'"]\s*:\s*[\'"]([^\'\"]+)[\'"]', action_input, re.IGNORECASE)

            # Also check in full response text if not found in action_input
            full_text = response_text.lower()
            if not table_match:
                table_search = re.search(r'[\'"]table[\'"]\s*:\s*[\'"]?(\w+)[\'"]?', full_text)
                if table_search:
                    table_match = table_search
            if not query_match:
                query_search = re.search(r'[\'"]query[\'"]\s*:\s*[\'"]([^\'\"]+)[\'"]', full_text)
                if query_search:
                    query_match = query_search

            if table_match and query_match:
                table = table_match.group(1)
                query = query_match.group(1)
                observation = execute_semantic_search(db, table, query)
            else:
                # Default to institutions/MSU if parsing fails
                observation = execute_semantic_search(db, "institutions", "MSU")

        elif action_name == "sql_query":
            # Extract SQL - could be wrapped in quotes or not
            sql = action_input.strip('"\'')

            # Remove "sql=" prefix if present
            sql = re.sub(r'^sql\s*[:=]\s*', '', sql, flags=re.IGNORECASE)
            sql = sql.strip('"\'')

            observation = execute_sql_query(db, sql)

        elif action_name == "crawl_web":
            # Extract URL from action_input
            url_match = re.search(r'url\s*[:=]\s*[\'"]?([^\'"\\s]+)[\'"]?', action_input, re.IGNORECASE)

            if url_match:
                url = url_match.group(1)
            else:
                # Try dict-style format
                url_match = re.search(r'[\'"]url[\'"]\s*:\s*[\'"]?([^\'"\\s]+)[\'"]?', action_input, re.IGNORECASE)
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
                if isinstance(result, dict):
                    if result.get("status") == "success":
                        observation = f"Web crawl completed: {result.get('title')} - {result.get('chunks_created')} chunks created"
                    else:
                        observation = f"Web crawl failed: {result.get('error')}"
                else:
                    observation = f"Web crawl response: {result}"
            else:
                observation = f"Error: Unexpected response from web crawler: {response.action}"

        else:
            observation = f"Error: Unknown action '{action_name}'. Available: semantic_search, sql_query, crawl_web"

        observations.append(f"Observation: {observation}")
        iteration += 1

    # Max iterations reached
    return {
        "success": False,
        "response": f"Unable to complete request after maximum iterations ({MAX_ITERATIONS}). The agent could not reach a final answer.",
        "iterations": MAX_ITERATIONS,
        "observations": observations
    }


def execute_orchestrator_response(orchestrator_response: str, message: str, page_content: dict = None) -> dict:
    """
    Parse and execute orchestrator-generated function call sequences.

    Args:
        orchestrator_response: String containing Python list of function calls
        message: Original user message
        page_content: Current page context

    Returns:
        Dictionary with combined results and execution status
    """
    try:
        # Log the raw orchestrator response for debugging
        print(f"\n{'='*60}")
        print(f"DEBUG: Raw Orchestrator Response:")
        print(f"{'='*60}")
        print(orchestrator_response)
        print(f"{'='*60}\n")

        # Clean up the orchestrator response before parsing
        # Gemini often generates mixed quotes, so normalize them
        cleaned_response = orchestrator_response.strip()

        # Instead of using ast.literal_eval (which fails on mixed quotes),
        # just extract all handle_ai_chat_request function calls using regex
        import re
        pattern = r"handle_ai_chat_request\([^)]+\)"
        function_calls = re.findall(pattern, cleaned_response)

        if not function_calls:
            # Try to parse as a Python list if regex found nothing
            try:
                function_calls = ast.literal_eval(cleaned_response)
            except:
                function_calls = []

        print(f"DEBUG: Extracted {len(function_calls)} function calls")

        if not isinstance(function_calls, list):
            return {
                'success': False,
                'error': 'Orchestrator response must be a list of function calls',
                'response': 'Invalid orchestrator format'
            }

        results = []

        # Execute each function call in sequence
        for i, function_call in enumerate(function_calls, 1):
            print(f"[{i}/{len(function_calls)}] Executing: {function_call}")

            try:
                # Extract role and message from function call string
                if "handle_ai_chat_request(role=" in function_call:
                    # Parse role and message parameters
                    import re
                    # Updated regex to handle both escaped and unescaped quotes
                    # This pattern matches: role='value' or role="value" and message='value' or message="value"
                    match = re.search(r"role=['\"]([^'\"]+)['\"],?\s*message=['\"]([^'\"]+)['\"]", function_call)

                    print(f"DEBUG: Trying to match: {function_call}")
                    print(f"DEBUG: Match result: {match}")

                    if match:
                        role = match.group(1)
                        expert_message = match.group(2)

                        # Import database and create LLM client for expert
                        from .database import database
                        db = database()
                        gemini = GeminiClient()

                        # Update global LLM_ROLES with database roles
                        global LLM_ROLES
                        db_roles = db.getLLMRoles()
                        if db_roles:
                            LLM_ROLES = db_roles

                        # Execute expert call (don't emit to socket for nested calls)
                        result = handle_ai_chat_request(
                            llm_client=gemini,
                            message=expert_message,
                            role=role,
                            room='main',
                            page_content=page_content,
                            emit_to_socket=False
                        )

                        # result is a Flask Response object, get JSON data first
                        result_data = result.get_json()
                        if result_data and result_data.get('success'):
                            # For database operations, execute the generated code
                            if role in ['Database Read Expert', 'Database Write Expert']:
                                execution_result = execute_database_operation(result_data['response'], role, db)
                                results.append({
                                    'role': role,
                                    'message': expert_message,
                                    'response': execution_result,
                                    'success': True
                                })
                            else:
                                # Content expert responses
                                results.append({
                                    'role': role,
                                    'message': expert_message,
                                    'response': result_data['response'],
                                    'success': True
                                })
                        else:
                            # Handle case where result_data is None or unsuccessful
                            error_msg = result_data.get('error', 'Unknown error') if result_data else 'Failed to get response'
                            results.append({
                                'role': role,
                                'message': expert_message,
                                'response': f"Error: {error_msg}",
                                'success': False
                            })
                    else:
                        return {
                            'success': False,
                            'error': f'Invalid function call format: {function_call}',
                            'response': 'Orchestrator generated invalid function call'
                        }
                else:
                    return {
                        'success': False,
                        'error': f'Invalid function call format: {function_call}',
                        'response': 'Orchestrator generated invalid function call'
                    }

            except Exception as e:
                results.append({
                    'role': 'Unknown',
                    'message': function_call,
                    'response': f"Execution error: {str(e)}",
                    'success': False
                })

        # Synthesize final response
        synthesis_prompt = f"""
        Based on the following expert execution results, provide a comprehensive response to the user's question: "{message}"

        Expert Results:
        {json.dumps(results, indent=2)}

        Provide a clear, integrated response that addresses the original question.
        """

        # Create synthesis LLM call
        gemini = GeminiClient()
        synthesis_result = gemini.send_message(
            message=synthesis_prompt,
            system_prompt="You are a response synthesizer who integrates multiple expert results into coherent answers."
        )

        final_response = synthesis_result.get('response', 'Unable to synthesize response')

        # Emit the final synthesized response to the chat
        from flask_app import socketio
        from .socket_events import process_and_emit_message
        process_and_emit_message(socketio, final_response, 'ai', 'main')

        return {
            'success': True,
            'response': final_response,
            'expert_results': results,
            'orchestrator_calls': len(function_calls)
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Orchestrator execution error: {str(e)}',
            'response': 'Failed to execute orchestrator plan'
        }


def execute_database_operation(generated_code: str, role: str, db) -> str:
    """
    Execute LLM-generated database operation code safely.

    Args:
        generated_code: Python code generated by Database Expert
        role: Type of database operation (Read vs Write)
        db: Database instance for operations

    Returns:
        String with operation result or error message
    """

    try:
        print(f"Executing {role} operation:")
        print("Generated code:")
        print(generated_code)

        if role == 'Database Read Expert':
            # For read operations, expect SQL query
            # Extract SQL from response and execute
            import re
            sql_match = re.search(r'SELECT.*?(?=\\n|$)', generated_code, re.IGNORECASE | re.DOTALL)

            if sql_match:
                sql_query = sql_match.group(0).strip()
                print(f"Executing SQL: {sql_query}")

                # Execute query and format results
                results = db.query(sql_query)
                return f"Query executed successfully. Results: {len(results)} records found.\\n\\nResults: {results[:5]}..."  # Show first 5 results
            else:
                return "No valid SQL query found in expert response."

        elif role == 'Database Write Expert':
            # For write operations, execute the Python code directly
            # Create a safe execution environment with db available
            safe_globals = {'db': db, 'json': json}

            exec(generated_code, safe_globals)
            return "Database write operation completed successfully."

        else:
            return f"Unknown database role: {role}"

    except Exception as e:
        print(f"Database operation error: {str(e)}")
        return f"Database operation failed: {str(e)}"