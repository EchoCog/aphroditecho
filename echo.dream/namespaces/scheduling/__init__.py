
"""
Scheduling Namespace
Manages DTE's temporal organization capabilities and project timelines.
"""
import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SchedulingNamespace:
    """Handles temporal organization and project scheduling for DTE."""
    
    def __init__(self):
        self.namespace_path = os.path.dirname(os.path.abspath(__file__))
        self.schedules = {}
        self.calendar = {}
        self.load_schedules()
    
    def load_schedules(self):
        """Load existing schedules."""
        schedules_file = os.path.join(self.namespace_path, 'schedules.json')
        if os.path.exists(schedules_file):
            try:
                with open(schedules_file, 'r') as f:
                    self.schedules = json.load(f)
            except Exception as e:
                logger.error(f"Error loading schedules: {e}")
                self.schedules = {}
                
        calendar_file = os.path.join(self.namespace_path, 'calendar.json')
        if os.path.exists(calendar_file):
            try:
                with open(calendar_file, 'r') as f:
                    self.calendar = json.load(f)
            except Exception as e:
                logger.error(f"Error loading calendar: {e}")
                self.calendar = {}
    
    def create_schedule(self, name, description, duration_days):
        """Create a new schedule template."""
        schedule_id = name.lower().replace(' ', '_')
        
        self.schedules[schedule_id] = {
            'id': schedule_id,
            'name': name,
            'description': description,
            'duration_days': duration_days,
            'milestones': [],
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat()
        }
        
        self._save_schedules()
        return self.schedules[schedule_id]
    
    def add_milestone(self, schedule_id, milestone_name, day_offset, estimated_hours):
        """Add a milestone to a schedule."""
        if schedule_id not in self.schedules:
            return False
        
        milestone = {
            'name': milestone_name,
            'day_offset': day_offset,
            'estimated_hours': estimated_hours,
            'added': datetime.now().isoformat()
        }
        
        self.schedules[schedule_id]['milestones'].append(milestone)
        self.schedules[schedule_id]['modified'] = datetime.now().isoformat()
        
        self._save_schedules()
        return True
    
    def schedule_project(self, project_id, schedule_id, start_date):
        """Schedule a project using a schedule template."""
        if schedule_id not in self.schedules:
            return False
            
        # Convert start_date string to datetime object if needed
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
            
        schedule = self.schedules[schedule_id]
        
        # Create calendar entries for each milestone
        for milestone in schedule['milestones']:
            milestone_date = start_date + timedelta(days=milestone['day_offset'])
            date_key = milestone_date.strftime('%Y-%m-%d')
            
            if date_key not in self.calendar:
                self.calendar[date_key] = []
                
            self.calendar[date_key].append({
                'project_id': project_id,
                'milestone': milestone['name'],
                'hours': milestone['estimated_hours'],
                'scheduled_at': datetime.now().isoformat()
            })
        
        self._save_calendar()
        return True
    
    def get_upcoming_events(self, days=7):
        """Get upcoming scheduled events."""
        today = datetime.now().date()
        upcoming = {}
        
        for i in range(days):
            check_date = today + timedelta(days=i)
            date_key = check_date.strftime('%Y-%m-%d')
            
            if date_key in self.calendar:
                upcoming[date_key] = self.calendar[date_key]
        
        return upcoming
    
    def _save_schedules(self):
        """Save schedules to disk."""
        schedules_file = os.path.join(self.namespace_path, 'schedules.json')
        try:
            with open(schedules_file, 'w') as f:
                json.dump(self.schedules, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving schedules: {e}")
    
    def _save_calendar(self):
        """Save calendar to disk."""
        calendar_file = os.path.join(self.namespace_path, 'calendar.json')
        try:
            with open(calendar_file, 'w') as f:
                json.dump(self.calendar, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving calendar: {e}")

# Create singleton instance
scheduling_namespace = SchedulingNamespace()
