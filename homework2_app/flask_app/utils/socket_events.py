# Author: Prof. MM Ghassemi <ghassem3@msu.edu>
import time
from flask_socketio import emit, join_room, leave_room

def get_chat_style(role='owner'):
    """Get styling for chat messages based on role."""
    if role == 'owner':
        return 'width: 100%;color:blue;text-align: right'
    elif role == 'ai':
        return 'width: 100%;color:black;text-align: left'
    else:  # guest or any other role
        return 'width: 100%;color:green;text-align: right'

def process_and_emit_message(socketio, message, user_role='guest', room='main'):
    """
    Centralized function to process and emit all chat messages.
    This ensures consistent logging and processing for all message types.
    
    Args:
        socketio: SocketIO instance
        message: The message content
        user_role: User role for styling and frontend type ('ai', 'owner', 'guest', etc.)
        room: Chat room to emit to
    """
    try:
        print(f"""message: from {user_role} to `{room}` room 
        message: {message}""")
        
        # Emit to frontend with both role and style for clarity
        socketio.emit('message', {
            'msg': message,
            'role': user_role,
            'style': get_chat_style(user_role)
        }, room=room, namespace='/chat')
        
    except Exception as e:
        print(f"Error in process_and_emit_message: {str(e)}")
        import traceback
        traceback.print_exc()

def register_socket_events(socketio, db):
    """Register SocketIO event handlers and AI broadcasting."""
    
    #--------------------------------------------------
    # SOCKET EVENT HANDLERS
    #--------------------------------------------------
    
    @socketio.on('joined', namespace='/chat')
    def joined(message={'room': 'main'}):
        """Handle user joining chat room."""
        room = message.get('room', 'main')
        join_room(room)

    @socketio.on('text', namespace='/chat')
    def text(message={'msg': 'Hello', 'room': 'main'}):
        """Handle user text messages in chat."""
        try:
            room = message.get('room', 'main')
            user_email = db.get_user_email()
            user_role = db.get_user_role()
            
            # Use centralized message processing
            process_and_emit_message(socketio, message.get('msg', ''), user_role, room)
        
        except Exception as e:
            print(f"Error in text handler: {str(e)}")
            import traceback
            traceback.print_exc()
