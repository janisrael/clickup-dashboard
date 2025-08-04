from flask import Flask, render_template, jsonify, request
import requests
import time
from datetime import datetime, timedelta
import json
import logging
from functools import wraps
import os
from threading import Thread
import schedule

app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin123'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ClickUp Configuration
API_TOKEN = os.getenv('CLICKUP_API_TOKEN', 'pk_99989505_RJXIV1Q62WJZDW5P5J30JDYRGHVF7N6R')
HEADERS = {'Authorization': API_TOKEN}
BASE_URL = 'https://api.clickup.com/api/v2'

# Global cache for dashboard data
dashboard_cache = {}
last_update = None



# Working Time Configuration (put this at the top of your file)
WORKDAY_START_HOUR = 9  # 9:00 AM
WORKDAY_END_HOUR = 17   # 5:00 PM
LUNCH_BREAK_START = 12  # 12:00 PM
LUNCH_BREAK_END = 12.5  # 12:30 PM (represented as 12.5 for calculations)
WORKING_HOURS_PER_DAY = 7.5  # 8 hours minus 30 minute break

# Sample static date configuration (remove for production)
SAMPLE_DATE = "2025-08-02"  # A Monday (not Saturday)
USE_SAMPLE_DATE = True  # Set to False for real dates

TARGET_MEMBERS = ['Arif', 'Jan', 'Wiktor']

def rate_limit(max_calls_per_minute=30):
    """Rate limiting decorator"""
    def decorator(func):
        calls = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [call for call in calls if call > now - 60]
            
            if len(calls) >= max_calls_per_minute:
                time.sleep(60 - (now - calls[0]))
                
            calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(max_calls_per_minute=25)
def make_clickup_request(url, method='GET', data=None):
    """Make rate-limited requests to ClickUp API with proper error handling"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS)
        elif method == 'POST':
            response = requests.post(url, headers=HEADERS, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data)
        
        # Handle 404 errors gracefully (task not found/deleted)
        if response.status_code == 404:
            logger.warning(f"Resource not found (404): {url}")
            return None
            
        if response.status_code == 429:
            logger.warning("Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return make_clickup_request(url, method, data)
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"ClickUp API request failed: {e}")
        return None

def get_team_id():
    """Get the team ID"""
    data = make_clickup_request(f"{BASE_URL}/team")
    if data and 'teams' in data:
        return data['teams'][0]['id']
    return None

def get_team_members(team_id):
    """Get all team members"""
    data = make_clickup_request(f"{BASE_URL}/team")
    if data and 'teams' in data:
        for team in data['teams']:
            if team.get('id') == str(team_id):
                return team.get('members', [])
    return []

def get_member_tasks(team_id, member_id, max_retries=3):
    """Get all open tasks for a team member"""
    url = f"{BASE_URL}/team/{team_id}/task?assignees[]={member_id}&include_closed=false"
    data = make_clickup_request(url)
    return data.get('tasks', []) if data else []

def is_task_in_progress(task):
    """Check if a task is currently in 'in progress' status"""
    status = task.get('status', {})
    if not status:
        return False
    
    status_name = status.get('status', '').lower()
    progress_keywords = [
        'progress', 'in progress', 'in-progress', 'inprogress',
        'active', 'working', 'doing', 'current', 'ongoing',
        'started', 'development', 'dev', 'implementing',
        'in dev', 'in development'
    ]
    
    return any(keyword in status_name for keyword in progress_keywords)

def get_task_activity_today(task_id, today_start):
    """Get task activity for today only with proper error handling"""
    url = f"{BASE_URL}/task/{task_id}/activity"
    data = make_clickup_request(url)
    
    # If the request failed (including 404), return empty list
    if not data:
        logger.debug(f"No activity data available for task {task_id} (may be deleted)")
        return []
    
    if 'activity' not in data:
        logger.debug(f"No activity field in response for task {task_id}")
        return []
    
    today_activity = []
    try:
        for activity in data['activity']:
            activity_timestamp = activity.get('date')
            if activity_timestamp:
                activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
                if activity_time.date() == today_start.date():
                    today_activity.append(activity)
    except (ValueError, TypeError) as e:
        logger.warning(f"Error processing activity timestamps for task {task_id}: {e}")
        return []
    
    return today_activity

def validate_task_exists(task_id):
    """Check if a task still exists before trying to get its activity"""
    url = f"{BASE_URL}/task/{task_id}"
    data = make_clickup_request(url)
    return data is not None

def find_in_progress_periods_today(tasks, today_start, current_time):
    """Find all periods when user had in-progress tasks today"""
    in_progress_periods = []
    
    # Check current status first
    currently_in_progress = []
    for task in tasks:
        if is_task_in_progress(task):
            currently_in_progress.append(task)
    
    # If tasks are currently in progress, we need to find when they started
    for task in currently_in_progress:
        try:
            task_updated = datetime.fromtimestamp(int(task.get('date_updated', 0)) / 1000)
            
            if task_updated.date() == current_time.date():
                period_start = task_updated
            else:
                period_start = today_start.replace(hour=9)  # Assume 9 AM work start
            
            duration_delta = current_time - period_start
            in_progress_periods.append({
                'start': period_start.isoformat(),
                'end': current_time.isoformat(),
                'task_name': task['name'],
                'duration_hours': duration_delta.total_seconds() / 3600
            })
        except (ValueError, TypeError) as e:
            logger.warning(f"Error processing task update time for task {task.get('name', 'Unknown')}: {e}")
            continue
    
    # Check activity for status changes today (sample first 5 tasks to avoid rate limits and errors)
    valid_tasks = []
    for task in tasks[:10]:  # Limit to first 10 tasks
        # Validate task exists before trying to get activity
        if validate_task_exists(task['id']):
            valid_tasks.append(task)
        else:
            logger.debug(f"Skipping deleted/invalid task: {task['id']}")
    
    # Only process first 5 valid tasks to avoid rate limits
    for task in valid_tasks[:5]:
        try:
            activity = get_task_activity_today(task['id'], today_start)
            
            for activity_item in activity:
                try:
                    comment = activity_item.get('comment', '').lower()
                    activity_timestamp = activity_item.get('date')
                    
                    if activity_timestamp and 'status' in comment:
                        activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
                        
                        if any(keyword in comment for keyword in ['progress', 'development', 'active', 'working']):
                            if 'to' in comment:
                                period_end = current_time
                                
                                # Look for later status changes
                                for later_activity in activity:
                                    try:
                                        later_timestamp = later_activity.get('date')
                                        if later_timestamp and int(later_timestamp) > int(activity_timestamp):
                                            later_time = datetime.fromtimestamp(int(later_timestamp) / 1000)
                                            later_comment = later_activity.get('comment', '').lower()
                                            
                                            if 'status' in later_comment and 'to' in later_comment:
                                                if not any(keyword in later_comment for keyword in ['progress', 'development', 'active', 'working']):
                                                    period_end = later_time
                                                    break
                                    except (ValueError, TypeError):
                                        continue
                                
                                duration_delta = period_end - activity_time
                                duration = duration_delta.total_seconds() / 3600
                                if duration > 0.1:  # At least 6 minutes
                                    in_progress_periods.append({
                                        'start': activity_time.isoformat(),
                                        'end': period_end.isoformat(),
                                        'task_name': task['name'],
                                        'duration_hours': duration
                                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing activity item for task {task['name']}: {e}")
                    continue
            
            time.sleep(0.5)  # Rate limit prevention
            
        except Exception as e:
            logger.error(f"Error processing task activity for {task.get('name', 'Unknown')}: {e}")
            continue
    
    # Sort and merge overlapping periods
    in_progress_periods.sort(key=lambda x: x['start'])
    merged_periods = []
    
    for period in in_progress_periods:
        if not merged_periods:
            merged_periods.append(period)
        else:
            try:
                last_period = merged_periods[-1]
                period_start = datetime.fromisoformat(period['start'])
                last_end = datetime.fromisoformat(last_period['end'])
                
                if period_start <= last_end + timedelta(minutes=30):
                    # Merge periods
                    period_end = datetime.fromisoformat(period['end'])
                    last_period['end'] = max(last_end, period_end).isoformat()
                    duration_delta = datetime.fromisoformat(last_period['end']) - datetime.fromisoformat(last_period['start'])
                    last_period['duration_hours'] = duration_delta.total_seconds() / 3600
                    if period['task_name'] not in last_period['task_name']:
                        last_period['task_name'] += f", {period['task_name']}"
                else:
                    merged_periods.append(period)
            except (ValueError, TypeError) as e:
                logger.warning(f"Error merging periods: {e}")
                merged_periods.append(period)
    
    return merged_periods

# def calculate_downtime_today(member_name, in_progress_periods, today_start, current_time):
#     """Calculate downtime periods of 3+ hours for today"""
#     workday_start = today_start.replace(hour=9, minute=0, second=0, microsecond=0)
#     downtime_periods = []
    
#     if not in_progress_periods:
#         if current_time > workday_start:
#             duration_delta = current_time - workday_start
#             hours_inactive = duration_delta.total_seconds() / 3600
#             if hours_inactive >= 3:
#                 downtime_periods.append({
#                     'start': workday_start.isoformat(),
#                     'end': current_time.isoformat(),
#                     'duration_hours': hours_inactive,
#                     'type': 'no_activity_all_day'
#                 })
#     else:
#         try:
#             # Check gap from workday start to first activity
#             first_activity = datetime.fromisoformat(in_progress_periods[0]['start'])
#             if first_activity > workday_start:
#                 gap_delta = first_activity - workday_start
#                 gap_hours = gap_delta.total_seconds() / 3600
#                 if gap_hours >= 3:
#                     downtime_periods.append({
#                         'start': workday_start.isoformat(),
#                         'end': first_activity.isoformat(),
#                         'duration_hours': gap_hours,
#                         'type': 'late_start'
#                     })
            
#             # Check gaps between activities
#             for i in range(len(in_progress_periods) - 1):
#                 gap_start = datetime.fromisoformat(in_progress_periods[i]['end'])
#                 gap_end = datetime.fromisoformat(in_progress_periods[i + 1]['start'])
#                 gap_delta = gap_end - gap_start
#                 gap_hours = gap_delta.total_seconds() / 3600
                
#                 if gap_hours >= 3:
#                     downtime_periods.append({
#                         'start': gap_start.isoformat(),
#                         'end': gap_end.isoformat(),
#                         'duration_hours': gap_hours,
#                         'type': 'midday_gap'
#                     })
            
#             # Check gap from last activity to now
#             last_activity = datetime.fromisoformat(in_progress_periods[-1]['end'])
#             current_gap_delta = current_time - last_activity
#             current_gap_hours = current_gap_delta.total_seconds() / 3600
#             if current_gap_hours >= 3:
#                 downtime_periods.append({
#                     'start': last_activity.isoformat(),
#                     'end': current_time.isoformat(),
#                     'duration_hours': current_gap_hours,
#                     'type': 'current_inactive'
#                 })
#         except (ValueError, TypeError) as e:
#             logger.warning(f"Error calculating downtime for {member_name}: {e}")
    
#     return downtime_periods

def calculate_downtime_today(member_name, in_progress_periods, today_start, current_time):
    """Calculate downtime periods of 3+ hours for today with working hours consideration"""
    # Skip calculation if today is Saturday
    if today_start.weekday() == 5:  # 5 = Saturday
        return []
    
    # Use sample date if configured
    if USE_SAMPLE_DATE:
        try:
            today_start = datetime.strptime(SAMPLE_DATE, "%Y-%m-%d")
            current_time = today_start.replace(hour=current_time.hour, minute=current_time.minute)
        except ValueError:
            pass  # Fall back to real date if sample date is invalid
    
    workday_start = today_start.replace(hour=WORKDAY_START_HOUR, minute=0, second=0, microsecond=0)
    workday_end = today_start.replace(hour=WORKDAY_END_HOUR, minute=0, second=0, microsecond=0)
    lunch_start = today_start.replace(hour=12, minute=0, second=0, microsecond=0)
    lunch_end = today_start.replace(hour=12, minute=30, second=0, microsecond=0)
    
    downtime_periods = []
    
    # Helper function to check if a time is during working hours (excluding lunch)
    def is_working_time(time):
        if time.weekday() == 5:  # Skip Saturday
            return False
        time_hour = time.hour + time.minute/60
        return (
            WORKDAY_START_HOUR <= time_hour < LUNCH_BREAK_START or
            LUNCH_BREAK_END <= time_hour < WORKDAY_END_HOUR
        )
    
    if not in_progress_periods:
        # No activity at all today (only if it's a workday)
        if current_time > workday_start and is_working_time(current_time):
            inactive_start = workday_start
            inactive_end = min(current_time, workday_end)
            
            # Subtract lunch break if applicable
            if inactive_start < lunch_start and inactive_end > lunch_end:
                inactive_duration = (lunch_start - inactive_start).total_seconds() / 3600
                inactive_duration += (inactive_end - lunch_end).total_seconds() / 3600
            else:
                inactive_duration = (inactive_end - inactive_start).total_seconds() / 3600
            
            if inactive_duration >= 3:
                downtime_periods.append({
                    'start': inactive_start.isoformat(),
                    'end': inactive_end.isoformat(),
                    'duration_hours': inactive_duration,
                    'type': 'no_activity_all_day'
                })
    else:
        # Check gaps between activities (considering working hours)
        previous_end = workday_start
        
        for period in sorted(in_progress_periods, key=lambda x: x['start']):
            period_start = datetime.fromisoformat(period['start'])
            period_end = datetime.fromisoformat(period['end'])
            
            # Only consider gaps during working hours (skip weekends)
            if previous_end < period_start and is_working_time(period_start):
                gap_start = max(previous_end, workday_start)
                gap_end = min(period_start, workday_end)
                
                # Handle lunch break in the gap
                if gap_start < lunch_start and gap_end > lunch_end:
                    before_lunch = (lunch_start - gap_start).total_seconds() / 3600
                    after_lunch = (gap_end - lunch_end).total_seconds() / 3600
                    gap_duration = before_lunch + after_lunch
                else:
                    gap_duration = (gap_end - gap_start).total_seconds() / 3600
                
                if gap_duration >= 3:
                    downtime_periods.append({
                        'start': gap_start.isoformat(),
                        'end': gap_end.isoformat(),
                        'duration_hours': gap_duration,
                        'type': 'midday_gap'
                    })
            
            previous_end = period_end
        
        # Check gap from last activity to now (only if it's a workday)
        if previous_end < current_time and is_working_time(current_time):
            gap_start = max(previous_end, workday_start)
            gap_end = min(current_time, workday_end)
            
            # Handle lunch break in the gap
            if gap_start < lunch_start and gap_end > lunch_end:
                before_lunch = (lunch_start - gap_start).total_seconds() / 3600
                after_lunch = (gap_end - lunch_end).total_seconds() / 3600
                gap_duration = before_lunch + after_lunch
            else:
                gap_duration = (gap_end - gap_start).total_seconds() / 3600
            
            if gap_duration >= 3:
                downtime_periods.append({
                    'start': gap_start.isoformat(),
                    'end': gap_end.isoformat(),
                    'duration_hours': gap_duration,
                    'type': 'current_inactive'
                })
    
    return downtime_periods

def analyze_team_performance():
    """Main function to analyze team performance"""
    logger.info("Starting team performance analysis...")
    
    try:
        team_id = get_team_id()
        if not team_id:
            logger.error("Could not get team ID")
            return None
            
        members = get_team_members(team_id)
        if not members:
            logger.error("Could not get team members")
            return None
        
        current_time = datetime.now()
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        all_member_data = {}
        members_with_downtime = []
        
        for i, member in enumerate(members):
            user_id = member['user']['id']
            user_name = member['user']['username']
            
            logger.info(f"Analyzing member {i+1}/{len(members)}: {user_name}")

            # Check if the member is in the target list
            if user_name not in TARGET_MEMBERS:
                continue  # Skip members who are not in the filter
            
            try:
                tasks = get_member_tasks(team_id, user_id)
                
                if not tasks:
                    workday_start = today_start.replace(hour=9)
                    if current_time > workday_start:
                        hours_since_work = (current_time - workday_start).total_seconds() / 3600
                        if hours_since_work >= 3:
                            downtime_periods = [{
                                'start': workday_start.isoformat(),
                                'end': current_time.isoformat(),
                                'duration_hours': hours_since_work,
                                'type': 'no_tasks'
                            }]
                            members_with_downtime.append(user_name)
                            all_member_data[user_name] = {
                                'in_progress_periods': [], 
                                'downtime_periods': downtime_periods
                            }
                        else:
                            all_member_data[user_name] = {
                                'in_progress_periods': [], 
                                'downtime_periods': []
                            }
                    else:
                        all_member_data[user_name] = {
                            'in_progress_periods': [], 
                            'downtime_periods': []
                        }
                else:
                    in_progress_periods = find_in_progress_periods_today(tasks, today_start, current_time)
                    downtime_periods = calculate_downtime_today(user_name, in_progress_periods, today_start, current_time)
                    
                    all_member_data[user_name] = {
                        'in_progress_periods': in_progress_periods,
                        'downtime_periods': downtime_periods
                    }
                    
                    if downtime_periods:
                        members_with_downtime.append(user_name)
                        
            except Exception as e:
                logger.error(f"Error analyzing {user_name}: {e}")
                all_member_data[user_name] = {
                    'in_progress_periods': [], 
                    'downtime_periods': []
                }
            
            # Rate limiting between members
            if i < len(members) - 1:
                time.sleep(2)
        
        # Calculate team metrics (only for target members)
        total_active_time = sum(
            sum(p['duration_hours'] for p in data['in_progress_periods']) 
            for member, data in all_member_data.items()
            if member in TARGET_MEMBERS
        )
        
        total_downtime_time = sum(
            sum(p['duration_hours'] for p in data['downtime_periods']) 
            for member, data in all_member_data.items()
            if member in TARGET_MEMBERS
        )
        
        team_efficiency = 0
        if total_active_time + total_downtime_time > 0:
            team_efficiency = (total_active_time / (total_active_time + total_downtime_time)) * 100
        
        currently_inactive = []
        for member_name, data in all_member_data.items():
            if member_name not in TARGET_MEMBERS:
                continue
                
            for period in data['downtime_periods']:
                try:
                    period_end = datetime.fromisoformat(period['end'])
                    if abs((period_end - current_time).total_seconds()) < 300:  # Within 5 minutes
                        currently_inactive.append(member_name)
                        break
                except (ValueError, TypeError):
                    continue
        
        results = {
            'timestamp': current_time.isoformat(),
            'date': current_time.strftime('%Y-%m-%d'),
            'analysis_time': current_time.strftime('%H:%M:%S'),
            'members_analyzed': len([m for m in members if m['user']['username'] in TARGET_MEMBERS]),
            'members_with_downtime': len(members_with_downtime),
            'downtime_members': members_with_downtime,
            'detailed_data': {k:v for k,v in all_member_data.items() if k in TARGET_MEMBERS},
            'team_metrics': {
                'total_active_hours': round(total_active_time, 1),
                'total_downtime_hours': round(total_downtime_time, 1),
                'team_efficiency': round(team_efficiency, 1),
                'currently_inactive': currently_inactive
            }
        }
        
        logger.info("Team performance analysis completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Error during team analysis: {e}")
        return None

def update_dashboard_cache():
    """Update the dashboard cache with fresh data"""
    global dashboard_cache, last_update
    
    logger.info("Updating dashboard cache...")
    data = analyze_team_performance()
    
    if data:
        dashboard_cache = data
        last_update = datetime.now()
        logger.info("Dashboard cache updated successfully")
    else:
        logger.error("Failed to update dashboard cache")

# Routes
@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """API endpoint to get dashboard data"""
    global dashboard_cache, last_update
    
    # If cache is empty or older than 5 minutes, refresh it
    if not dashboard_cache or not last_update or (datetime.now() - last_update).seconds > 300:
        update_dashboard_cache()
    
    if dashboard_cache:
        return jsonify(dashboard_cache)
    else:
        # Return sample data if real data fails
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'analysis_time': datetime.now().strftime('%H:%M:%S'),
            'members_analyzed': 0,
            'members_with_downtime': 0,
            'downtime_members': [],
            'detailed_data': {},
            'team_metrics': {
                'total_active_hours': 0,
                'total_downtime_hours': 0,
                'team_efficiency': 0,
                'currently_inactive': []
            },
            'error': 'Unable to fetch ClickUp data'
        })

@app.route('/api/refresh-status')
def refresh_status():
    return jsonify({
        'status': 'ready' if is_refresh_complete() else 'refreshing',
        'last_updated': last_update_time.isoformat() if last_update_time else None
    })


@app.route('/api/refresh')
def refresh_data():
    """Force refresh the dashboard data"""
    update_dashboard_cache()
    return jsonify({'status': 'success', 'updated_at': last_update.isoformat() if last_update else None})

@app.route('/api/team-members')
def get_team_members_api():
    """Get list of team members"""
    try:
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
                    }
                    for member in members
                ]
            })
        else:
            return jsonify({'error': 'Could not retrieve team information'}), 500
    except Exception as e:
        logger.error(f"Error getting team members: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export')
def export_data():
    """Export current dashboard data"""
    if dashboard_cache:
        return jsonify({
            'exported_at': datetime.now().isoformat(),
            'data': dashboard_cache
        })
    else:
        return jsonify({'error': 'No data available to export'}), 404

@app.route('/api/member/<member_name>')
def get_member_details(member_name):
    """Get detailed information for a specific member"""
    if dashboard_cache and 'detailed_data' in dashboard_cache:
        member_data = dashboard_cache['detailed_data'].get(member_name)
        if member_data:
            return jsonify({
                'member_name': member_name,
                'data': member_data,
                'timestamp': dashboard_cache['timestamp']
            })
        else:
            return jsonify({'error': f'Member {member_name} not found'}), 404
    else:
        return jsonify({'error': 'No dashboard data available'}), 404

@app.route('/api/alerts')
def get_alerts():
    """Get current alerts"""
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
            'message': f'🚨 CRITICAL: {len(critical_members)} member(s) with 4+ hours downtime: {", ".join(critical_members)}',
            'members': critical_members,
            'priority': 1
        })
    
    currently_inactive = team_metrics.get('currently_inactive', [])
    if currently_inactive:
        alerts.append({
            'type': 'critical',
            'message': f'🔥 IMMEDIATE: {len(currently_inactive)} member(s) currently inactive: {", ".join(currently_inactive)}',
            'members': currently_inactive,
            'priority': 1
        })
    
    total_members = dashboard_cache.get('members_analyzed', 0)
    if warning_members and len(warning_members) > total_members * 0.5:
        alerts.append({
            'type': 'warning',
            'message': '⚠️ TEAM ISSUE: Over 50% of team has significant downtime',
            'members': warning_members,
            'priority': 2
        })
    
    efficiency = team_metrics.get('team_efficiency', 100)
    if efficiency < 50:
        alerts.append({
            'type': 'warning',
            'message': f'📉 PRODUCTIVITY: Team efficiency is {efficiency}%',
            'priority': 2
        })
    
    if not alerts:
        alerts.append({
            'type': 'success',
            'message': '✅ All Clear: No critical issues detected',
            'priority': 3
        })
    
    # Sort by priority (1 = highest)
    alerts.sort(key=lambda x: x.get('priority', 3))
    
    return jsonify({'alerts': alerts})

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cache_last_updated': last_update.isoformat() if last_update else None,
        'cache_available': bool(dashboard_cache)
    })

# Background task scheduler
def schedule_updates():
    """Schedule background updates"""
    schedule.every(15).minutes.do(update_dashboard_cache)
    
    while True:
        schedule.run_pending()
        time.sleep(60 * 15)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Template folder configuration
app.template_folder = 'template'
app.static_folder = 'static'

if __name__ == '__main__':
    # Start background scheduler in a separate thread
    # scheduler_thread = Thread(target=schedule_updates, daemon=True)
    # scheduler_thread.start()
    
    # Initial cache update
    # update_dashboard_cache()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5012, use_reloader=False)