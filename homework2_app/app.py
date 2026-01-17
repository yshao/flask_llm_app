# Author: Prof. MM Ghassemi <ghassem3@msu.edu>

import os
from dotenv import load_dotenv
import uvicorn
from flask_app import create_app, socketio

# Load environment variables from .env file
load_dotenv()

#--------------------------------------------------
# APPLICATION ENTRY POINT
#--------------------------------------------------
app = create_app(debug=True)

if __name__ == "__main__":
    # Get port and host from environment variables with fallbacks
    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("FLASK_HOST", "0.0.0.0")

    # Run with uvicorn on port 8080
    # Use socketio.asgi_app for proper ASGI support with Flask-SocketIO
    # reload=True for development auto-reload
    # log_level="info" for standard logging
    uvicorn.run(
        socketio.asgi_app,
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )