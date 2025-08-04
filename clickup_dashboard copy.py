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
import pytz
from datetime import date as date_type 

TIMEZONE = pytz.timezone('America/Edmonton') 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin123'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# jan key pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K
# ClickUp Configuration
API_TOKEN = os.getenv('CLICKUP_API_TOKEN', 'pk_99989505_RJXIV1Q62WJZDW5P5J30JDYRGHVF7N6R') # tricia key
HEADERS = {'Authorization': API_TOKEN}
BASE_URL = 'https://api.clickup.com/api/v2'

# Global cache for dashboard data
dashboard_cache = {}
last_update = None

# Working Time Configuration
WORKDAY_START_HOUR = 9  # 9:00 AM
WORKDAY_END_HOUR = 17   # 5:00 PM
LUNCH_BREAK_START = 12  # 12:00 PM
LUNCH_BREAK_END = 12.5  # 12:30 PM (represented as 12.5 for calculations)
WORKING_HOURS_PER_DAY = 7.5  # 8 hours minus 30 minute break

# Sample static date configuration (remove for production)
SAMPLE_DATE = "2025-07-01"  # A Monday (not Saturday)
USE_SAMPLE_DATE = False  # Set to False for real dates

TARGET_MEMBERS = ['Jan', 'Wiktor']

def get_current_date():
    """Get current date based on configuration"""
    if USE_SAMPLE_DATE:
        try:
            return TIMEZONE.localize(datetime.strptime(SAMPLE_DATE, "%Y-%m-%d")).date()
        except ValueError:
            return datetime.now(TIMEZONE).date()
    return datetime.now(TIMEZONE).date()

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

def get_analysis_context(data):
    """Enhanced to handle both regular and fallback data"""
    try:
        timestamp = data.get('timestamp') or data.get('analysis_time')
        if not timestamp:
            return {'error': 'No timestamp in data'}
            
        analysis_time = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
        current_hour = analysis_time.hour + analysis_time.minute/60
        
        is_weekend = data.get('is_weekend', False)
        is_working_hours = (
            not is_weekend and 
            WORKDAY_START_HOUR <= current_hour < WORKDAY_END_HOUR
        )
        
        return {
            'data_status': 'LIVE',
            'next_expected_update': next_working_day(data.get('date')),
            'current_analysis_time': timestamp,
            'working_hours': f"{WORKDAY_START_HOUR}:00-{WORKDAY_END_HOUR}:00",
            'is_weekend': is_weekend
        }
    except Exception as e:
        logger.error(f"Error generating analysis context: {str(e)}")
        return {'error': 'Could not generate context'}


def next_working_day(date_str):
    """Calculates the next working day (skips weekends)"""
    date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Increment until we find a weekday (0-4 = Monday-Friday)
    while True:
        date += timedelta(days=1)
        if date.weekday() < 5:  # 0-4 = Monday-Friday
            return date.strftime("%Y-%m-%d")

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
    status = task.get('status', {})
    if not status:
        return False
    
    status_name = str(status.get('status', '')).lower()
    status_type = str(status.get('type', '')).lower()
    
    progress_indicators = [
        'progress', 'in progress', 'in-progress', 'inprogress',
        'active', 'working', 'doing', 'current', 'ongoing',
        'started', 'development', 'dev', 'implementing',
        'in dev', 'in development', 'bugs', 'qa',
        'fix', 'review', 'testing', 'custom'
    ]
    
    return any(indicator in status_name for indicator in progress_indicators)


# def is_task_in_progress(task):
#     """Check if a task is currently in 'in progress' status"""
#     status = task.get('status', {})
#     if not status:
#         return False
    
#     status_name = status.get('status', '').lower()
#     status_type = status.get('type', '').lower()
    
#     progress_keywords = [
#         'progress', 'in progress', 'in-progress', 'inprogress',
#         'active', 'working', 'doing', 'current', 'ongoing',
#         'started', 'development', 'dev', 'implementing',
#         'in dev', 'in development', 'wip', 'work in progress',
#         'coding', 'building', 'processing'
#     ]
    
#     # Check both status name and type
#     return (any(keyword in status_name for keyword in progress_keywords) or
#             any(keyword in status_type for keyword in progress_keywords))

def get_task_activity(task_id, date_filter=None):
    """Get task activity with optional date filtering"""
    url = f"{BASE_URL}/task/{task_id}/activity"
    data = make_clickup_request(url)
    
    if not data:
        logger.debug(f"No activity data available for task {task_id}")
        return []
    
    if 'activity' not in data:
        logger.debug(f"No activity field in response for task {task_id}")
        return []
    
    if date_filter:
        filtered_activity = []
        try:
            for activity in data['activity']:
                activity_timestamp = activity.get('date')
                if activity_timestamp:
                    activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
                    if activity_time.date() == date_filter:
                        filtered_activity.append(activity)
            return filtered_activity
        except (ValueError, TypeError) as e:
            logger.warning(f"Error processing activity timestamps for task {task_id}: {e}")
            return []
    
    return data['activity']

def validate_task_exists(task_id):
    """Check if a task still exists before trying to get its activity"""
    url = f"{BASE_URL}/task/{task_id}"
    data = make_clickup_request(url)
    return data is not None

def analyze_task_age(task):
    """Analyze task age and return age category"""
    try:
        date_created = datetime.fromtimestamp(int(task.get('date_created', 0)) / 1000)
        days_old = (datetime.now() - date_created).days
        
        if days_old >= 14:
            return 'very_old', days_old
        elif days_old >= 7:
            return 'old', days_old
        elif days_old >= 3:
            return 'moderate', days_old
        else:
            return 'new', days_old
    except (ValueError, TypeError):
        return 'unknown', 0

def is_milestone_task(task):
    """Check if task is a milestone"""
    try:
        custom_fields = task.get('custom_fields', [])
        for field in custom_fields:
            if field.get('name', '').lower() == 'milestone' and field.get('value'):
                return True
        return False
    except Exception:
        return False


def find_in_progress_periods(tasks, date_filter, current_time):
    """Find all periods when user had in-progress tasks on the specified date."""
    # Proper type checking
    if not isinstance(date_filter, date_type):
        logger.error(f"Invalid date_filter type: {type(date_filter)}. Expected datetime.date")
        return []

    logger.debug(f"Starting analysis for date: {date_filter}")
    
    in_progress_periods = []
    current_time = TIMEZONE.localize(current_time) if current_time.tzinfo is None else current_time.astimezone(TIMEZONE)
    
    # Check current status first
    currently_in_progress = [task for task in tasks if is_task_in_progress(task)]
    logger.info(f"Found {len(currently_in_progress)} in-progress tasks")
    
    for task in currently_in_progress:
        try:
            task_updated = datetime.fromtimestamp(int(task.get('date_updated', 0)) / 1000, TIMEZONE)
            task_created = datetime.fromtimestamp(int(task.get('date_created', 0)) / 1000, TIMEZONE)
            
            # Determine period start - proper date comparison
            if task_updated.date() == date_filter:
                period_start = task_updated
            else:
                workday_start = TIMEZONE.localize(
                    datetime.combine(date_filter, datetime.min.time()).replace(hour=WORKDAY_START_HOUR)
                )
                period_start = workday_start
            
            # Calculate duration
            if current_time > period_start:
                duration = (current_time - period_start).total_seconds() / 3600
                if duration >= 0.1:  # At least 6 minutes
                    in_progress_periods.append({
                        'start': period_start.isoformat(),
                        'end': current_time.isoformat(),
                        'task_name': task['name'],
                        'task_id': task['id'],
                        'duration_hours': round(duration, 2),
                        'status': task.get('status', {}).get('status', '')
                    })

        except Exception as e:
            logger.error(f"Error processing task {task.get('id', 'unknown')}: {str(e)}")
            continue

    # Process historical activity
    for task in tasks[:5]:  # Limit to 5 tasks to avoid rate limits
        try:
            activity = get_task_activity(task['id'], date_filter)
            if not activity:
                continue
                
            # Process activity items
            for item in activity:
                try:
                    comment = item.get('comment', '').lower()
                    if 'status' not in comment:
                        continue
                        
                    if any(kw in comment for kw in ['progress', 'active', 'working']):
                        period = {
                            'start': datetime.fromtimestamp(int(item['date'])/1000, TIMEZONE).isoformat(),
                            'end': current_time.isoformat(),
                            'task_name': task['name'],
                            'task_id': task['id'],
                            'duration_hours': 0,  # Will be calculated
                            'status': task.get('status', {}).get('status', '')
                        }
                        in_progress_periods.append(period)
                except Exception as e:
                    logger.warning(f"Error processing activity: {str(e)}")
                    continue
                    
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            logger.error(f"Error getting activity for task {task.get('id', 'unknown')}: {str(e)}")
            continue

    # Merge overlapping periods
    if not in_progress_periods:
        return []
        
    # Sort by start time
    in_progress_periods.sort(key=lambda x: x['start'])
    
    merged_periods = []
    for period in in_progress_periods:
        if not merged_periods:
            merged_periods.append(period)
        else:
            last = merged_periods[-1]
            last_end = datetime.fromisoformat(last['end'])
            current_start = datetime.fromisoformat(period['start'])
            
            if current_start <= last_end + timedelta(minutes=30):
                # Merge periods
                new_end = max(last_end, datetime.fromisoformat(period['end']))
                last['end'] = new_end.isoformat()
                last['duration_hours'] = round(
                    (new_end - datetime.fromisoformat(last['start'])).total_seconds() / 3600, 
                    2
                )
                last['task_name'] = f"{last['task_name']}, {period['task_name']}"
            else:
                merged_periods.append(period)
    
    return merged_periods

def calculate_downtime(member_name, in_progress_periods, date_filter, current_time):
    """Fixed downtime calculation"""

        # Remove weekend check
    if not in_progress_periods:
        workday_start = TIMEZONE.localize(datetime.combine(date_filter, datetime.min.time()).replace(hour=WORKDAY_START_HOUR))
        inactive_hours = (current_time - workday_start).total_seconds() / 3600
        if inactive_hours >= 1:  # Reduced from 3 hours
            return [{
                'start': workday_start.isoformat(),
                'end': current_time.isoformat(),
                'duration_hours': inactive_hours,
                'type': 'no_activity'
            }]
        return []


    # if date_filter.weekday() >= 5:  # Weekend
    #     return []
    
    # Convert to timezone-aware datetimes
    tz = pytz.timezone('UTC')  # Or your local timezone
    workday_start = tz.localize(datetime.combine(
        date_filter, 
        datetime.min.time()
    ).replace(hour=WORKDAY_START_HOUR))
    
    current_time = tz.localize(current_time)
    
    # Calculate actual working minutes (excluding lunch)
    work_minutes = (WORKDAY_END_HOUR - WORKDAY_START_HOUR) * 60 - 30
    
    # If no activity periods, check if should be marked inactive
    if not in_progress_periods:
        inactive_hours = (current_time - workday_start).total_seconds() / 3600
        if inactive_hours >= 3:
            return [{
                'start': workday_start.isoformat(),
                'end': current_time.isoformat(),
                'duration_hours': inactive_hours,
                'type': 'no_activity'
            }]
        return []
    
    # Sort periods and find gaps
    in_progress_periods.sort(key=lambda x: x['start'])
    downtime_periods = []
    prev_end = workday_start
    
    for period in in_progress_periods:
        period_start = datetime.fromisoformat(period['start']).astimezone(tz)
        period_end = datetime.fromisoformat(period['end']).astimezone(tz)
        
        # Calculate gap between periods
        gap_hours = (period_start - prev_end).total_seconds() / 3600
        
        if gap_hours >= 3:  # Only significant gaps
            downtime_periods.append({
                'start': prev_end.isoformat(),
                'end': period_start.isoformat(),
                'duration_hours': gap_hours,
                'type': 'between_tasks'
            })
        
        prev_end = period_end
    
    # Check gap after last activity
    remaining_hours = (current_time - prev_end).total_seconds() / 3600
    if remaining_hours >= 3:
        downtime_periods.append({
            'start': prev_end.isoformat(),
            'end': current_time.isoformat(),
            'duration_hours': remaining_hours,
            'type': 'current_inactive'
        })
    
    return downtime_periods

def analyze_member_tasks(tasks, date_filter):
    """Analyze member's tasks for productivity metrics"""
    task_metrics = {
        'total_tasks': len(tasks),
        'tasks_in_progress': 0,
        'tasks_completed_today': 0,
        'tasks_created_today': 0,
        'tasks_by_age': {
            'very_old': 0,
            'old': 0,
            'moderate': 0,
            'new': 0
        },
        'milestone_tasks': 0,
        'avg_task_age': 0,
        'oldest_task': None
    }
    
    if not tasks:
        return task_metrics
    
    total_age = 0
    oldest_task = None
    max_age = 0
    
    for task in tasks:
        # Task age analysis
        age_category, days_old = analyze_task_age(task)
        task_metrics['tasks_by_age'][age_category] += 1
        total_age += days_old
        
        if days_old > max_age:
            max_age = days_old
            oldest_task = {
                'name': task.get('name'),
                'id': task.get('id'),
                'age_days': days_old,
                'status': task.get('status', {}).get('status')
            }
        
        # Milestone tasks
        if is_milestone_task(task):
            task_metrics['milestone_tasks'] += 1
        
        # Tasks in progress
        if is_task_in_progress(task):
            task_metrics['tasks_in_progress'] += 1
        
        # Tasks completed today
        status = task.get('status', {})
        if status.get('type') == 'closed':
            date_closed = datetime.fromtimestamp(int(task.get('date_closed', 0)) / 1000)
            if date_closed.date() == date_filter:
                task_metrics['tasks_completed_today'] += 1
        
        # Tasks created today
        date_created = datetime.fromtimestamp(int(task.get('date_created', 0)) / 1000)
        if date_created.date() == date_filter:
            task_metrics['tasks_created_today'] += 1
    
    # Calculate averages
    if task_metrics['total_tasks'] > 0:
        task_metrics['avg_task_age'] = round(total_age / task_metrics['total_tasks'], 1)
    
    task_metrics['oldest_task'] = oldest_task
    
    return task_metrics

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
        
        current_date = get_current_date()
        current_time = datetime.now(TIMEZONE)  # Use timezone-aware datetime
        
        # If using sample date, adjust the current_time to match the sample date
        if USE_SAMPLE_DATE:
            try:
                current_time = TIMEZONE.localize(datetime.combine(
                    current_date, 
                    current_time.time()
                ))
            except ValueError:
                pass
        
        today_start = datetime.combine(current_date, datetime.min.time())
        
        all_member_data = {}
        members_with_downtime = []
        members_with_old_tasks = []
        
        for i, member in enumerate(members):
            user_id = member['user']['id']
            user_name = member['user']['username']
            
            logger.info(f"Analyzing member {i+1}/{len(members)}: {user_name}")

            # Check if the member is in the target list
            if user_name not in TARGET_MEMBERS:
                continue  # Skip members who are not in the filter
            
            try:
                logger.info(f"Fetching tasks for {user_name}...")
                tasks = get_member_tasks(team_id, user_id)
                logger.info(f"Raw tasks from API: {json.dumps(tasks[:2], indent=2)}")  # Log first 2 tasks

                # Check task statuses
                for task in tasks[:5]:  # First 5 tasks
                    logger.info(f"Task {task['id']} status: {task.get('status', {}).get('status')}")
                    
                task_metrics = analyze_member_tasks(tasks, current_date)
                
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
                                'in_progress_periods': in_progress_periods,  # Make sure this isn't being overwritten
                                'downtime_periods': downtime_periods,
                                'task_metrics': task_metrics
                            }
                        else:
                            all_member_data[user_name] = {
                                'in_progress_periods': in_progress_periods,  # Make sure this isn't being overwritten
                                'downtime_periods': downtime_periods,
                                'task_metrics': task_metrics
                            }
                    else:
                        all_member_data[user_name] = {
                            'in_progress_periods': in_progress_periods,  # Make sure this isn't being overwritten
                            'downtime_periods': downtime_periods,
                            'task_metrics': task_metrics
                        }
                else:
                    in_progress_periods = find_in_progress_periods(tasks, current_date, current_time)
                    downtime_periods = calculate_downtime(user_name, in_progress_periods, current_date, current_time)
                    
                    all_member_data[user_name] = {
                        'in_progress_periods': in_progress_periods,  # Make sure this isn't being overwritten
                        'downtime_periods': downtime_periods,
                        'task_metrics': task_metrics
                    }
                    
                    if downtime_periods:
                        members_with_downtime.append(user_name)
                    
                    # Check for old tasks
                    if task_metrics['tasks_by_age']['very_old'] > 0 or task_metrics['tasks_by_age']['old'] > 2:
                        members_with_old_tasks.append(user_name)
                        
            except Exception as e:
                logger.error(f"Error analyzing {user_name}: {e}")
                all_member_data[user_name] = {
                    'in_progress_periods': [], 
                    'downtime_periods': [],
                    'task_metrics': {
                        'total_tasks': 0,
                        'tasks_in_progress': 0,
                        'tasks_completed_today': 0,
                        'tasks_created_today': 0,
                        'tasks_by_age': {
                            'very_old': 0,
                            'old': 0,
                            'moderate': 0,
                            'new': 0
                        },
                        'milestone_tasks': 0,
                        'avg_task_age': 0,
                        'oldest_task': None
                    }
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
        
        # Calculate expected working hours (considering current time)
        current_hour = current_time.hour + current_time.minute/60
        if current_date.weekday() == 5:  # Saturday
            expected_hours = 0
        else:
            if current_hour < WORKDAY_START_HOUR:
                expected_hours = 0
            elif current_hour < LUNCH_BREAK_START:
                expected_hours = current_hour - WORKDAY_START_HOUR
            elif current_hour < LUNCH_BREAK_END:
                expected_hours = LUNCH_BREAK_START - WORKDAY_START_HOUR
            elif current_hour < WORKDAY_END_HOUR:
                expected_hours = (LUNCH_BREAK_START - WORKDAY_START_HOUR) + (current_hour - LUNCH_BREAK_END)
            else:
                expected_hours = WORKING_HOURS_PER_DAY
        
        expected_hours = round(expected_hours, 1)
        
        team_efficiency = 0
        if expected_hours > 0:
            team_efficiency = (total_active_time / (total_active_time + total_downtime_time)) * 100 if (total_active_time + total_downtime_time) > 0 else 0
        
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
        
        # Calculate task age metrics
        total_old_tasks = sum(
            data['task_metrics']['tasks_by_age']['very_old'] + data['task_metrics']['tasks_by_age']['old']
            for member, data in all_member_data.items()
            if member in TARGET_MEMBERS
        )
        
        total_milestone_tasks = sum(
            data['task_metrics']['milestone_tasks']
            for member, data in all_member_data.items()
            if member in TARGET_MEMBERS
        )
        
        results = {
            'timestamp': current_time.isoformat(),
            'date': current_date.strftime('%Y-%m-%d'),
            'analysis_time': current_time.strftime('%H:%M:%S'),
            'day_of_week': current_date.strftime('%A'),
            'is_weekend': current_date.weekday() >= 5,
            'members_analyzed': len([m for m in members if m['user']['username'] in TARGET_MEMBERS]),
            'members_with_downtime': len(members_with_downtime),
            'downtime_members': members_with_downtime,
            'members_with_old_tasks': members_with_old_tasks,
            'detailed_data': {k:v for k,v in all_member_data.items() if k in TARGET_MEMBERS},
            'team_metrics': {
                'total_active_hours': round(total_active_time, 1),
                'total_downtime_hours': round(total_downtime_time, 1),
                'expected_working_hours': expected_hours,
                'team_efficiency': round(team_efficiency, 1),
                'currently_inactive': currently_inactive,
                'total_old_tasks': total_old_tasks,
                'total_milestone_tasks': total_milestone_tasks,
                'workday_progress': round((current_hour - WORKDAY_START_HOUR) / (WORKDAY_END_HOUR - WORKDAY_START_HOUR) * 100, 1) 
                    if not current_date.weekday() >= 5 and WORKDAY_START_HOUR <= current_hour <= WORKDAY_END_HOUR else 0
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
        data['analysis_context'] = get_analysis_context(data)
        dashboard_cache = data
        last_update = datetime.now()
        logger.info("Dashboard cache updated successfully")
    else:
        logger.error("Failed to update dashboard cache")

# Routes (remain the same as in your original code)
@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """API endpoint to get dashboard data"""
    global dashboard_cache, last_update
    
        # Check if we should force a refresh
    force_refresh = request.args.get('refresh', '').lower() == 'true'

    # If cache is empty or older than 5 minutes, refresh it
    if force_refresh or not dashboard_cache or not last_update or (datetime.now() - last_update).seconds > 300:
        update_dashboard_cache()
    
        # Optional: Filter by date if provided
    requested_date = request.args.get('date')
    if requested_date and dashboard_cache:
        # Implement your date filtering logic here
        pass
    
    if dashboard_cache:
        return jsonify(dashboard_cache)
    else:
        # Return sample data if real data fails
        current_time = datetime.now()
        current_date = get_current_date()

        
        fallback_data = {
            'timestamp': current_time.isoformat(),
            'date': current_date.strftime('%Y-%m-%d'),
            'analysis_time': current_time.strftime('%H:%M:%S'),
            'day_of_week': current_date.strftime('%A'),
            'is_weekend': current_date.weekday() >= 5,
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
        
        # Add context to fallback data too
        fallback_data['analysis_context'] = get_analysis_context(fallback_data)
        return jsonify(fallback_data)

@app.route('/api/refresh-status')
def refresh_status():
    return jsonify({
        'status': 'ready' if dashboard_cache else 'refreshing',
        'last_updated': last_update.isoformat() if last_update else None
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
    # Initial cache update
    update_dashboard_cache()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5012, use_reloader=False)