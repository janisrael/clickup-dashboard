from flask import Flask
from blueprints.dashboard_routes import dashboard_bp
from blueprints.monitoring_routes import monitoring_bp
from scheduler import start_scheduler

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Register blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(monitoring_bp)

    # Setup folders
    app.template_folder = 'template'
    app.static_folder = 'static'

    return app

if __name__ == '__main__':
    app = create_app()
    # start_scheduler()
    app.run(debug=True, host='0.0.0.0', port=5015, use_reloader=False)
