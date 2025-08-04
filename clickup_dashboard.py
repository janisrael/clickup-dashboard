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
import numpy as np
import pandas as pd
import warnings
from datetime import date as date_type 

# Suppress warnings
warnings.filterwarnings('ignore', message='Glyph .* missing from font.*')

TIMEZONE = pytz.timezone('America/Edmonton') 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin123'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ClickUp Configuration - Using the accurate API token from first script
API_TOKEN = os.getenv('CLICKUP_API_TOKEN', 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K')
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

# Use original accurate analysis - no member filtering
TARGET_MEMBERS = None  # Set to None to analyze all members like the original script

def get_current_date():
    """Get current date"""
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
    if not date_str:
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
    date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Increment until we find a weekday (0-4 = Monday-Friday)
    while True:
        date += timedelta(days=1)
        if date.weekday() < 5:  # 0-4 = Monday-Friday
            return date.strftime("%Y-%m-%d")

@rate_limit(max_calls_per_minute=25)
def make_clickup_request(url, method='GET', data=None, max_retries=3):
    """Make rate-limited requests to ClickUp API with proper error handling"""
    for attempt in range(max_retries):
        try:
            if method == 'GET':
                response = requests.get(url, headers=HEADERS)
            elif method == 'POST':
                response = requests.post(url, headers=HEADERS, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=HEADERS, json=data)
            
            # Handle 404 errors gracefully
            if response.status_code == 404:
                logger.warning(f"Resource not found (404): {url}")
                return None
                
            if response.status_code == 429:
                wait_time = 60
                logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ClickUp API request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(30)
    
    logger.error("Failed to fetch data after all retries")
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
    """Get all open tasks for a team member - using original accurate method"""
    url = f"{BASE_URL}/team/{team_id}/task?assignees[]={member_id}&include_closed=false"
    data = make_clickup_request(url, max_retries=max_retries)
    return data.get('tasks', []) if data else []

def is_task_in_progress(task):
    """Check if a task is currently in 'in progress' status - using original accurate method"""
    status = task.get('status', {})
    if not status:
        return False
    
    status_name = status.get('status', '').lower()
    
    # Using the exact keywords from the original accurate script
    progress_keywords = [
        'progress', 'in progress', 'in-progress', 'inprogress',
        'active', 'working', 'doing', 'current', 'ongoing',
        'started', 'development', 'dev', 'implementing',
        'in dev', 'in development'
    ]
    
    return any(keyword in status_name for keyword in progress_keywords)

def get_today_timestamps():
    """Get start and end timestamps for today - from original script"""
    now = datetime.now(TIMEZONE)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Convert to ClickUp timestamps (milliseconds)
    start_ts = int(start_of_day.timestamp() * 1000)
    current_ts = int(now.timestamp() * 1000)
    
    return start_ts, current_ts, start_of_day, now

def get_task_activity_today(task_id, today_start):
    """Get task activity for today only - from original accurate script"""
    try:
        url = f"{BASE_URL}/task/{task_id}/activity"
        data = make_clickup_request(url)
        
        if not data or 'activity' not in data:
            return []
            
        all_activity = data['activity']
        
        # Filter for today's activity only
        today_activity = []
        for activity in all_activity:
            activity_timestamp = activity.get('date')
            if activity_timestamp:
                try:
                    activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
                    if activity_time.date() == today_start.date():
                        today_activity.append(activity)
                except (ValueError, TypeError):
                    continue
        
        return today_activity
        
    except Exception as e:
        logger.error(f"Error getting activity for task {task_id}: {e}")
        return []

def find_in_progress_periods_today(tasks, today_start, current_time):
    """Find all periods when user had in-progress tasks today - using original accurate method"""
    in_progress_periods = []
    
    logger.info(f"Analyzing {len(tasks)} tasks for in-progress periods...")
    
    # Check current status first - exactly like original
    currently_in_progress = []
    for task in tasks:
        if is_task_in_progress(task):
            currently_in_progress.append(task)
            logger.debug(f"Currently in progress: {task['name'][:50]}")
    
    # If tasks are currently in progress, find when they started - exactly like original
    for task in currently_in_progress:
        try:
            task_updated = datetime.fromtimestamp(int(task.get('date_updated', 0)) / 1000)
            
            # If task was updated today, use that as start time
            if task_updated.date() == current_time.date():
                period_start = task_updated
            else:
                # Task was already in progress from start of day
                period_start = today_start.replace(hour=9)  # Assume 9 AM work start
            
            duration_delta = current_time - period_start
            in_progress_periods.append({
                'start': period_start,
                'end': current_time,
                'task_name': task['name'],
                'duration_hours': duration_delta.total_seconds() / 3600
            })
        except (ValueError, TypeError) as e:
            logger.warning(f"Error processing task {task.get('id', 'unknown')}: {e}")
            continue
    
    # Also check activity for status changes today (sample first 10 tasks to avoid rate limits)
    for task in tasks[:10]:
        logger.debug(f"Checking activity for: {task['name'][:40]}...")
        activity = get_task_activity_today(task['id'], today_start)
        
        # Look for status changes to "in progress" today - exactly like original
        for activity_item in activity:
            try:
                comment = activity_item.get('comment', '').lower()
                activity_timestamp = activity_item.get('date')
                
                if activity_timestamp and 'status' in comment:
                    activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
                    
                    # Check if status changed TO in-progress
                    if any(keyword in comment for keyword in ['progress', 'development', 'active', 'working']):
                        if 'to' in comment:
                            # Find when this in-progress period ended (or is still ongoing)
                            period_end = current_time
                            
                            # Look for later status changes
                            for later_activity in activity:
                                later_timestamp = later_activity.get('date')
                                if later_timestamp and int(later_timestamp) > int(activity_timestamp):
                                    later_time = datetime.fromtimestamp(int(later_timestamp) / 1000)
                                    later_comment = later_activity.get('comment', '').lower()
                                    
                                    if 'status' in later_comment and 'to' in later_comment:
                                        # Check if it changed away from in-progress
                                        if not any(keyword in later_comment for keyword in ['progress', 'development', 'active', 'working']):
                                            period_end = later_time
                                            break
                            
                            duration_delta = period_end - activity_time
                            duration = duration_delta.total_seconds() / 3600
                            if duration > 0.1:  # At least 6 minutes
                                in_progress_periods.append({
                                    'start': activity_time,
                                    'end': period_end,
                                    'task_name': task['name'],
                                    'duration_hours': duration
                                })
                                
                                logger.debug(f"Found period: {activity_time.strftime('%H:%M')} - "
                                          f"{period_end.strftime('%H:%M')} ({duration:.1f}h)")
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing activity item: {e}")
                continue
        
        time.sleep(1)  # Rate limit prevention
    
    # Sort and merge overlapping periods - exactly like original
    in_progress_periods.sort(key=lambda x: x['start'])
    merged_periods = []
    
    for period in in_progress_periods:
        if not merged_periods:
            merged_periods.append(period)
        else:
            last_period = merged_periods[-1]
            # If periods overlap or are close together (within 30 minutes)
            if period['start'] <= last_period['end'] + timedelta(minutes=30):
                # Merge periods
                last_period['end'] = max(last_period['end'], period['end'])
                duration_delta = last_period['end'] - last_period['start']
                last_period['duration_hours'] = duration_delta.total_seconds() / 3600
                if period['task_name'] not in last_period['task_name']:
                    last_period['task_name'] += f", {period['task_name']}"
            else:
                merged_periods.append(period)
    
    return merged_periods

def calculate_downtime_today(member_name, in_progress_periods, today_start, current_time):
    """Calculate downtime periods of 3+ hours for today - using original accurate method"""
    logger.debug(f"Calculating downtime for {member_name}...")
    
    workday_start = today_start.replace(hour=9, minute=0, second=0, microsecond=0)  # 9 AM
    downtime_periods = []
    
    if not in_progress_periods:
        # No in-progress periods at all today
        if current_time > workday_start:
            duration_delta = current_time - workday_start
            hours_inactive = duration_delta.total_seconds() / 3600
            if hours_inactive >= 3:
                downtime_periods.append({
                    'start': workday_start,
                    'end': current_time,
                    'duration_hours': hours_inactive,
                    'type': 'no_activity_all_day'
                })
                logger.debug(f"No activity all day: {hours_inactive:.1f} hours")
    else:
        # Check gap from workday start to first activity
        first_activity = in_progress_periods[0]['start']
        if first_activity > workday_start:
            gap_delta = first_activity - workday_start
            gap_hours = gap_delta.total_seconds() / 3600
            if gap_hours >= 3:
                downtime_periods.append({
                    'start': workday_start,
                    'end': first_activity,
                    'duration_hours': gap_hours,
                    'type': 'late_start'
                })
                logger.debug(f"Late start: {gap_hours:.1f} hours")
        
        # Check gaps between activities
        for i in range(len(in_progress_periods) - 1):
            gap_start = in_progress_periods[i]['end']
            gap_end = in_progress_periods[i + 1]['start']
            gap_delta = gap_end - gap_start
            gap_hours = gap_delta.total_seconds() / 3600
            
            if gap_hours >= 3:
                downtime_periods.append({
                    'start': gap_start,
                    'end': gap_end,
                    'duration_hours': gap_hours,
                    'type': 'midday_gap'
                })
                logger.debug(f"Midday gap: {gap_hours:.1f} hours")
        
        # Check gap from last activity to now
        last_activity = in_progress_periods[-1]['end']
        current_gap_delta = current_time - last_activity
        current_gap_hours = current_gap_delta.total_seconds() / 3600
        if current_gap_hours >= 3:
            downtime_periods.append({
                'start': last_activity,
                'end': current_time,
                'duration_hours': current_gap_hours,
                'type': 'current_inactive'
            })
            logger.debug(f"CURRENTLY INACTIVE: {current_gap_hours:.1f} hours since last activity")
    
    return downtime_periods

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
            try:
                date_closed = datetime.fromtimestamp(int(task.get('date_closed', 0)) / 1000)
                if date_closed.date() == date_filter:
                    task_metrics['tasks_completed_today'] += 1
            except (ValueError, TypeError):
                pass
        
        # Tasks created today
        try:
            date_created = datetime.fromtimestamp(int(task.get('date_created', 0)) / 1000)
            if date_created.date() == date_filter:
                task_metrics['tasks_created_today'] += 1
        except (ValueError, TypeError):
            pass
    
    # Calculate averages
    if task_metrics['total_tasks'] > 0:
        task_metrics['avg_task_age'] = round(total_age / task_metrics['total_tasks'], 1)
    
    task_metrics['oldest_task'] = oldest_task
    
    return task_metrics

def analyze_team_performance():
    """Main function to analyze team performance - using original accurate algorithm"""
    logger.info("Starting comprehensive team performance analysis...")
    
    try:
        team_id = get_team_id()
        if not team_id:
            logger.error("Could not get team ID")
            return None
            
        members = get_team_members(team_id)
        if not members:
            logger.error("Could not get team members")
            return None
        
        # Get today's timestamps - using original method
        start_ts, current_ts, today_start, current_time = get_today_timestamps()
        current_date = current_time.date()
        
        logger.info(f"Monitoring: {current_time.strftime('%A, %B %d, %Y')}")
        logger.info(f"Current time: {current_time.strftime('%H:%M:%S')}")
        logger.info(f"Work day assumption: 9:00 AM - now")
        
        members_with_downtime = []
        members_with_old_tasks = []
        all_member_data = {}
        
        # Analyze each team member with progress tracking - exactly like original
        logger.info(f"Analyzing {len(members)} team members...")
        
        for i, member in enumerate(members):
            user_id = member['user']['id']
            user_name = member['user']['username']
            
            logger.info(f"ANALYZING MEMBER {i+1}/{len(members)}: {user_name}")
            
            try:
                # Get member's tasks - using original method
                logger.info("Fetching tasks...")
                tasks = get_member_tasks(team_id, user_id)
                logger.info(f"Found {len(tasks)} open tasks")
                
                # Analyze task metrics
                task_metrics = analyze_member_tasks(tasks, current_date)
                
                if not tasks:
                    # No tasks = full downtime if it's been 3+ hours since work started - exactly like original
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
                                'downtime_periods': downtime_periods,
                                'task_metrics': task_metrics
                            }
                            logger.info(f"NO TASKS ASSIGNED: {hours_since_work:.1f} hours of downtime")
                        else:
                            all_member_data[user_name] = {
                                'in_progress_periods': [],
                                'downtime_periods': [],
                                'task_metrics': task_metrics
                            }
                            logger.info(f"No tasks but within acceptable range")
                    else:
                        all_member_data[user_name] = {
                            'in_progress_periods': [],
                            'downtime_periods': [],
                            'task_metrics': task_metrics
                        }
                        logger.info(f"Work day hasn't started yet")
                else:
                    # Analyze task activity - using original accurate methods
                    logger.info("Analyzing task activity patterns...")
                    in_progress_periods = find_in_progress_periods_today(tasks, today_start, current_time)
                    logger.info(f"Found {len(in_progress_periods)} active periods today")
                    
                    # Calculate downtime - using original accurate method
                    logger.info("Calculating downtime periods...")
                    downtime_periods = calculate_downtime_today(user_name, in_progress_periods, today_start, current_time)
                    
                    # Convert datetime objects to ISO strings for JSON serialization
                    for period in in_progress_periods:
                        if isinstance(period['start'], datetime):
                            period['start'] = period['start'].isoformat()
                        if isinstance(period['end'], datetime):
                            period['end'] = period['end'].isoformat()
                    
                    for period in downtime_periods:
                        if isinstance(period['start'], datetime):
                            period['start'] = period['start'].isoformat()
                        if isinstance(period['end'], datetime):
                            period['end'] = period['end'].isoformat()
                    
                    all_member_data[user_name] = {
                        'in_progress_periods': in_progress_periods,
                        'downtime_periods': downtime_periods,
                        'task_metrics': task_metrics
                    }
                    
                    if downtime_periods:
                        members_with_downtime.append(user_name)
                        total_downtime = sum(p['duration_hours'] for p in downtime_periods)
                        logger.info(f"DOWNTIME DETECTED: {total_downtime:.1f} total hours")
                        
                        # Show breakdown
                        for j, period in enumerate(downtime_periods, 1):
                            start_time_str = datetime.fromisoformat(period['start']).strftime('%H:%M')
                            end_time_str = datetime.fromisoformat(period['end']).strftime('%H:%M') if period['end'] != current_time.isoformat() else "NOW"
                            logger.info(f"  {j}. {start_time_str} - {end_time_str} ({period['duration_hours']:.1f}h) [{period['type']}]")
                    else:
                        logger.info(f"No significant downtime detected (active day)")
                
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
            
            # Progress indicator
            progress = ((i + 1) / len(members)) * 100
            logger.info(f"Progress: {progress:.0f}% complete")
            
            # Rate limiting between members
            if i < len(members) - 1:
                logger.info("Rate limiting pause...")
                time.sleep(3)
        
        # Calculate team metrics - exactly like original
        total_active_time = sum(
            sum(p['duration_hours'] for p in data['in_progress_periods']) 
            for data in all_member_data.values()
        )
        
        total_downtime_time = sum(
            sum(p['duration_hours'] for p in data['downtime_periods']) 
            for data in all_member_data.values()
        )
        
        # Calculate expected working hours (considering current time)
        current_hour = current_time.hour + current_time.minute/60
        if current_date.weekday() >= 5:  # Weekend
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
        
        # Find currently inactive members - exactly like original
        currently_inactive = []
        for member_name, data in all_member_data.items():
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
            for data in all_member_data.values()
        )
        
        total_milestone_tasks = sum(
            data['task_metrics']['milestone_tasks']
            for data in all_member_data.values()
        )
        
        # Generate comprehensive results - exactly like original but with additional metrics
        results = {
            'timestamp': current_time.isoformat(),
            'date': current_date.strftime('%Y-%m-%d'),
            'analysis_time': current_time.strftime('%H:%M:%S'),
            'day_of_week': current_date.strftime('%A'),
            'is_weekend': current_date.weekday() >= 5,
            'members_analyzed': len(members),
            'members_with_downtime': len(members_with_downtime),
            'downtime_members': members_with_downtime,
            'members_with_old_tasks': members_with_old_tasks,
            'detailed_data': all_member_data,
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
        
        logger.info("=== COMPREHENSIVE DOWNTIME SUMMARY ===")
        logger.info(f"{current_time.strftime('%A, %B %d, %Y')} at {current_time.strftime('%H:%M')}")
        
        if not members_with_downtime:
            logger.info("✅ EXCELLENT! ALL TEAM MEMBERS ARE ACTIVE!")
            logger.info("No one has 3+ hours of downtime today.")
        else:
            logger.info(f"⚠️ ATTENTION REQUIRED: {len(members_with_downtime)} MEMBER(S) WITH SIGNIFICANT DOWNTIME")
            
            # Categorize by severity - exactly like original
            critical_members = []  # 6+ hours
            severe_members = []    # 4-6 hours  
            moderate_members = []  # 3-4 hours
            
            for member_name in members_with_downtime:
                data = all_member_data[member_name]
                total_downtime = sum(p['duration_hours'] for p in data['downtime_periods'])
                
                if total_downtime >= 6:
                    critical_members.append((member_name, total_downtime))
                elif total_downtime >= 4:
                    severe_members.append((member_name, total_downtime))
                else:
                    moderate_members.append((member_name, total_downtime))
            
            # Display by severity
            if critical_members:
                logger.info(f"🚨 CRITICAL (6+ hours downtime): {len(critical_members)} members")
                for member, hours in critical_members:
                    logger.info(f"   {member}: {hours:.1f} hours - IMMEDIATE ACTION REQUIRED")
            
            if severe_members:
                logger.info(f"🔴 SEVERE (4-6 hours downtime): {len(severe_members)} members")
                for member, hours in severe_members:
                    logger.info(f"   {member}: {hours:.1f} hours - ACTION NEEDED")
            
            if moderate_members:
                logger.info(f"🟡 MODERATE (3-4 hours downtime): {len(moderate_members)} members")
                for member, hours in moderate_members:
                    logger.info(f"   {member}: {hours:.1f} hours - MONITOR")
            
            # Show currently inactive members
            if currently_inactive:
                logger.info(f"🔥 CURRENTLY INACTIVE ({len(currently_inactive)} members):")
                for member in currently_inactive:
                    data = all_member_data[member]
                    current_period = None
                    for period in data['downtime_periods']:
                        try:
                            period_end = datetime.fromisoformat(period['end'])
                            if abs((period_end - current_time).total_seconds()) < 300:
                                current_period = period
                                break
                        except (ValueError, TypeError):
                            continue
                    
                    if current_period:
                        try:
                            period_start = datetime.fromisoformat(current_period['start'])
                            inactive_duration = (current_time - period_start).total_seconds() / 3600
                            logger.info(f"    {member}: inactive for {inactive_duration:.1f} hours (since {period_start.strftime('%H:%M')})")
                        except (ValueError, TypeError):
                            logger.info(f"    {member}: currently inactive")
        
        # Final comprehensive statistics - exactly like original
        logger.info(f"📊 TEAM PERFORMANCE METRICS:")
        logger.info(f"    Analysis time: {current_time.strftime('%H:%M')}")
        logger.info(f"    Total members: {len(members)}")
        logger.info(f"    Fully active members: {len(members) - len(members_with_downtime)}")
        logger.info(f"    Members with downtime: {len(members_with_downtime)}")
        
        if currently_inactive:
            logger.info(f"    Currently inactive: {len(currently_inactive)}")
        
        logger.info(f"    Total active hours: {total_active_time:.1f}h")
        logger.info(f"    Total downtime: {total_downtime_time:.1f}h")
        logger.info(f"    Team efficiency: {team_efficiency:.1f}%")
        
        if members_with_downtime:
            avg_downtime = total_downtime_time / len(members_with_downtime)
            logger.info(f"    Avg downtime per affected member: {avg_downtime:.1f}h")
        
        logger.info("Team performance analysis completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Error during team analysis: {e}")
        return None

def update_dashboard_cache():
    """Update the dashboard cache with fresh data"""
    global dashboard_cache, last_update
    
    logger.info("Updating dashboard cache with accurate analysis...")
    data = analyze_team_performance()
    
    if data:
        data['analysis_context'] = get_analysis_context(data)
        dashboard_cache = data
        last_update = datetime.now()
        logger.info("Dashboard cache updated successfully with accurate data")
    else:
        logger.error("Failed to update dashboard cache")

# Flask Routes
@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """API endpoint to get dashboard data with accurate analysis"""
    global dashboard_cache, last_update
    
    # Check if we should force a refresh
    force_refresh = request.args.get('refresh', '').lower() == 'true'

    # If cache is empty or older than 5 minutes, refresh it
    if force_refresh or not dashboard_cache or not last_update or (datetime.now() - last_update).seconds > 300:
        update_dashboard_cache()
    
    # Optional: Filter by date if provided
    requested_date = request.args.get('date')
    if requested_date and dashboard_cache:
        # Implement your date filtering logic here if needed
        pass
    
    if dashboard_cache:
        return jsonify(dashboard_cache)
    else:
        # Return fallback data if real data fails
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
            'error': 'Unable to fetch ClickUp data - using accurate analysis algorithm'
        }
        
        # Add context to fallback data too
        fallback_data['analysis_context'] = get_analysis_context(fallback_data)
        return jsonify(fallback_data)

@app.route('/api/refresh-status')
def refresh_status():
    """Get refresh status"""
    return jsonify({
        'status': 'ready' if dashboard_cache else 'refreshing',
        'last_updated': last_update.isoformat() if last_update else None,
        'algorithm': 'accurate_original_algorithm'
    })

@app.route('/api/refresh')
def refresh_data():
    """Force refresh the dashboard data"""
    logger.info("Manual refresh requested - using accurate analysis")
    update_dashboard_cache()
    return jsonify({
        'status': 'success', 
        'updated_at': last_update.isoformat() if last_update else None,
        'algorithm': 'accurate_original_algorithm'
    })

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
            'algorithm': 'accurate_original_algorithm',
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
                'timestamp': dashboard_cache['timestamp'],
                'algorithm': 'accurate_original_algorithm'
            })
        else:
            return jsonify({'error': f'Member {member_name} not found'}), 404
    else:
        return jsonify({'error': 'No dashboard data available'}), 404

@app.route('/api/alerts')
def get_alerts():
    """Get current alerts using accurate analysis"""
    if not dashboard_cache:
        return jsonify({'alerts': []})
    
    alerts = []
    detailed_data = dashboard_cache.get('detailed_data', {})
    team_metrics = dashboard_cache.get('team_metrics', {})
    
    critical_members = []
    warning_members = []
    
    # Use the same categorization logic as the original accurate script
    for member_name, member_data in detailed_data.items():
        total_downtime = sum(p['duration_hours'] for p in member_data.get('downtime_periods', []))
        
        if total_downtime >= 6:  # Critical - 6+ hours
            critical_members.append(member_name)
        elif total_downtime >= 4:  # Severe - 4-6 hours
            critical_members.append(member_name)
        elif total_downtime >= 3:  # Warning - 3-4 hours
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
    
    # Check for old tasks
    old_tasks = team_metrics.get('total_old_tasks', 0)
    if old_tasks > 10:
        alerts.append({
            'type': 'warning',
            'message': f'📅 TASK MANAGEMENT: {old_tasks} old tasks (7+ days) need attention',
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
    
    return jsonify({
        'alerts': alerts,
        'algorithm': 'accurate_original_algorithm'
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cache_last_updated': last_update.isoformat() if last_update else None,
        'cache_available': bool(dashboard_cache),
        'algorithm': 'accurate_original_algorithm',
        'api_token_configured': bool(API_TOKEN)
    })

@app.route('/api/summary')
def get_summary():
    """Get executive summary of team performance"""
    if not dashboard_cache:
        return jsonify({'error': 'No data available'}), 404
    
    team_metrics = dashboard_cache.get('team_metrics', {})
    detailed_data = dashboard_cache.get('detailed_data', {})
    
    # Calculate summary statistics
    total_members = dashboard_cache.get('members_analyzed', 0)
    members_with_downtime = dashboard_cache.get('members_with_downtime', 0)
    currently_inactive = len(team_metrics.get('currently_inactive', []))
    
    # Categorize members by downtime severity
    critical_count = 0
    severe_count = 0
    moderate_count = 0
    
    for member_data in detailed_data.values():
        total_downtime = sum(p['duration_hours'] for p in member_data.get('downtime_periods', []))
        if total_downtime >= 6:
            critical_count += 1
        elif total_downtime >= 4:
            severe_count += 1
        elif total_downtime >= 3:
            moderate_count += 1
    
    # Generate status
    if critical_count > 0 or currently_inactive > 0:
        status = 'CRITICAL'
        status_color = 'red'
    elif severe_count > 0 or members_with_downtime > total_members * 0.3:
        status = 'WARNING'
        status_color = 'orange'
    elif moderate_count > 0:
        status = 'ATTENTION'
        status_color = 'yellow'
    else:
        status = 'HEALTHY'
        status_color = 'green'
    
    summary = {
        'timestamp': dashboard_cache.get('timestamp'),
        'date': dashboard_cache.get('date'),
        'status': status,
        'status_color': status_color,
        'team_metrics': {
            'total_members': total_members,
            'active_members': total_members - members_with_downtime,
            'members_with_downtime': members_with_downtime,
            'currently_inactive': currently_inactive,
            'team_efficiency': team_metrics.get('team_efficiency', 0),
            'total_active_hours': team_metrics.get('total_active_hours', 0),
            'total_downtime_hours': team_metrics.get('total_downtime_hours', 0)
        },
        'severity_breakdown': {
            'critical': critical_count,  # 6+ hours
            'severe': severe_count,      # 4-6 hours
            'moderate': moderate_count   # 3-4 hours
        },
        'recommendations': []
    }
    
    # Generate recommendations
    if critical_count > 0:
        summary['recommendations'].append('🚨 Immediate intervention required for critical members')
    if currently_inactive > 0:
        summary['recommendations'].append('🔥 Check on currently inactive team members')
    if team_metrics.get('team_efficiency', 100) < 60:
        summary['recommendations'].append('📈 Review team workload and task distribution')
    if team_metrics.get('total_old_tasks', 0) > 5:
        summary['recommendations'].append('📅 Address overdue tasks and project planning')
    
    if not summary['recommendations']:
        summary['recommendations'].append('✅ Team is performing well - maintain current practices')
    
    return jsonify(summary)

# Background task scheduler
def schedule_updates():
    """Schedule background updates"""
    schedule.every(10).minutes.do(update_dashboard_cache)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

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
    logger.info("🚀 Starting ClickUp Enhanced Team Performance API")
    logger.info("Using accurate analysis algorithm from original script")
    logger.info(f"API Token configured: {'Yes' if API_TOKEN else 'No'}")
    logger.info(f"Working hours: {WORKDAY_START_HOUR}:00 - {WORKDAY_END_HOUR}:00")
    
    # Initial cache update with accurate analysis
    logger.info("Performing initial analysis...")
    update_dashboard_cache()
    
    # Start background scheduler in a separate thread
    scheduler_thread = Thread(target=schedule_updates, daemon=True)
    scheduler_thread.start()
    logger.info("Background scheduler started - updates every 10 minutes")
    
    # Run the Flask app
    logger.info("Starting Flask server on http://0.0.0.0:5012")
    app.run(debug=True, host='0.0.0.0', port=5012, use_reloader=False)