# Author: Prof. MM Ghassemi <ghassem3@msu.edu>

import os
from dotenv import load_dotenv
from flask_app import create_app, socketio

# Load environment variables from .env file
load_dotenv()

#--------------------------------------------------
# APPLICATION ENTRY POINT
#--------------------------------------------------
app = create_app(debug=True)

if __name__ == "__main__":
    # Get port and host from environment variables with fallbacks
    port = os.environ.get("PORT", "8080")
    if port == "":
        port = "8080"
    
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    
    # Start the application with SocketIO support and auto-reloader enabled
    # allow_unsafe_werkzeug is needed for development with Flask-SocketIO
    socketio.run(app, host=host, port=int(port), debug=True, use_reloader=True, allow_unsafe_werkzeug=True)