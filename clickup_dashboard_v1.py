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
        logger.info(f"Waiting {3600/60} minutes before next update...")
        time.sleep(3600)

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

@app.route('/api/projects')
def api_projects():
    """Get project data with enhanced timeline information"""
    try:
        # Get existing dashboard data
        dashboard_data = get_dashboard_data_internal()
        
        # Extract and enhance project data
        projects = extract_project_data(dashboard_data)
        
        return jsonify({
            'status': 'success',
            'projects': projects,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return jsonify({'error': 'Failed to retrieve projects'}), 500

def extract_project_data(dashboard_data):
    """Extract project data from dashboard data"""
    projects = []
    project_map = {}
    
    detailed_data = dashboard_data.get('detailed_data', {})
    
    for member_name, member_data in detailed_data.items():
        if 'task_details' in member_data:
            for task in member_data['task_details']:
                project_name = task.get('project_name', 'Unknown Project')
                
                if project_name not in project_map:
                    project_map[project_name] = {
                        'id': project_name.lower().replace(' ', '-'),
                        'name': project_name,
                        'client': extract_client_from_project(project_name),
                        'status': 'active',
                        'startDate': get_project_start_date(task),
                        'deadline': get_project_deadline(task),
                        'assignees': [],
                        'tasks': [],
                        'progress': 0,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                
                project = project_map[project_name]
                
                # Add task to project
                project['tasks'].append({
                    'id': task.get('id', f"task_{len(project['tasks'])}"),
                    'name': task.get('name', 'Unnamed Task'),
                    'status': task.get('status', 'unknown'),
                    'assignee': member_name,
                    'startDate': extract_task_start_date(task, member_data),
                    'dueDate': extract_task_due_date(task),
                    'completed': task.get('status') in ['completed', 'closed'],
                    'priority': task.get('priority', 'normal'),
                    'project_name': project_name,
                    'list_name': task.get('list_name', 'Default List')
                })
                
                # Add assignee if not already present
                if member_name not in project['assignees']:
                    project['assignees'].append(member_name)
    
    # Calculate progress for each project
    for project in project_map.values():
        if project['tasks']:
            completed_tasks = len([t for t in project['tasks'] if t['completed']])
            project['progress'] = (completed_tasks / len(project['tasks'])) * 100
        else:
            project['progress'] = 0
        
        projects.append(project)
    
    return projects

def extract_client_from_project(project_name):
    """Extract client information from project name"""
    # Add your logic to determine client from project name
    client_mapping = {
        'web development': 'TechCorp',
        'ui/ux design': 'StartupXYZ',
        'cms setup': 'Enterprise Ltd',
    }
    return client_mapping.get(project_name.lower(), 'Internal')

def get_project_start_date(task):
    """Get project start date from task data"""
    # Implement logic to extract start date
    return datetime.now().strftime('%Y-%m-%d')

def get_project_deadline(task):
    """Get project deadline from task data"""
    # Implement logic to extract deadline
    return task.get('due_date')

def extract_task_start_date(task, member_data):
    """Extract task start date from periods"""
    periods = member_data.get('in_progress_periods', [])
    for period in periods:
        if period.get('task_id') == task.get('id'):
            return period.get('start', '').split('T')[0]
    return None

def extract_task_due_date(task):
    """Extract task due date"""
    return task.get('due_date')

@app.route('/api/projects/alerts')
def api_project_alerts():
    """Get project-related alerts"""
    try:
        projects_response = api_projects()
        projects_data = projects_response.get_json()
        
        if projects_data.get('status') != 'success':
            return jsonify({'error': 'Failed to load project data'}), 500
        
        projects = projects_data['projects']
        today = datetime.now().date()
        
        overdue_tasks = []
        due_today_tasks = []
        upcoming_tasks = []
        
        for project in projects:
            for task in project['tasks']:
                if task.get('dueDate') and not task['completed']:
                    due_date = datetime.strptime(task['dueDate'], '%Y-%m-%d').date()
                    
                    if due_date < today:
                        overdue_tasks.append({
                            'task': task,
                            'project': project['name'],
                            'days_overdue': (today - due_date).days
                        })
                    elif due_date == today:
                        due_today_tasks.append({
                            'task': task,
                            'project': project['name']
                        })
                    elif due_date <= today + timedelta(days=7):
                        upcoming_tasks.append({
                            'task': task,
                            'project': project['name'],
                            'days_until_due': (due_date - today).days
                        })
        
        return jsonify({
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': overdue_tasks
            },
            'due_today': {
                'count': len(due_today_tasks),
                'tasks': due_today_tasks
            },
            'upcoming': {
                'count': len(upcoming_tasks),
                'tasks': upcoming_tasks
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting project alerts: {e}")
        return jsonify({'error': 'Failed to retrieve project alerts'}), 500

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