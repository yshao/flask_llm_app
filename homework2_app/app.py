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
    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("FLASK_HOST", "127.0.0.1")

    # Run with socketio.run() for gevent mode
    # Note: use_reloader must be False for gevent mode compatibility
    # For production, use gunicorn with gevent worker class
    socketio.run(
        app,
        host=host,
        port=port,
        debug=True,
        use_reloader=False,  # gevent mode doesn't support reloader
        log_output=True
    )