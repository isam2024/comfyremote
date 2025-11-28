"""
Main Flask application for RunPod ComfyUI WebUI
Initializes the server, registers blueprints, and manages shared resources
"""
import os
import sys
import logging
from flask import Flask
from flask_cors import CORS

from config import Config
from services import PodManager, SSEBroadcaster, CostCalculator

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Validate configuration
    try:
        Config.validate()
        logger.info(f"Configuration validated: {Config.get_summary()}")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)

    # Initialize shared services
    sse_broadcaster = SSEBroadcaster()
    pod_manager = PodManager(sse_broadcaster=sse_broadcaster)
    cost_calculator = CostCalculator()

    # Store services in app config for access in routes
    app.config['SSE_BROADCASTER'] = sse_broadcaster
    app.config['POD_MANAGER'] = pod_manager
    app.config['COST_CALCULATOR'] = cost_calculator

    # Register blueprints
    from routes import pods_bp, sse_bp, monitoring_bp, health_bp, workflows_bp

    app.register_blueprint(pods_bp)
    app.register_blueprint(sse_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(workflows_bp)

    logger.info("All blueprints registered successfully")

    # Log registered routes
    if Config.DEBUG:
        logger.debug("Registered routes:")
        for rule in app.url_map.iter_rules():
            logger.debug(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")

    return app


def main():
    """Main entry point"""
    app = create_app()

    logger.info(f"Starting RunPod ComfyUI WebUI on {Config.HOST}:{Config.PORT}")
    logger.info(f"Debug mode: {Config.DEBUG}")

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        threaded=True
    )


if __name__ == '__main__':
    main()
