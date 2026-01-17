# Author: Prof. MM Ghassemi <ghassem3@msu.edu>

#--------------------------------------------------
# Import REQUIREMENTS
#--------------------------------------------------
import os
import time
from flask import Flask
from flask_socketio import SocketIO
from flask_failsafe import failsafe

#--------------------------------------------------
# CONFIGURATION CONSTANTS
#--------------------------------------------------
DB_MAX_RETRIES = 30
DB_RETRY_DELAY = 2

#--------------------------------------------------
# GLOBAL INSTANCES
#--------------------------------------------------
# Use gevent mode for compatibility (gevent is installed)
# Note: For uvicorn ASGI, use async_mode='asyncio' with proper ASGI setup
socketio = SocketIO(async_mode='gevent', cors_allowed_origins="*")

#--------------------------------------------------
# DATABASE INITIALIZATION
#--------------------------------------------------
def initialize_database():
    """
    Initialize database with retry logic and proper error handling.
    
    Returns:
        database: Initialized database instance
        
    Raises:
        Exception: If database connection fails after all retry attempts
    """
    from .utils.database import database
    
    for attempt in range(DB_MAX_RETRIES):
        try:
            db = database()
            print(f"Database connection attempt {attempt + 1}/{DB_MAX_RETRIES}")
            db.createTables(purge=True)
            print("Database tables created successfully")
            print("Database tables and initial data imported successfully")
            return db
        except Exception as e:
            print(f"Database connection failed (attempt {attempt + 1}/{DB_MAX_RETRIES}): {e}")
            if attempt < DB_MAX_RETRIES - 1:
                print(f"Retrying in {DB_RETRY_DELAY} seconds...")
                time.sleep(DB_RETRY_DELAY)
            else:
                print("Failed to connect to database after all retries")
                raise

#--------------------------------------------------
# CONFIGURATION MANAGEMENT
#--------------------------------------------------
def load_configuration(app, debug=False):
    """
    Load and apply application configuration.
    
    Args:
        app: Flask application instance
        debug: Debug mode flag
    """
    try:
        from .config import Config
        app.config.from_object(Config)
        Config.init_app(app)
    except ImportError:
        # Fallback configuration if config.py doesn't exist
        print("Config.py not found, using fallback configuration")
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        app.debug = debug
        app.secret_key = 'dev-fallback-key-change-in-production'

def apply_app_settings(app, debug=False):
    """
    Apply common application settings.
    
    Args:
        app: Flask application instance
        debug: Debug mode flag
    """
    # Prevent issues with cached static files
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.debug = debug
    
    # Secret key is already set by config.py or fallback
    # No need to override it here

#--------------------------------------------------
# APPLICATION FACTORY
#--------------------------------------------------
@failsafe
def create_app(debug=False):
    """
    Create and configure the Flask application.
    
    Args:
        debug: Debug mode flag
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    load_configuration(app, debug)
    
    # Apply application settings
    apply_app_settings(app, debug)

    # Initialize SocketIO
    socketio.init_app(app)

    # Import routes and initialize database within app context
    with app.app_context():
        from . import routes
        
        # Initialize database (now has access to current_app.config)
        try:
            db = initialize_database()
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            raise

        # Register socket events
        from .utils.socket_events import register_socket_events
        register_socket_events(socketio, db)

    # Add context processor for cache-busting
    @app.context_processor
    def cache_buster():
        """Provide cache-busting timestamp for static assets."""
        import time
        return {'cache_buster': int(time.time())}

    # Add request/response middleware
    @app.after_request
    def add_header(r):
        """Add headers to prevent caching issues."""
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        return r

    return app
