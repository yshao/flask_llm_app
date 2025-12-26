# Author: Prof. MM Ghassemi <ghassem3@msu.edu>

from flask import current_app as app
from flask import render_template, redirect, request, session, url_for, jsonify, send_from_directory
from .utils.database import database
from .utils.llm import GeminiClient
from .utils.llm import handle_ai_chat_request
from .utils.llm import handle_ai_chat_request_react
from .utils.llm import execute_orchestrator_response
from .utils.llm import USE_REACT
from .utils.llm import assess_message_risk
from .utils.a2a_protocol import A2AProtocol, A2AMessage
from .utils.evaluation_agent import EvaluationAgent
from bs4 import BeautifulSoup
import json

#--------------------------------------------------
# GLOBAL INSTANCES
#--------------------------------------------------
db = database()
a2a_protocol = A2AProtocol()
evaluation_agent = EvaluationAgent(a2a_protocol, db)

#--------------------------------------------------
# MAIN APPLICATION ROUTES
#--------------------------------------------------

@app.route('/')
def home():
    return render_template('dynamic-page.html', user=db.get_user_email(), page_type='home')

@app.route('/agents')
def agents():
    return render_template('dynamic-page.html', user=db.get_user_email(), page_type='agents')

@app.route('/agents/resume')
def resume():
    return render_template('dynamic-page.html', user=db.get_user_email(), page_type='resume')

@app.route('/api/resume')
def api_resume():
    """API endpoint to serve resume data as JSON for Vue.js frontend."""
    resume_data = db.getResumeData()
    return jsonify({ "success": True, "data": resume_data})

#--------------------------------------------------
# CHAT ROUTES
#--------------------------------------------------
@app.route('/chat/ai', methods=['POST'])
def chat_with_ai():
    # Get message, page content, and system prompt from request data
    data          = request.get_json()
    message       = data.get('message', '').strip()
    page_content  = data.get('pageContent', {})

    # Log the received data for debugging
    print(f"Received message: {message}")
    print(f"Received page content: {page_content}")

    # Check for pending confirmation first
    if 'pending_action' in session:
        if message.lower() in ['yes', 'y', 'ok', 'sure']:
            # User confirmed - execute pending action
            pending = session.pop('pending_action')
            print(f"User confirmed action: {pending['message']}")

            # Execute the pending action
            if USE_REACT:
                return jsonify(handle_ai_chat_request_react(GeminiClient(), pending['message'], 'main', page_content))
            else:
                return process_orchestrator_request(pending['message'], page_content)

        elif message.lower() in ['no', 'n', 'cancel']:
            # User declined - cancel action
            session.pop('pending_action')
            return jsonify({"response": "Action cancelled."})

        else:
            # Invalid response
            return jsonify({"response": "Please respond with 'yes' to proceed or 'no' to cancel."})

    # Assess risk for new messages
    risk = assess_message_risk(message)
    if risk['risk_level'] == 'high':
        # Store and ask for confirmation
        session['pending_action'] = {'message': message}
        return jsonify({
            "response": f"Warning: {risk['explanation']}\n\nDo you want to proceed? (yes/no)",
            "requires_confirmation": True
        })

    # Normal processing
    return process_orchestrator_request(message, page_content)


def process_orchestrator_request(message, page_content):
    """
    Process the request through the orchestrator.

    Args:
        message: User message
        page_content: Current page context

    Returns:
        JSON response
    """
    # Create LLM client and pass it to the handler
    gemini = GeminiClient()

    # Create a dynamic system prompt that leverages page content when relevant
    if page_content and page_content.get('content'):
        
        # Clean HTML content to get clean text
        clean_content = clean_html_content(page_content.get('content', ''))
        
        #Specify prompt to use when responding to the user's message.
        system_prompt = f""" 
            You are a helpful AI assistant. You have access to the current page content that the user is viewing.
            IMPORTANT INSTRUCTIONS:
            1. If the user's question is related to the content on the current page, use that content to provide accurate and relevant answers.
            2. Reference specific information from the page when it helps answer the user's question.
            3. If the user asks about something not covered on the current page, provide general helpful information.
            4. Be conversational and helpful while maintaining accuracy.

            CURRENT PAGE CONTENT:
            Title:   {page_content.get('title', 'Unknown page')}
            URL:     {page_content.get('url', 'N/A')}
            Content: {clean_content}

            Use this content to provide contextually relevant responses when appropriate.
        """

    else:
        # Fallback system prompt when no page content is available
        system_prompt = "You are a helpful AI assistant."
        print("Using fallback system prompt (no page content available)")

    # Use ReAct orchestrator if enabled, otherwise use original orchestrator
    if USE_REACT:
        print("Using ReAct orchestrator")
        result = handle_ai_chat_request_react(gemini, message, 'main', page_content)
        return jsonify(result)
    else:
        print("Using original orchestrator")
        # Use orchestrator by default for multi-expert coordination (don't emit raw plan to socket)
        orchestrator_response = handle_ai_chat_request(llm_client=gemini, message=message, system_prompt=system_prompt, room='main', page_content=page_content, role="Orchestrator", emit_to_socket=False)

        # Get the orchestrator's response
        response_data = orchestrator_response.get_json() if hasattr(orchestrator_response, 'get_json') else orchestrator_response

        if response_data.get('success'):
            orchestrator_plan = response_data.get('response', '')
            print(f"Orchestrator plan: {orchestrator_plan}")

            # Execute the orchestrator's plan (this will emit the final synthesized response)
            execution_result = execute_orchestrator_response(orchestrator_plan, message, page_content)

            return jsonify(execution_result)
        else:
            # If orchestrator failed, return the error
            return orchestrator_response

#--------------------------------------------------
# AUTHENTICATION ROUTES
#--------------------------------------------------
@app.route('/login')
def login():
    return render_template('dynamic-page.html', user=db.get_user_email(), page_type='login')

@app.route('/processlogin', methods=["POST", "GET"])
def processlogin():
    data     = request.get_json()
    email    = data.get('email')
    password = data.get('password')

    # Validate required fields
    if not email or not password:
        return json.dumps({"success": 0,"error": "Email and password are required"})
    
    # Check if the username and password match
    status = db.authenticate(email=email, password=password)

    # Encrypt email and store it in the session
    session['email'] = db.reversibleEncrypt('encrypt', email) 

    return json.dumps(status)

@app.route('/logout')
def logout():
    # Clear the entire session
    session.clear()
    return redirect('/')


#--------------------------------------------------
# UTILITY ROUTES
#--------------------------------------------------

@app.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

def clean_html_content(html_content):
    """
    Clean HTML content by removing tags and extracting clean text.

    Args:
        html_content (str): Raw HTML content

    Returns:
        str: Clean text content without HTML tags
    """
    if not html_content:
        return ""

    try:
        # Parse HTML with Beautiful Soup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script, style, and other non-content elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Get text and clean it up
        text = soup.get_text()

        # Clean up whitespace and normalize
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        # Remove excessive whitespace
        text = ' '.join(text.split())

        return text
    except Exception as e:
        print(f"Error cleaning HTML content: {e}")
        # Fallback: return original content if cleaning fails
        return html_content


#--------------------------------------------------
# AGENT-TO-AGENT (A2A) PROTOCOL ROUTES
#--------------------------------------------------

@app.route('/api/a2a', methods=['POST'])
def a2a_handler():
    """
    Handle A2A protocol messages from evaluation agent.

    Receives A2A messages, processes them via the chat system,
    and returns A2A-formatted responses.
    """
    try:
        data = request.get_json()

        # Parse A2A message from request
        a2a_message = A2AMessage.from_dict(data)

        print(f"Received A2A message: {a2a_message.action} from {a2a_message.sender}")

        # Handle different A2A actions
        if a2a_message.action == "chat_request":
            # Extract parameters
            message = a2a_message.params.get('message', '')
            page_context = a2a_message.params.get('page_context', {})

            # Create LLM client
            gemini = GeminiClient()

            # Build system prompt
            if page_context and page_context.get('content'):
                clean_content = clean_html_content(page_context.get('content', ''))
                system_prompt = f"""
                    You are a helpful AI assistant. You have access to the current page content that the user is viewing.
                    IMPORTANT INSTRUCTIONS:
                    1. If the user's question is related to the content on the current page, use that content to provide accurate and relevant answers.
                    2. Reference specific information from the page when it helps answer the user's question.
                    3. If the user asks about something not covered on the current page, provide general helpful information.
                    4. Be conversational and helpful while maintaining accuracy.

                    CURRENT PAGE CONTENT:
                    Title:   {page_context.get('title', 'Unknown page')}
                    URL:     {page_context.get('url', 'N/A')}
                    Content: {clean_content}

                    Use this content to provide contextually relevant responses when appropriate.
                """
            else:
                system_prompt = "You are a helpful AI assistant."

            # Get AI response
            ai_result = chatGPT.send_message(
                message=message,
                conversation_history=[],
                system_prompt=system_prompt
            )

            agent_response = ai_result.get('response', 'Error processing request')

            # Send A2A response back
            response_message = a2a_protocol.send_response(
                message_id=a2a_message.message_id,
                sender="chat_agent",
                recipient=a2a_message.sender,
                result=agent_response
            )

            return jsonify(response_message.to_dict())

        else:
            # Unknown action
            error_response = a2a_protocol.send_response(
                message_id=a2a_message.message_id,
                sender="chat_agent",
                recipient=a2a_message.sender,
                result=None,
                error=f"Unknown action: {a2a_message.action}"
            )
            return jsonify(error_response.to_dict()), 400

    except Exception as e:
        print(f"Error in A2A handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


#--------------------------------------------------
# BENCHMARK ROUTES
#--------------------------------------------------

@app.route('/benchmark')
def benchmark_dashboard():
    """Render the benchmark dashboard page."""
    return render_template('dynamic-page.html', user=db.get_user_email(), page_type='benchmark')


@app.route('/api/benchmark/run', methods=['POST'])
def run_benchmark():
    """
    Run benchmark suite via API.

    Accepts JSON with optional 'category' parameter to filter tests.
    """
    try:
        data = request.get_json() or {}
        category = data.get('category')

        print(f"\n{'='*60}")
        print(f"API Request: Running Benchmark Suite")
        print(f"Category Filter: {category if category else 'All'}")
        print(f"{'='*60}\n")

        # Run benchmark suite synchronously
        # In production, this should be async/background job
        result = run_benchmark_sync(category=category)

        return jsonify(result)

    except Exception as e:
        print(f"Error running benchmark: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


def run_benchmark_sync(category=None):
    """
    Synchronous benchmark execution with A2A protocol.

    Args:
        category: Filter test cases by category (optional)

    Returns:
        Dictionary with benchmark results and metrics
    """
    # Load test cases
    test_cases = db.getBenchmarkTestCases(category=category, active_only=True)

    if not test_cases:
        return {
            "success": False,
            "error": "No active test cases found",
            "metrics": db.getBenchmarkMetrics(category=category)
        }

    print(f"Loaded {len(test_cases)} test cases")

    # Run each test
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Testing: {test_case['test_name']}")

        # Prepare test parameters
        test_id = test_case['test_id']
        input_message = test_case['input_message']
        page_context = test_case.get('page_context')

        # Parse page_context if it's a JSON string
        if page_context and isinstance(page_context, str):
            try:
                page_context = json.loads(page_context)
            except json.JSONDecodeError:
                page_context = None

        # Send request via A2A
        import time
        start_time = time.time()

        message_id = a2a_protocol.send_request(
            sender="evaluation_agent",
            recipient="chat_agent",
            action="chat_request",
            params={
                "message": input_message,
                "page_context": page_context
            }
        )

        # Simulate getting response (in real impl, would be async)
        # For synchronous version, directly call chat handler
        gemini = GeminiClient()

        # Build system prompt
        if page_context and page_context.get('content'):
            clean_content = clean_html_content(page_context.get('content', ''))
            system_prompt = f"""
                You are a helpful AI assistant. You have access to the current page content that the user is viewing.
                IMPORTANT INSTRUCTIONS:
                1. If the user's question is related to the content on the current page, use that content to provide accurate and relevant answers.
                2. Reference specific information from the page when it helps answer the user's question.
                3. If the user asks about something not covered on the current page, provide general helpful information.
                4. Be conversational and helpful while maintaining accuracy.

                CURRENT PAGE CONTENT:
                Title:   {page_context.get('title', 'Unknown page')}
                URL:     {page_context.get('url', 'N/A')}
                Content: {clean_content}

                Use this content to provide contextually relevant responses when appropriate.
            """
        else:
            system_prompt = "You are a helpful AI assistant."

        ai_result = chatGPT.send_message(
            message=input_message,
            conversation_history=[],
            system_prompt=system_prompt
        )

        agent_response = ai_result.get('response', 'Error processing request')
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Evaluate response
        passed, error_message = evaluation_agent.evaluate_response(
            actual_response=agent_response,
            expected_response=test_case['expected_output'],
            comparison_type=test_case['expected_output_type']
        )

        # Store result
        result_id = db.storeBenchmarkResult(
            test_id=test_id,
            agent_response=agent_response,
            expected_response=test_case['expected_output'],
            passed=passed,
            execution_time_ms=execution_time_ms,
            error_message=error_message,
            metadata={
                'test_name': test_case['test_name'],
                'comparison_type': test_case['expected_output_type']
            }
        )

        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"    Result: {status} ({execution_time_ms}ms)")
        if error_message:
            print(f"    Error: {error_message}")

        results.append({
            "test_id": test_id,
            "test_name": test_case['test_name'],
            "passed": passed,
            "execution_time_ms": execution_time_ms,
            "error_message": error_message
        })

    # Get final metrics
    metrics = db.getBenchmarkMetrics(category=category)

    print(f"\n{'='*60}")
    print(f"Benchmark Complete")
    print(f"Success Rate: {metrics['success_rate']}%")
    print(f"{'='*60}\n")

    return {
        "success": True,
        "total_tests": len(results),
        "results": results,
        "metrics": metrics
    }


@app.route('/api/benchmark/metrics', methods=['GET'])
def get_benchmark_metrics():
    """Get aggregated benchmark metrics."""
    try:
        category = request.args.get('category')
        metrics = db.getBenchmarkMetrics(category=category)
        return jsonify({"success": True, "metrics": metrics})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/benchmark/results', methods=['GET'])
def get_benchmark_results():
    """Get recent benchmark results."""
    try:
        limit = int(request.args.get('limit', 20))
        results = db.getRecentBenchmarkResults(limit=limit)
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/benchmark/test-cases', methods=['GET'])
def get_test_cases():
    """Get all test cases."""
    try:
        category = request.args.get('category')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        test_cases = db.getBenchmarkTestCases(category=category, active_only=active_only)
        return jsonify({"success": True, "test_cases": test_cases})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
