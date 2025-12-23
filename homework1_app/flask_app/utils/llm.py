# Author: Prof. MM Ghassemi <ghassem3@msu.edu>
# Homework 1: Multi-Expert AI Agent System

import os
import time
from typing import Dict, List, Optional
from flask import current_app, session, jsonify
from flask_app import socketio
from .socket_events import process_and_emit_message
import google.generativeai as genai
import ast
import re
import json

# Master prompt template for role-based expert system
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
        "domain": "PostgreSQL database queries and data analysis",
        "specific_instructions": "Use database schema provided to answer question below. Respond with only SQL query code. Do not include explanations or markdown formatting.",
        "few_shot_examples": "Q: How long did he work at MSU?\nA: SELECT start_date, end_date FROM positions WHERE institution_id = (SELECT inst_id FROM institutions WHERE name LIKE '%MSU%');",
        "background_context": "Database schema with tables: users(institution_id,email,password,role), institutions(inst_id,name,type,location), positions(position_id,inst_id,title,start_date,end_date,description), experiences(exp_id,position_id,title,description,start_date,end_date), skills(skill_id,experience_id,name,type,level)"
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