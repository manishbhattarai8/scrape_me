import schedule
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import pytz

from scraper import NepaliPatroVegetableScraper
from scheduler_config import get_config
from notification import NotificationManager
import config as main_config

class VegetablePriceScheduler:
    def __init__(self, schedule_type='daily_morning'):
        self.config = get_config()
        self.schedule_type = schedule_type
        self.scheduler = BackgroundScheduler(
            timezone=pytz.timezone(self.config.SCHEDULER_SETTINGS['timezone'])
        )
        self.notification_manager = NotificationManager()
        self.setup_logging()
        self.status_file = main_config.DATA_DIR / "scheduler_status.json"
        self.is_running = False
        
    def setup_logging(self):
        """Setup logging for scheduler"""
        log_file = main_config.LOGS_DIR / "scheduler.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('VegetableScheduler')
        
    def save_status(self, status_info):
        """Save scheduler status to file"""
        try:
            status_data = {
                'last_updated': datetime.now().isoformat(),
                'schedule_type': self.schedule_type,
                'is_running': self.is_running,
                **status_info
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving status: {e}")
    
    def scrape_job(self):
        """Main scraping job with error handling and retries"""
        job_start_time = datetime.now()
        self.logger.info(f"Starting scheduled scraping job at {job_start_time}")
        
        for attempt in range(self.config.RETRY_SETTINGS['max_retries']):
            try:
                scraper = NepaliPatroVegetableScraper()
                scraper.run()
                
                # Job successful
                job_end_time = datetime.now()
                duration = (job_end_time - job_start_time).total_seconds()
                
                success_info = {
                    'last_successful_run': job_end_time.isoformat(),
                    'last_run_duration': duration,
                    'last_attempt': attempt + 1,
                    'status': 'success'
                }
                
                self.save_status(success_info)
                self.notification_manager.send_success_notification(success_info)
                self.logger.info(f"Scheduled scraping completed successfully in {duration:.2f} seconds")
                return
                
            except Exception as e:
                self.logger.error(f"Scraping attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.RETRY_SETTINGS['max_retries'] - 1:
                    # Calculate retry delay with optional exponential backoff
                    if self.config.RETRY_SETTINGS['exponential_backoff']:
                        delay = self.config.RETRY_SETTINGS['retry_delay'] * (2 ** attempt)
                    else:
                        delay = self.config.RETRY_SETTINGS['retry_delay']
                    
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    # All attempts failed
                    job_end_time = datetime.now()
                    failure_info = {
                        'last_failed_run': job_end_time.isoformat(),
                        'last_error': str(e),
                        'total_attempts': attempt + 1,
                        'status': 'failed'
                    }
                    
                    self.save_status(failure_info)
                    self.notification_manager.send_error_notification(failure_info)
                    self.logger.error(f"All {attempt + 1} scraping attempts failed")
    
    def setup_schedule(self):
        """Setup the chosen schedule"""
        schedule_config = self.config.SCHEDULES.get(self.schedule_type)
        
        if not schedule_config:
            raise ValueError(f"Unknown schedule type: {self.schedule_type}")
        
        self.logger.info(f"Setting up schedule: {self.schedule_type}")
        
        if schedule_config['type'] == 'interval':
            # Interval-based scheduling
            trigger_kwargs = {}
            if 'hours' in schedule_config:
                trigger_kwargs['hours'] = schedule_config['hours']
            if 'minutes' in schedule_config:
                trigger_kwargs['minutes'] = schedule_config['minutes']
            
            self.scheduler.add_job(
                self.scrape_job,
                trigger=IntervalTrigger(**trigger_kwargs),
                id='scrape_vegetables',
                max_instances=1,
                coalesce=True
            )
            
        elif schedule_config['type'] == 'daily':
            # Daily at specific time
            time_parts = schedule_config['time'].split(':')
            hour, minute = int(time_parts[0]), int(time_parts[1])
            
            self.scheduler.add_job(
                self.scrape_job,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='scrape_vegetables',
                max_instances=1,
                coalesce=True
            )
            
        elif schedule_config['type'] == 'multiple':
            # Multiple times per day
            for i, time_str in enumerate(schedule_config['times']):
                time_parts = time_str.split(':')
                hour, minute = int(time_parts[0]), int(time_parts[1])
                
                self.scheduler.add_job(
                    self.scrape_job,
                    trigger=CronTrigger(hour=hour, minute=minute),
                    id=f'scrape_vegetables_{i}',
                    max_instances=1,
                    coalesce=True
                )
                
        elif schedule_config['type'] == 'weekdays':
            # Weekdays only
            time_parts = schedule_config['time'].split(':')
            hour, minute = int(time_parts[0]), int(time_parts[1])
            
            self.scheduler.add_job(
                self.scrape_job,
                trigger=CronTrigger(day_of_week='mon-fri', hour=hour, minute=minute),
                id='scrape_vegetables',
                max_instances=1,
                coalesce=True
            )
            
        elif schedule_config['type'] == 'weekend':
            # Weekends only
            time_parts = schedule_config['time'].split(':')
            hour, minute = int(time_parts[0]), int(time_parts[1])
            
            self.scheduler.add_job(
                self.scrape_job,
                trigger=CronTrigger(day_of_week='sat,sun', hour=hour, minute=minute),
                id='scrape_vegetables',
                max_instances=1,
                coalesce=True
            )
    
    def start(self):
        """Start the scheduler"""
        try:
            self.setup_schedule()
            self.scheduler.start()
            self.is_running = True
            
            start_info = {
                'scheduler_started': datetime.now().isoformat(),
                'status': 'running',
                'schedule_type': self.schedule_type
            }
            self.save_status(start_info)
            
            self.logger.info(f"Scheduler started with schedule: {self.schedule_type}")
            self.notification_manager.send_scheduler_notification("Scheduler started", start_info)
            
            # Keep the scheduler running
            try:
                while self.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Scheduler interrupted by user")
                self.stop()
                
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            self.is_running = False
            
            stop_info = {
                'scheduler_stopped': datetime.now().isoformat(),
                'status': 'stopped'
            }
            self.save_status(stop_info)
            
            self.logger.info("Scheduler stopped")
            self.notification_manager.send_scheduler_notification("Scheduler stopped", stop_info)
            
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
    
    def get_next_run_time(self):
        """Get the next scheduled run time"""
        jobs = self.scheduler.get_jobs()
        if jobs:
            next_times = [job.next_run_time for job in jobs if job.next_run_time]
            if next_times:
                return min(next_times)
        return None

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Vegetable Price Scheduler')
    parser.add_argument('--schedule', '-s', 
                       choices=list(get_config().SCHEDULES.keys()),
                       default='daily_morning',
                       help='Schedule type to use')
    parser.add_argument('--list-schedules', '-l', 
                       action='store_true',
                       help='List available schedule types')
    
    args = parser.parse_args()
    
    if args.list_schedules:
        print("Available schedule types:")
        config = get_config()
        for name, schedule in config.SCHEDULES.items():
            print(f"  {name}: {schedule}")
        return
    
    scheduler = VegetablePriceScheduler(args.schedule)
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
        scheduler.stop()

if __name__ == "__main__":
    main()