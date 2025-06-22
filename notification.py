import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import platform

# Windows-specific imports
if platform.system() == "Windows":
    try:
        from win10toast import ToastNotifier
        WINDOWS_NOTIFICATIONS = True
    except ImportError:
        WINDOWS_NOTIFICATIONS = False
else:
    WINDOWS_NOTIFICATIONS = False

from scheduler_config import get_config

class NotificationManager:
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger('NotificationManager')
        
        if WINDOWS_NOTIFICATIONS:
            self.toaster = ToastNotifier()
    
    def send_email(self, subject, body):
        """Send email notification"""
        try:
            email_config = self.config.NOTIFICATIONS['email']
            
            if not email_config['enabled']:
                return False
            
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            text = msg.as_string()
            server.sendmail(email_config['sender_email'], email_config['recipient_email'], text)
            server.quit()
            
            self.logger.info(f"Email sent: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def send_desktop_notification(self, title, message):
        """Send desktop notification (Windows)"""
        try:
            desktop_config = self.config.NOTIFICATIONS['desktop']
            
            if not desktop_config['enabled']:
                return False
            
            if WINDOWS_NOTIFICATIONS:
                self.toaster.show_toast(
                    title,
                    message,
                    duration=10,
                    icon_path=None,
                    threaded=True
                )
                return True
            else:
                self.logger.warning("Desktop notifications not available on this system")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send desktop notification: {e}")
            return False
    
    def send_success_notification(self, success_info):
        """Send success notification"""
        duration = success_info.get('last_run_duration', 0)
        timestamp = success_info.get('last_successful_run', '')
        
        title = "Vegetable Price Scraping - Success"
        message = f"Scraping completed successfully in {duration:.2f}s at {timestamp[:19]}"
        
        # Desktop notification
        if self.config.NOTIFICATIONS['desktop']['success_notifications']:
            self.send_desktop_notification(title, message)
        
        # Email notification
        email_body = f"""
Vegetable Price Scraping Completed Successfully

Details:
- Completion Time: {timestamp}
- Duration: {duration:.2f} seconds
- Attempts: {success_info.get('last_attempt', 1)}
- Status: Success

This is an automated notification from your vegetable price scheduler.
        """
        self.send_email(title, email_body)
    
    def send_error_notification(self, error_info):
        """Send error notification"""
        timestamp = error_info.get('last_failed_run', '')
        error = error_info.get('last_error', 'Unknown error')
        attempts = error_info.get('total_attempts', 1)
        
        title = "Vegetable Price Scraping - Failed"
        message = f"Scraping failed after {attempts} attempts at {timestamp[:19]}"
        
        # Desktop notification
        if self.config.NOTIFICATIONS['desktop']['error_notifications']:
            self.send_desktop_notification(title, message)
        
        # Email notification
        email_body = f"""
Vegetable Price Scraping Failed

Details:
- Failure Time: {timestamp}
- Total Attempts: {attempts}
- Error: {error}
- Status: Failed

Please check the logs for more details.

This is an automated notification from your vegetable price scheduler.
        """
        self.send_email(title, email_body)
    
    def send_scheduler_notification(self, action, info):
        """Send scheduler status notification"""
        timestamp = info.get('scheduler_started', info.get('scheduler_stopped', ''))
        
        title = f"Vegetable Price Scheduler - {action}"
        message = f"Scheduler {action.lower()} at {timestamp[:19]}"
        
        # Desktop notification
        self.send_desktop_notification(title, message)
        
        # Email notification (optional for scheduler events)
        if action == "started":
            schedule_type = info.get('schedule_type', 'unknown')
            email_body = f"""
Vegetable Price Scheduler Started

Details:
- Start Time: {timestamp}
- Schedule Type: {schedule_type}
- Status: Running

The scheduler will now run automatically according to the configured schedule.

This is an automated notification from your vegetable price scheduler.
            """
            self.send_email(title, email_body)