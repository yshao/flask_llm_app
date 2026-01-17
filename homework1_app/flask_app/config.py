# Author: Prof. MM Ghassemi <ghassem3@msu.edu>

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """
    Configuration class for the Flask application.
    Centralizes all configuration settings including Flask, database,
    OpenAI API, container, and system configurations.
    """
    
    #--------------------------------------------------
    # FLASK CONFIGURATION
    #--------------------------------------------------
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'AKWNF1231082fksejfOSEHFOISEHF24142124124124124iesfhsoijsopdjf'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 8080))
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    SEND_FILE_MAX_AGE_DEFAULT = int(os.environ.get('SEND_FILE_MAX_AGE_DEFAULT', 0))
    
    #--------------------------------------------------
    # DATABASE CONFIGURATION
    #--------------------------------------------------
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'db')
    DATABASE_HOST = os.environ.get('DATABASE_HOST', 'postgres')
    DATABASE_USER = os.environ.get('DATABASE_USER', 'postgres')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'iamsosecure')
    DATABASE_PORT = int(os.environ.get('DATABASE_PORT', 5432))
    
    #--------------------------------------------------
    # POSTGRESQL CONFIGURATION
    #--------------------------------------------------
    POSTGRES_VERSION = os.environ.get('POSTGRES_VERSION', '13')
    POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))
    
    #--------------------------------------------------
    # GROQ CONFIGURATION
    #--------------------------------------------------
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    GROQ_MODEL = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
    GROQ_MAX_TOKENS = int(os.environ.get('GROQ_MAX_TOKENS', 4000))
    GROQ_MAX_CONVERSATION_HISTORY = int(os.environ.get('GROQ_MAX_CONVERSATION_HISTORY', 1))
    GROQ_TEMPERATURE = float(os.environ.get('GROQ_TEMPERATURE', 0.7))
    GROQ_SYSTEM_PROMPT = os.environ.get('GROQ_SYSTEM_PROMPT', 'You are a helpful AI assistant. Provide clear, concise, and accurate responses.')

    #--------------------------------------------------
    # OPENAI CONFIGURATION (retained for reference)
    #--------------------------------------------------
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_MAX_TOKENS = int(os.environ.get('OPENAI_MAX_TOKENS', 4000))
    OPENAI_MAX_CONVERSATION_HISTORY = int(os.environ.get('OPENAI_MAX_CONVERSATION_HISTORY', 1))
    OPENAI_TEMPERATURE = float(os.environ.get('OPENAI_TEMPERATURE', 0.7))
    OPENAI_SYSTEM_PROMPT = os.environ.get('OPENAI_SYSTEM_PROMPT', 'You are a helpful AI assistant. Provide clear, concise, and accurate responses.')
    
    #--------------------------------------------------
    # ENCRYPTION CONFIGURATION
    #--------------------------------------------------
    ENCRYPTION_ONEWAY_SALT = os.environ.get('ENCRYPTION_ONEWAY_SALT', 'averysaltysailortookalongwalkoffashortbridge')
    ENCRYPTION_ONEWAY_N = int(os.environ.get('ENCRYPTION_ONEWAY_N', 32))  # pow(2,5) = 32
    ENCRYPTION_ONEWAY_R = int(os.environ.get('ENCRYPTION_ONEWAY_R', 9))
    ENCRYPTION_ONEWAY_P = int(os.environ.get('ENCRYPTION_ONEWAY_P', 1))
    ENCRYPTION_REVERSIBLE_KEY = os.environ.get('ENCRYPTION_REVERSIBLE_KEY', '7pK_fnSKIjZKuv_Gwc--sZEMKn2zc8VvD6zS96XcNHE=')
    
    #--------------------------------------------------
    # CONTAINER CONFIGURATION
    #--------------------------------------------------
    POSTGRES_CONTAINER = os.environ.get('POSTGRES_CONTAINER', 'homework-postgres')
    FLASK_CONTAINER = os.environ.get('FLASK_CONTAINER', 'homework-flask-app')
    DB_INIT_CONTAINER = os.environ.get('DB_INIT_CONTAINER', 'homework-db-init')
    
    #--------------------------------------------------
    # SYSTEM CONFIGURATION
    #--------------------------------------------------
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
