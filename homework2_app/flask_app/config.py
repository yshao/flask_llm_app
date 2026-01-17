# Author: Prof. MM Ghassemi <ghassem3@msu.edu>
#
# Configuration file for the Flask application.
# All sensitive values should be loaded from environment variables.
# Default values provided are for development only.

import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """
    Configuration class for the Flask application.
    Centralizes all configuration settings including Flask, database,
    OpenAI API, container, and system configurations.
    """

    #==================================================
    # FLASK CONFIGURATION
    #==================================================
    # Secret key for session encryption - should be set via environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

    # Flask environment settings
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 8080))
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')

    # Static file caching
    SEND_FILE_MAX_AGE_DEFAULT = int(os.environ.get('SEND_FILE_MAX_AGE_DEFAULT', 0))

    #==================================================
    # DATABASE CONFIGURATION
    #==================================================
    # PostgreSQL database connection settings
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'db')
    DATABASE_HOST = os.environ.get('DATABASE_HOST', 'postgres')
    DATABASE_USER = os.environ.get('DATABASE_USER', 'postgres')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'changeme')
    DATABASE_PORT = int(os.environ.get('DATABASE_PORT', 5432))

    #==================================================
    # POSTGRESQL CONFIGURATION
    #==================================================
    POSTGRES_VERSION = os.environ.get('POSTGRES_VERSION', '13')
    POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))

    #==================================================
    # GROQ CONFIGURATION
    #==================================================
    # Groq API settings for LLM operations
    # API key should be set via GROQ_API_KEY environment variable
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    GROQ_MODEL = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
    GROQ_MAX_TOKENS = int(os.environ.get('GROQ_MAX_TOKENS', 4000))
    GROQ_MAX_CONVERSATION_HISTORY = int(os.environ.get('GROQ_MAX_CONVERSATION_HISTORY', 1))
    GROQ_TEMPERATURE = float(os.environ.get('GROQ_TEMPERATURE', 0.7))
    GROQ_SYSTEM_PROMPT = os.environ.get('GROQ_SYSTEM_PROMPT', 'You are a helpful AI assistant. Provide clear, concise, and accurate responses.')

    #==================================================
    # OPENAI CONFIGURATION (retained for reference)
    #==================================================
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_MAX_TOKENS = int(os.environ.get('OPENAI_MAX_TOKENS', 4000))
    OPENAI_MAX_CONVERSATION_HISTORY = int(os.environ.get('OPENAI_MAX_CONVERSATION_HISTORY', 1))
    OPENAI_TEMPERATURE = float(os.environ.get('OPENAI_TEMPERATURE', 0.7))
    OPENAI_SYSTEM_PROMPT = os.environ.get('OPENAI_SYSTEM_PROMPT', 'You are a helpful AI assistant. Provide clear, concise, and accurate responses.')

    #==================================================
    # ENCRYPTION CONFIGURATION
    #==================================================
    # Settings for one-way password encryption (scrypt)
    ENCRYPTION_ONEWAY_SALT = os.environ.get('ENCRYPTION_ONEWAY_SALT', 'changeme-salt-value')
    ENCRYPTION_ONEWAY_N = int(os.environ.get('ENCRYPTION_ONEWAY_N', 32))  # pow(2,5) = 32
    ENCRYPTION_ONEWAY_R = int(os.environ.get('ENCRYPTION_ONEWAY_R', 9))
    ENCRYPTION_ONEWAY_P = int(os.environ.get('ENCRYPTION_ONEWAY_P', 1))

    # Settings for reversible encryption (Fernet)
    # Key should be set via environment variable for production
    ENCRYPTION_REVERSIBLE_KEY = os.environ.get('ENCRYPTION_REVERSIBLE_KEY', 'changeme-reversible-key')

    #==================================================
    # CONTAINER CONFIGURATION
    #==================================================
    # Docker container names for orchestration
    POSTGRES_CONTAINER = os.environ.get('POSTGRES_CONTAINER', 'homework-postgres')
    FLASK_CONTAINER = os.environ.get('FLASK_CONTAINER', 'homework-flask-app')
    DB_INIT_CONTAINER = os.environ.get('DB_INIT_CONTAINER', 'homework-db-init')

    #==================================================
    # SYSTEM CONFIGURATION
    #==================================================
    TIMEZONE = os.environ.get('TIMEZONE', 'America/New_York')
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

    @staticmethod
    def init_app(app):
        """
        Initialize configuration with Flask app.

        Args:
            app: Flask application instance to configure
        """
        # Set Flask environment variables
        app.config['ENV'] = Config.FLASK_ENV
        app.config['DEBUG'] = Config.FLASK_DEBUG
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = Config.SEND_FILE_MAX_AGE_DEFAULT

        # Set timezone if available
        if hasattr(Config, 'TIMEZONE'):
            os.environ['TZ'] = Config.TIMEZONE

        #==================================================
        # LOGGING CONFIGURATION
        #==================================================
        # Configure application logging with both file and console handlers
        log_level = logging.DEBUG if Config.FLASK_DEBUG else logging.INFO

        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        # Configure format for detailed logging
        log_format = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File handler with rotation (10MB max, keep 5 backups)
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'app.log'),
            maxBytes=10*1024*1024,
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_format)

        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(log_format)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.handlers.clear()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Set Flask app logger
        app.logger.setLevel(log_level)

        # Silence noisy loggers
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('socketio').setLevel(logging.WARNING)

        app.logger.info("="*60)
        app.logger.info("Application initialized")
        app.logger.info(f"Environment: {Config.ENVIRONMENT}")
        app.logger.info(f"Debug mode: {Config.FLASK_DEBUG}")
        app.logger.info(f"Logging level: {logging.getLevelName(log_level)}")
        app.logger.info(f"Log file: {os.path.join(logs_dir, 'app.log')}")
        app.logger.info("="*60)
