from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
from functools import lru_cache
import time
import threading

app = Flask(__name__)
app.template_folder = 'template_v1'
app.static_folder = 'static_v1'

# Configuration
CLICKUP_API_KEY = os.getenv('CLICKUP_API_KEY', 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K')
TEAM_ID = os.getenv('CLICKUP_TEAM_ID', '9013605091')
SPACE_ID = os.getenv('CLICKUP_SPACE_ID', '90132462540')

BASE_URL = 'https://api.clickup.com/api/v2'
HEADERS = {'Authorization': CLICKUP_API_KEY, 'Content-Type': 'application/json'}
EDMONTON_TZ = pytz.timezone('America/Edmonton')

# Cache for different dates
data_cache = {}
cache_timestamp = {}

def get_all_list_ids_from_space(space_id):
    """Get all list IDs from the Space (no folders)"""
    list_ids = []
    
    # Get lists directly from the space
    lists_url = f'{BASE_URL}/space/{space_id}/list'
    response = requests.get(lists_url, headers=HEADERS)
    
    if response.status_code == 200:
        lists = response.json().get('lists', [])
        for lst in lists:
            list_ids.append(lst['id'])
    
    return list_ids

def fetch_users_in_team():
    """Fetch all team members"""
    url = f'{BASE_URL}/team'
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        teams = response.json().get('teams', [])
        if teams:
            return teams[0].get('members', [])
    return []

def fetch_user_tasks_from_lists(user_id, list_ids, target_date):
    """Fetch tasks for a specific user from the lists"""
    user_tasks = []
    excluded_statuses = ['complete', 'closed', 'archived', 'cancelled', 'done', 'resolved']
    
    for list_id in list_ids:
        url = f'{BASE_URL}/list/{list_id}/task'
        params = {
            'archived': 'false',
            'subtasks': 'true',
            'include_closed': 'false'
        }
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                for task in tasks:
                    assignee_ids = [a['id'] for a in task.get('assignees', [])]
                    task_status = task.get('status', {}).get('status', '').lower()
                    
                    if user_id in assignee_ids and task_status not in excluded_statuses:
                        user_tasks.append(task)
        except Exception as e:
            print(f"Error fetching list {list_id}: {e}")
            
    return user_tasks

def analyze_task_activity(task, target_date):
    """Analyze task activity and return in-progress periods"""
    in_progress_periods = []
    
    try:
        # Get task history
        history_url = f'{BASE_URL}/task/{task["id"]}/history'
        response = requests.get(history_url, headers=HEADERS)
        
        if response.status_code == 200:
            history = response.json().get('history', [])
            
            # Sort history by date
            history.sort(key=lambda x: int(x.get('date', 0)))
            
            # Track status changes
            for i, change in enumerate(history):
                if change.get('field') == 'status':
                    timestamp = int(change.get('date', 0)) / 1000
                    change_time = datetime.fromtimestamp(timestamp, tz=EDMONTON_TZ)
                    
                    # Check if this is within our target date
                    if change_time.date() == target_date.date():
                        after_value = change.get('after', {}).get('status', '').lower()
                        
                        # Check if changed TO in-progress
                        if any(keyword in after_value for keyword in ['progress', 'development', 'active', 'working']):
                            # Find when it ended
                            end_time = None
                            
                            for j in range(i + 1, len(history)):
                                next_change = history[j]
                                if next_change.get('field') == 'status':
                                    next_timestamp = int(next_change.get('date', 0)) / 1000
                                    next_time = datetime.fromtimestamp(next_timestamp, tz=EDMONTON_TZ)
                                    next_status = next_change.get('after', {}).get('status', '').lower()
                                    
                                    if not any(keyword in next_status for keyword in ['progress', 'development', 'active', 'working']):
                                        end_time = next_time
                                        break
                            
                            if not end_time:
                                end_time = datetime.now(tz=EDMONTON_TZ)
                            
                            duration_hours = (end_time - change_time).total_seconds() / 3600
                            
                            if duration_hours > 0.1:  # At least 6 minutes
                                in_progress_periods.append({
                                    'start': change_time,
                                    'end': end_time,
                                    'task_name': task['name'],
                                    'duration_hours': duration_hours
                                })
    except Exception as e:
        print(f"Error analyzing task {task.get('id')}: {e}")
    
    return in_progress_periods

def calculate_downtime_periods(in_progress_periods, target_date):
    """Calculate downtime periods between active work"""
    downtime_periods = []
    
    if not in_progress_periods:
        return downtime_periods
    
    # Sort by start time
    sorted_periods = sorted(in_progress_periods, key=lambda x: x['start'])
    
    # Define working hours (9 AM - 5 PM Edmonton time)
    work_start = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
    work_end = target_date.replace(hour=17, minute=0, second=0, microsecond=0)
    
    # Check for downtime at start of day
    if sorted_periods[0]['start'] > work_start:
        duration = (sorted_periods[0]['start'] - work_start).total_seconds() / 3600
        if duration > 0.5:  # More than 30 minutes
            downtime_periods.append({
                'start': work_start,
                'end': sorted_periods[0]['start'],
                'duration_hours': duration,
                'type': 'start_of_day'
            })
    
    # Check for gaps between periods
    for i in range(len(sorted_periods) - 1):
        gap_start = sorted_periods[i]['end']
        gap_end = sorted_periods[i + 1]['start']
        duration = (gap_end - gap_start).total_seconds() / 3600
        
        if duration > 0.5:  # More than 30 minutes
            downtime_periods.append({
                'start': gap_start,
                'end': gap_end,
                'duration_hours': duration,
                'type': 'between_tasks'
            })
    
    # Check for downtime at end of day
    last_period_end = sorted_periods[-1]['end']
    if last_period_end < work_end:
        duration = (work_end - last_period_end).total_seconds() / 3600
        if duration > 0.5:  # More than 30 minutes
            downtime_periods.append({
                'start': last_period_end,
                'end': work_end,
                'duration_hours': duration,
                'type': 'end_of_day'
            })
    
    return downtime_periods

def analyze_team_performance(target_date_str):
    """Main analysis function"""
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        target_date = EDMONTON_TZ.localize(target_date)
    except:
        target_date = datetime.now(tz=EDMONTON_TZ)
    
    # Check if weekend
    if target_date.weekday() >= 5:  # Saturday or Sunday
        return {
            'date': target_date_str,
            'is_weekend': True,
            'message': 'Limited analysis available for weekends'
        }
    
    # Fetch team members
    members = fetch_users_in_team()
    
    # Get all lists
    list_ids = get_all_list_ids_from_space(SPACE_ID)
    
    detailed_data = {}
    team_stats = {
        'total_active_hours': 0,
        'total_downtime_hours': 0,
        'members_analyzed': 0,
        'members_with_downtime': 0,
        'currently_inactive': [],
        'downtime_members': []
    }
    
    # Analyze each member
    for member in members:
        user = member.get('user', {})
        user_id = user.get('id')
        username = user.get('username', 'Unknown')
        
        if not user_id:
            continue
        
        # Skip certain users if needed
        if username.lower() in ['bot', 'system', 'test']:
            continue
        
        print(f"Analyzing {username}...")
        
        # Get user's tasks
        tasks = fetch_user_tasks_from_lists(user_id, list_ids, target_date)
        
        # Analyze activity for each task
        all_in_progress_periods = []
        for task in tasks:
            periods = analyze_task_activity(task, target_date)
            all_in_progress_periods.extend(periods)
        
        # Calculate downtime
        downtime_periods = calculate_downtime_periods(all_in_progress_periods, target_date)
        
        # Calculate totals
        total_active_hours = sum(p['duration_hours'] for p in all_in_progress_periods)
        total_downtime_hours = sum(p['duration_hours'] for p in downtime_periods)
        
        # Update team stats
        team_stats['total_active_hours'] += total_active_hours
        team_stats['total_downtime_hours'] += total_downtime_hours
        team_stats['members_analyzed'] += 1
        
        if downtime_periods:
            team_stats['members_with_downtime'] += 1
            
        if total_downtime_hours > 2:  # More than 2 hours downtime
            team_stats['downtime_members'].append(username)
        
        # Check if currently inactive
        now = datetime.now(tz=EDMONTON_TZ)
        if now.hour >= 9 and now.hour < 17:  # During work hours
            is_active = any(
                p['start'] <= now <= p['end'] 
                for p in all_in_progress_periods
            )
            if not is_active:
                team_stats['currently_inactive'].append(username)
        
        # Store detailed data
        detailed_data[username] = {
            'user_id': user_id,
            'total_active_hours': total_active_hours,
            'total_downtime_hours': total_downtime_hours,
            'task_count': len(tasks),
            'in_progress_periods': all_in_progress_periods,
            'downtime_periods': downtime_periods
        }
    
    # Calculate team efficiency
    total_work_hours = team_stats['members_analyzed'] * 8  # 8 hour workday
    team_efficiency = (team_stats['total_active_hours'] / total_work_hours * 100) if total_work_hours > 0 else 0
    
    return {
        'date': target_date_str,
        'timestamp': datetime.now().isoformat(),
        'analysis_time': datetime.now().strftime('%H:%M:%S'),
        'team_metrics': {
            **team_stats,
            'team_efficiency': team_efficiency
        },
        'detailed_data': detailed_data,
        'is_weekend': False
    }

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """API endpoint for dashboard data"""
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Check cache
    if date_str in data_cache:
        cache_age = time.time() - cache_timestamp.get(date_str, 0)
        if cache_age < 600:  # 10 minutes
            return jsonify(data_cache[date_str])
    
    # Perform analysis
    data = analyze_team_performance(date_str)
    
    # Update cache
    data_cache[date_str] = data
    cache_timestamp[date_str] = time.time()
    
    return jsonify(data)

@app.route('/api/alerts')
def get_alerts():
    """Get current alerts"""
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Get data from cache or analyze
    if date_str in data_cache:
        data = data_cache[date_str]
    else:
        data = analyze_team_performance(date_str)
        data_cache[date_str] = data
        cache_timestamp[date_str] = time.time()
    
    alerts = []
    
    # Generate alerts based on data
    if data.get('team_metrics'):
        metrics = data['team_metrics']
        
        # High downtime alert
        if metrics['total_downtime_hours'] > metrics['members_analyzed'] * 2:
            alerts.append({
                'type': 'warning',
                'message': f"High team downtime: {metrics['total_downtime_hours']:.1f} hours total",
                'timestamp': datetime.now().isoformat()
            })
        
        # Currently inactive members
        if metrics.get('currently_inactive'):
            alerts.append({
                'type': 'info',
                'message': f"Currently inactive: {', '.join(metrics['currently_inactive'])}",
                'timestamp': datetime.now().isoformat()
            })
        
        # Low efficiency
        if metrics.get('team_efficiency', 100) < 70:
            alerts.append({
                'type': 'danger',
                'message': f"Low team efficiency: {metrics['team_efficiency']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
    
    return jsonify({'alerts': alerts})

def background_refresh():
    """Background task to refresh data periodically"""
    while True:
        time.sleep(600)  # 10 minutes
        try:
            # Refresh today's data
            today = datetime.now().strftime('%Y-%m-%d')
            data = analyze_team_performance(today)
            data_cache[today] = data
            cache_timestamp[today] = time.time()
            print(f"Background refresh completed at {datetime.now()}")
        except Exception as e:
            print(f"Background refresh error: {e}")

if __name__ == '__main__':
    # Start background refresh thread
    refresh_thread = threading.Thread(target=background_refresh, daemon=True)
    refresh_thread.start()
    
    # Run Flask app
    app.run(debug=True, port=5013)