from flask import Blueprint, request, render_template
from services.dashboard_service import (
    get_dashboard_data,
    get_team_members_api,
    get_alerts,
    get_summary,
    get_health,
    refresh_data,
    get_member_details,
    export_data
)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

@dashboard_bp.route('/api/dashboard-data')
def api_dashboard_data():
    return get_dashboard_data(request)

@dashboard_bp.route('/api/team-members')
def api_team_members():
    return get_team_members_api()

@dashboard_bp.route('/api/alerts')
def api_alerts():
    return get_alerts()

@dashboard_bp.route('/api/summary')
def api_summary():
    return get_summary()

@dashboard_bp.route('/api/health')
def api_health():
    return get_health()

@dashboard_bp.route('/api/refresh')
def api_refresh():
    return refresh_data()

@dashboard_bp.route('/api/member/<member_name>')
def api_member_details(member_name):
    return get_member_details(member_name)

@dashboard_bp.route('/api/export')
def api_export():
    return export_data()
