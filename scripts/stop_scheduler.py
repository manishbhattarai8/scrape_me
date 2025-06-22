#!/usr/bin/env python3
"""
Stop the running vegetable price scheduler
"""

import sys
import json
import psutil
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import config

def find_scheduler_process():
    """Find running scheduler process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'scheduler.py' in ' '.join(cmdline):
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def main():
    print("Looking for running scheduler...")
    
    # Check status file
    status_file = config.DATA_DIR / "scheduler_status.json"
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            
            if status.get('is_running'):
                print(f"Scheduler status: {status.get('status', 'unknown')}")
                print(f"Schedule type: {status.get('schedule_type', 'unknown')}")
        except Exception as e:
            print(f"Error reading status file: {e}")
    
    # Find and terminate process
    pid = find_scheduler_process()
    if pid:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=10)
            print(f"Scheduler process (PID: {pid}) terminated successfully.")
        except psutil.TimeoutExpired:
            print(f"Process didn't terminate gracefully, killing it...")
            proc.kill()
            print(f"Scheduler process (PID: {pid}) killed.")
        except Exception as e:
            print(f"Error stopping scheduler: {e}")
    else:
        print("No running scheduler process found.")

if __name__ == "__main__":
    main()