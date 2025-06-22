from datetime import time
import os

class SchedulerConfig:
    # Scheduling Options
    SCHEDULES = {
        # Basic schedules
        'every_hour': {'type': 'interval', 'hours': 1},
        'every_2_hours': {'type': 'interval', 'hours': 2},
        'every_6_hours': {'type': 'interval', 'hours': 6},
        'every_12_hours': {'type': 'interval', 'hours': 12},
        'daily_morning': {'type': 'daily', 'time': '09:00'},
        'daily_evening': {'type': 'daily', 'time': '18:00'},
        'twice_daily': {'type': 'multiple', 'times': ['09:00', '18:00']},
        
        # Market-specific schedules (Nepal time)
        'market_hours': {'type': 'multiple', 'times': ['08:00', '12:00', '16:00', '20:00']},
        'business_hours': {'type': 'interval', 'hours': 3, 'start_time': '08:00', 'end_time': '18:00'},
        
        # Weekly schedules
        'weekdays_only': {'type': 'weekdays', 'time': '10:00'},
        'weekend_only': {'type': 'weekend', 'time': '11:00'},
        
        # Custom intervals
        'every_30_minutes': {'type': 'interval', 'minutes': 30},
        'every_15_minutes': {'type': 'interval', 'minutes': 15},  # For testing
    }
    
    # Notification Settings
    NOTIFICATIONS = {
        'email': {
            'enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': '',  # Your email
            'sender_password': '',  # App password
            'recipient_email': '',  # Where to send notifications
        },
        'desktop': {
            'enabled': True,  # Windows desktop notifications
            'success_notifications': True,
            'error_notifications': True,
        },
        'log_only': {
            'enabled': True,
        }
    }
    
    # Scheduler Settings
    SCHEDULER_SETTINGS = {
        'max_workers': 1,  # Only one scraping job at a time
        'coalesce': True,  # If a job is delayed, skip missed executions
        'max_instances': 1,  # Only one instance of each job
        'timezone': 'Asia/Kathmandu',
        'misfire_grace_time': 300,  # 5 minutes grace time
    }
    
    # Auto-retry settings
    RETRY_SETTINGS = {
        'max_retries': 3,
        'retry_delay': 60,  # seconds
        'exponential_backoff': True,
    }
    
    # Data management
    DATA_MANAGEMENT = {
        'auto_cleanup': True,
        'keep_days': 30,  # Keep data for 30 days
        'backup_before_cleanup': True,
        'compress_old_data': True,
    }

# Environment-based configuration
def get_config():
    config = SchedulerConfig()
    
    # Override with environment variables if present
    if os.getenv('SCRAPER_EMAIL'):
        config.NOTIFICATIONS['email']['sender_email'] = os.getenv('SCRAPER_EMAIL')
        config.NOTIFICATIONS['email']['sender_password'] = os.getenv('SCRAPER_EMAIL_PASSWORD')
        config.NOTIFICATIONS['email']['recipient_email'] = os.getenv('SCRAPER_RECIPIENT_EMAIL')
        config.NOTIFICATIONS['email']['enabled'] = True
    
    return config