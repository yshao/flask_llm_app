# Author: AI Agent Benchmark System
# Purpose: Evaluation agent for running benchmarks via A2A Protocol
#
# This module provides:
# - Benchmark suite execution via A2A protocol
# - Test case evaluation and comparison
# - Result storage and metrics tracking
# - Response validation against expected outputs

import time
import json
from typing import Dict, Any, List, Optional
from .a2a_protocol import A2AProtocol
from .database import database


#==================================================
# EVALUATION AGENT CLASS
#==================================================

class EvaluationAgent:
    """
    Agent-to-Agent (A2A) based evaluation agent for benchmarking AI agents.

    This agent sends test queries to the chat system via A2A protocol,
    evaluates responses against expected outputs, and stores results
    in the database for metrics tracking.
    """

    def __init__(self, a2a_protocol: A2AProtocol, db: database):
        """
        Initialize the evaluation agent.

        Args:
            a2a_protocol: A2A protocol instance for inter-agent communication
            db: Database instance for storing results
        """
        self.a2a = a2a_protocol
        self.db = db
        self.agent_id = "evaluation_agent"

    def run_benchmark_suite(
        self,
        category: Optional[str] = None,
        target_agent: str = "chat_agent"
    ) -> Dict[str, Any]:
        """
        Run a full benchmark suite and return aggregated metrics.

        Args:
            category: Filter test cases by category (optional)
            target_agent: Identifier of the agent to test (default: "chat_agent")

        Returns:
            Dictionary with suite results and metrics
        """
        print(f"\n{'='*60}")
        print(f"Starting Benchmark Suite")
        print(f"Category: {category if category else 'All'}")
        print(f"Target Agent: {target_agent}")
        print(f"{'='*60}\n")

        # Load test cases from database
        test_cases = self.db.getBenchmarkTestCases(category=category, active_only=True)

        if not test_cases:
            return {
                "success": False,
                "error": "No active test cases found",
                "metrics": self.db.getBenchmarkMetrics(category=category)
            }

        print(f"Loaded {len(test_cases)} test cases\n")

        # Run each test case
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}/{len(test_cases)}] Running: {test_case['test_name']}")

            result = self.run_single_test(test_case, target_agent)
            results.append(result)

            status = "[PASS]" if result['passed'] else "[FAIL]"
            print(f"    Result: {status}")
            if result.get('error_message'):
                print(f"    Error: {result['error_message']}")
            print()

        # Get updated metrics after running tests
        metrics = self.db.getBenchmarkMetrics(category=category)

        print(f"\n{'='*60}")
        print(f"Benchmark Suite Completed")
        print(f"{'='*60}")
        print(f"Total Tests:    {metrics['total_tests']}")
        print(f"Passed:         {metrics['passed_tests']}")
        print(f"Failed:         {metrics['failed_tests']}")
        print(f"Success Rate:   {metrics['success_rate']}%")
        print(f"Avg Time:       {metrics['avg_execution_time_ms']}ms")
        print(f"{'='*60}\n")

        return {
            "success": True,
            "total_tests": len(results),
            "results": results,
            "metrics": metrics
        }

    def run_single_test(
        self,
        test_case: Dict[str, Any],
        target_agent: str = "chat_agent"
    ) -> Dict[str, Any]:
        """
        Execute a single benchmark test case.

        Args:
            test_case: Dictionary containing test case data
            target_agent: Identifier of the agent to test

        Returns:
            Dictionary with test result details
        """
        test_id = test_case['test_id']
        input_message = test_case['input_message']
        expected_output = test_case['expected_output']
        expected_output_type = test_case['expected_output_type']
        page_context = test_case.get('page_context')

        # Parse page_context from JSON string if present
        if page_context and isinstance(page_context, str):
            try:
                page_context = json.loads(page_context)
            except json.JSONDecodeError:
                page_context = None

        # Start timing
        start_time = time.time()

        # Send test query via A2A protocol
        message_id = self.a2a.send_request(
            sender=self.agent_id,
            recipient=target_agent,
            action="chat_request",
            params={
                "message": input_message,
                "page_context": page_context
            }
        )

        # In a real implementation, this would wait for the response asynchronously
        # For this synchronous version, we'll simulate the response retrieval
        # The actual response will be handled by the routes.py A2A handler

        # Note: In production, this would use async/await or message queue
        # For now, we'll handle response synchronously in the routes

        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)

        return {
            "test_id": test_id,
            "test_name": test_case['test_name'],
            "message_id": message_id,
            "execution_time_ms": execution_time_ms,
            "expected_output_type": expected_output_type,
            "expected_output": expected_output,
            "passed": None,  # Will be determined after response
            "error_message": None
        }

    def evaluate_response(
        self,
        actual_response: str,
        expected_response: str,
        comparison_type: str
    ) -> tuple:
        """
        Evaluate an agent response against expected output.

        Args:
            actual_response: The actual response from the agent
            expected_response: The expected response
            comparison_type: Type of comparison ('contains_text', 'exact_match', 'sql_result')

        Returns:
            Tuple of (passed: bool, error_message: str or None)
        """
        try:
            if comparison_type == "contains_text":
                # Case-insensitive substring matching
                passed = expected_response.lower() in actual_response.lower()
                error_msg = None if passed else f"Expected text '{expected_response}' not found in response"
                return (passed, error_msg)

            elif comparison_type == "exact_match":
                # Direct string comparison after normalization
                actual_normalized = actual_response.strip().lower()
                expected_normalized = expected_response.strip().lower()
                passed = actual_normalized == expected_normalized
                error_msg = None if passed else "Response does not match expected output exactly"
                return (passed, error_msg)

            elif comparison_type == "sql_result":
                # For SQL validation, check if response contains valid SQL
                # This is a simplified check - in production, you might execute and validate
                sql_keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE']
                passed = any(keyword in actual_response.upper() for keyword in sql_keywords)
                error_msg = None if passed else "Response does not contain valid SQL query"
                return (passed, error_msg)

            else:
                return (False, f"Unknown comparison type: {comparison_type}")

        except Exception as e:
            return (False, f"Evaluation error: {str(e)}")

    def complete_test_evaluation(
        self,
        test_result: Dict[str, Any],
        agent_response: str
    ) -> Dict[str, Any]:
        """
        Complete test evaluation with agent response and store in database.

        Args:
            test_result: Partial test result from run_single_test
            agent_response: Actual response from the agent

        Returns:
            Updated test result dictionary
        """
        # Evaluate the response
        passed, error_message = self.evaluate_response(
            actual_response=agent_response,
            expected_response=test_result['expected_output'],
            comparison_type=test_result['expected_output_type']
        )

        # Update result
        test_result['passed'] = passed
        test_result['error_message'] = error_message
        test_result['agent_response'] = agent_response

        # Store result in database
        result_id = self.db.storeBenchmarkResult(
            test_id=test_result['test_id'],
            agent_response=agent_response,
            expected_response=test_result['expected_output'],
            passed=passed,
            execution_time_ms=test_result['execution_time_ms'],
            error_message=error_message,
            metadata={
                'test_name': test_result['test_name'],
                'comparison_type': test_result['expected_output_type']
            }
        )

        test_result['result_id'] = result_id

        return test_result

    def get_benchmark_summary(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get benchmark summary statistics.

        Args:
            category: Filter by test category (optional)

        Returns:
            Dictionary with benchmark metrics
        """
        return self.db.getBenchmarkMetrics(category=category)

    def get_recent_results(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent benchmark test results.

        Args:
            limit: Number of recent results to retrieve

        Returns:
            List of result dictionaries
        """
        return self.db.getRecentBenchmarkResults(limit=limit)
