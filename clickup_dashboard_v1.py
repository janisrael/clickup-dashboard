from flask import Flask, render_template, request, jsonify
import logging
import threading
import time
from datetime import datetime
from services.dashboard_service import (
    get_dashboard_data,
    get_team_members_api,
    get_alerts,
    get_summary,
    get_health,
    refresh_data,
    get_member_details,
    export_data,
    update_dashboard_cache
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.template_folder = 'template_v1'
app.static_folder = 'static_v1'

# Dashboard routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """Get dashboard data for a specific date"""
    try:
        return get_dashboard_data(request)
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'error': 'Failed to retrieve dashboard data'}), 500

@app.route('/api/team-members')
def api_team_members():
    """Get team members information"""
    try:
        return get_team_members_api()
    except Exception as e:
        logger.error(f"Error getting team members: {e}")
        return jsonify({'error': 'Failed to retrieve team members'}), 500

@app.route('/api/alerts')
def api_alerts():
    """Get current alerts"""
    try:
        return get_alerts()
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': 'Failed to retrieve alerts'}), 500

@app.route('/api/summary')
def api_summary():
    """Get dashboard summary"""
    try:
        return get_summary()
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({'error': 'Failed to retrieve summary'}), 500

@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    try:
        return get_health()
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """Force refresh dashboard data"""
    try:
        return refresh_data()
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({'error': 'Failed to refresh data'}), 500

@app.route('/api/member/<member_name>')
def api_member_details(member_name):
    """Get detailed information for a specific member"""
    try:
        return get_member_details(member_name)
    except Exception as e:
        logger.error(f"Error getting member details for {member_name}: {e}")
        return jsonify({'error': f'Failed to retrieve details for {member_name}'}), 500

@app.route('/api/export')
def api_export():
    """Export dashboard data"""
    try:
        return export_data()
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({'error': 'Failed to export data'}), 500

# Additional utility endpoints
@app.route('/api/status')
def api_status():
    """Get detailed system status"""
    try:
        status = {
            'timestamp': datetime.now().isoformat(),
            'app_status': 'running',
            'version': '1.0.0',
            'environment': 'production'
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    return jsonify({'error': 'An unexpected error occurred'}), 500

def background_cache_updater():
    """Background task to update cache periodically"""
    while True:
        try:
            logger.info("Running background cache update...")
            update_dashboard_cache()
            logger.info("Background cache update completed")
        except Exception as e:
            logger.error(f"Background cache update failed: {e}")
        
        # Wait 10 minutes before next update
        time.sleep(600)

def start_background_tasks():
    """Start background tasks"""
    # Initial cache update
    try:
        logger.info("Performing initial cache update...")
        update_dashboard_cache()
        logger.info("Initial cache update completed")
    except Exception as e:
        logger.error(f"Initial cache update failed: {e}")
    
    # Start background updater
    background_thread = threading.Thread(target=background_cache_updater, daemon=True)
    background_thread.start()
    logger.info("Background cache updater started")

if __name__ == '__main__':
    logger.info("Starting ClickUp Dashboard Application...")
    
    # Start background tasks
    start_background_tasks()
    
    # Run the Flask application
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5013,
        use_reloader=False  # Disable reloader to prevent duplicate background threads
    )