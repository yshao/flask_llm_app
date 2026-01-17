# Author: AI Agent Benchmark System
# Purpose: Agent-to-Agent (A2A) Protocol for structured inter-agent communication
#
# This module provides:
# - A2AMessage class for structured inter-agent messages
# - A2AProtocol class for managing agent communication
# - Request/response lifecycle management
# - Message tracking and history for debugging

import uuid
from typing import Dict, Any, Optional
from datetime import datetime

#==================================================
# A2A MESSAGE CLASS
#==================================================

class A2AMessage:
    """
    Represents a message in the Agent-to-Agent protocol.

    Messages have a unique identifier, sender/recipient information,
    an action to perform, and parameters for that action.
    """

    def __init__(self, sender: str, recipient: str, action: str, params: Dict[str, Any]):
        """
        Initialize an A2A message.

        Args:
            sender: Identifier of the agent sending the message
            recipient: Identifier of the agent receiving the message
            action: The action to perform (e.g., "chat_request", "evaluate", "response")
            params: Dictionary of parameters for the action
        """
        self.message_id = str(uuid.uuid4())
        self.sender = sender
        self.recipient = recipient
        self.action = action
        self.params = params
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            'message_id': self.message_id,
            'sender': self.sender,
            'recipient': self.recipient,
            'action': self.action,
            'params': self.params,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Create message from dictionary."""
        msg = cls(
            sender=data['sender'],
            recipient=data['recipient'],
            action=data['action'],
            params=data['params']
        )
        if 'message_id' in data:
            msg.message_id = data['message_id']
        if 'timestamp' in data:
            msg.timestamp = data['timestamp']
        return msg


#==================================================
# A2A PROTOCOL CLASS
#==================================================

class A2AProtocol:
    """
    Manages Agent-to-Agent protocol communication.

    Tracks pending requests, handles message routing,
    and manages the request/response lifecycle.
    """

    def __init__(self):
        """Initialize the A2A protocol handler."""
        self.pending_requests = {}  # message_id -> A2AMessage
        self.message_history = []   # List of all messages for debugging

    def send_request(
        self,
        sender: str,
        recipient: str,
        action: str,
        params: Dict[str, Any]
    ) -> str:
        """
        Send a request from one agent to another.

        Args:
            sender: Identifier of the agent sending the request
            recipient: Identifier of the agent receiving the request
            action: The action to perform
            params: Parameters for the action

        Returns:
            Message ID for tracking the request
        """
        message = A2AMessage(sender, recipient, action, params)

        # Store as pending until we get a response
        self.pending_requests[message.message_id] = message

        # Track in history for debugging
        self.message_history.append(message)

        return message.message_id

    def send_response(
        self,
        message_id: str,
        sender: str,
        recipient: str,
        result: Any,
        error: Optional[str] = None
    ) -> A2AMessage:
        """
        Send a response to a previous request.

        Args:
            message_id: ID of the original request message
            sender: Identifier of the agent sending the response
            recipient: Identifier of the agent receiving the response
            result: The result of processing the request
            error: Optional error message if request failed

        Returns:
            A2AMessage containing the response
        """
        response_params = {
            'result': result,
            'original_message_id': message_id
        }

        if error:
            response_params['error'] = error
            response_params['success'] = False
        else:
            response_params['success'] = True

        response = A2AMessage(sender, recipient, "response", response_params)

        # Remove the original request from pending
        if message_id in self.pending_requests:
            del self.pending_requests[message_id]

        # Track in history
        self.message_history.append(response)

        return response

    def get_pending_request(self, message_id: str) -> Optional[A2AMessage]:
        """
        Retrieve a pending request by message ID.

        Args:
            message_id: The message ID to look up

        Returns:
            The A2AMessage if found, None otherwise
        """
        return self.pending_requests.get(message_id)

    def get_message_history(self, limit: int = 100) -> list:
        """
        Get recent message history for debugging.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of recent A2AMessage objects
        """
        return self.message_history[-limit:]

    def clear_history(self):
        """Clear message history (useful for testing)."""
        self.message_history = []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get protocol statistics.

        Returns:
            Dictionary with protocol stats
        """
        return {
            'pending_requests': len(self.pending_requests),
            'total_messages': len(self.message_history),
            'pending_message_ids': list(self.pending_requests.keys())
        }
