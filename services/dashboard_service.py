# services/dashboard_service.py

from flask import jsonify
from datetime import datetime
import logging
from config import Config
from services.dashboard_logic import analyze_team_performance, get_analysis_context, get_current_date

logger = logging.getLogger(__name__)

# Cache variables
dashboard_cache = {}
last_update = None

def update_dashboard_cache():
    global dashboard_cache, last_update
    logger.info("Updating dashboard cache...")
    data = analyze_team_performance()
    if data:
        data['analysis_context'] = get_analysis_context(data)
        dashboard_cache = data
        last_update = datetime.now()
        logger.info("Dashboard cache updated")
    else:
        logger.error("Failed to update dashboard cache")

def get_dashboard_data(request):
    global dashboard_cache, last_update
    force_refresh = request.args.get('refresh', '').lower() == 'true'
    if force_refresh or not dashboard_cache or not last_update or (datetime.now() - last_update).seconds > 300:
        update_dashboard_cache()
    if dashboard_cache:
        return jsonify(dashboard_cache)
    else:
        fallback_data = {
            'timestamp': datetime.now().isoformat(),
            'date': get_current_date().strftime('%Y-%m-%d'),
            'analysis_time': datetime.now().strftime('%H:%M:%S'),
            'day_of_week': get_current_date().strftime('%A'),
            'is_weekend': get_current_date().weekday() >= 5,
            'members_analyzed': 0,
            'members_with_downtime': 0,
            'downtime_members': [],
            'members_with_old_tasks': [],
            'detailed_data': {},
            'team_metrics': {
                'total_active_hours': 0,
                'total_downtime_hours': 0,
                'expected_working_hours': 0,
                'team_efficiency': 0,
                'currently_inactive': [],
                'total_old_tasks': 0,
                'total_milestone_tasks': 0,
                'workday_progress': 0
            },
            'error': 'Unable to fetch ClickUp data'
        }
        fallback_data['analysis_context'] = get_analysis_context(fallback_data)
        return jsonify(fallback_data)

def get_team_members_api():
    from services.dashboard_logic import get_team_id, get_team_members
    team_id = get_team_id()
    if team_id:
        members = get_team_members(team_id)
        return jsonify({
            'team_id': team_id,
            'members': [
                {
                    'user_id': member['user']['id'],
                    'username': member['user']['username'],
                    'email': member['user']['email']
                } for member in members
            ]
        })
    return jsonify({'error': 'Could not retrieve team information'}), 500

def refresh_data():
    update_dashboard_cache()
    return jsonify({
        'status': 'success',
        'updated_at': last_update.isoformat() if last_update else None
    })

def get_member_details(member_name):
    if dashboard_cache and 'detailed_data' in dashboard_cache:
        member_data = dashboard_cache['detailed_data'].get(member_name)
        if member_data:
            return jsonify({
                'member_name': member_name,
                'data': member_data,
                'timestamp': dashboard_cache['timestamp']
            })
        return jsonify({'error': f'Member {member_name} not found'}), 404
    return jsonify({'error': 'No dashboard data available'}), 404

def export_data():
    if dashboard_cache:
        return jsonify({
            'exported_at': datetime.now().isoformat(),
            'data': dashboard_cache
        })
    return jsonify({'error': 'No data available to export'}), 404

def get_alerts():
    if not dashboard_cache:
        return jsonify({'alerts': []})
    alerts = []
    detailed_data = dashboard_cache.get('detailed_data', {})
    team_metrics = dashboard_cache.get('team_metrics', {})
    critical_members = []
    warning_members = []
    for member_name, member_data in detailed_data.items():
        total_downtime = sum(p['duration_hours'] for p in member_data.get('downtime_periods', []))
        if total_downtime >= 4:
            critical_members.append(member_name)
        elif total_downtime >= 3:
            warning_members.append(member_name)
    if critical_members:
        alerts.append({
            'type': 'critical',
            'message': f'{len(critical_members)} member(s) with 4+ hrs downtime: {", ".join(critical_members)}',
            'members': critical_members
        })
    if warning_members:
        alerts.append({
            'type': 'warning',
            'message': f'{len(warning_members)} member(s) with 3+ hrs downtime: {", ".join(warning_members)}',
            'members': warning_members
        })
    if not alerts:
        alerts.append({
            'type': 'success',
            'message': 'All team members active and within expected productivity'
        })
    return jsonify({'alerts': alerts})

def get_summary():
    if not dashboard_cache:
        return jsonify({'error': 'No data available'}), 404
    tm = dashboard_cache.get('team_metrics', {})
    summary = {
        'timestamp': dashboard_cache.get('timestamp'),
        'status': 'HEALTHY' if tm.get('team_efficiency', 100) >= 60 else 'ATTENTION',
        'team_efficiency': tm.get('team_efficiency', 0),
        'active_hours': tm.get('total_active_hours', 0),
        'downtime_hours': tm.get('total_downtime_hours', 0),
        'currently_inactive': tm.get('currently_inactive', [])
    }
    return jsonify(summary)

def get_health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cache_last_updated': last_update.isoformat() if last_update else None,
        'cache_available': bool(dashboard_cache)
    })
