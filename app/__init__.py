# app/__init__.py
import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask, jsonify

# Import configuration object
from config import Config

def create_app(config_class=Config):
    """Application Factory Function"""
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration from config.py
    app.config.from_object(config_class)

    # Optional: Load instance config if it exists (e.g., for secrets)
    # app.config.from_pyfile('config.py', silent=True) # Looks in instance/config.py

    # Configure Logging
    # Ensure logs directory exists (handled in config.py now, but good practice)
    log_dir = os.path.dirname(app.config['LOGGING_FILENAME'])
    os.makedirs(log_dir, exist_ok=True)

    # Use RotatingFileHandler for better log management
    file_handler = RotatingFileHandler(
        app.config['LOGGING_FILENAME'],
        maxBytes=10240,  # Max 10KB per file
        backupCount=10   # Keep 10 backup files
    )
    file_handler.setFormatter(logging.Formatter(app.config['LOGGING_FORMAT']))
    file_handler.setLevel(app.config['LOGGING_LEVEL'])

    # Add handler to Flask's logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(app.config['LOGGING_LEVEL'])

    # Also configure root logger if needed (for libraries logging)
    logging.basicConfig(level=app.config['LOGGING_LEVEL'], format=app.config['LOGGING_FORMAT'])


    app.logger.info('CS432 API Startup') # Log app start

    # Register Blueprints
    from .auth.routes import auth_bp
    from .members.routes import members_bp
    from .teams.routes import teams_bp
    # from .events.routes import events_bp 
    # from .matches.routes import matches_bp 
    # from .venues.routes import venues_bp 
    # from .equipment.routes import equipment_bp 

    app.register_blueprint(auth_bp) # No URL prefix, routes like /login
    app.register_blueprint(members_bp) # No URL prefix, routes like /profile/me, /admin/add_member
    app.register_blueprint(teams_bp, url_prefix='/teams')  # Register with a URL prefix
    # app.register_blueprint(events_bp, url_prefix='/events') # Register new
    # app.register_blueprint(matches_bp, url_prefix='/matches') # Register new
    # app.register_blueprint(venues_bp, url_prefix='/venues') # Register new
    # app.register_blueprint(equipment_bp, url_prefix='/equipment') # Register new

    # Simple default route (optional)
    @app.route('/')
    def index():
         return jsonify({"message": "Welcome to the Modular CS432 Group API"})

    return app