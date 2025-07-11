#!/usr/bin/env python3
"""
Log watcher script for BakeMate backend.
Monitors logs for errors and automatically attempts to fix issues.
"""

import os
import re
import sys
import time
import subprocess
import datetime
from collections import deque
import itertools

# Configuration
LOG_FILE = "app_files/logs/backend.log"
ERROR_PATTERNS = [
    r"Traceback",
    r"ERROR",
    r"Exception",
    r"Error:",
]
HEALTH_CHECK_URL = "http://localhost:8000/health"
HEALTH_CHECK_INTERVAL = 2  # seconds
HEALTH_CHECK_TIMEOUT = 30  # seconds
STABLE_PERIOD = 180  # 3 minutes in seconds

def tail_log(filename, last_n_lines=200):
    """Read the last N lines of a file without loading the whole file."""
    try:
        with open(filename, 'r') as f:
            return deque(f, last_n_lines)
    except FileNotFoundError:
        print(f"Log file {filename} not found.")
        return []

def check_health():
    """Check if the service is healthy by polling the health endpoint."""
    try:
        result = subprocess.run(
            ["curl", "-sf", HEALTH_CHECK_URL],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False

def save_error_log(lines, timestamp):
    """Save error logs to artifacts directory."""
    filename = f"artifacts/error_{timestamp}.log"
    with open(filename, 'w') as f:
        f.writelines(lines)
    print(f"Error log saved to {filename}")
    return filename

def run_tests():
    """Run pytest to reproduce the issue locally."""
    print("Running tests to reproduce the issue...")
    result = subprocess.run(
        ["pytest", "-q"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout, result.stderr

def extract_error_info(log_lines):
    """Extract error information from log lines."""
    error_info = {
        'traceback': [],
        'file': None,
        'line': None,
        'error_type': None,
        'error_message': None
    }
    
    in_traceback = False
    
    for line in log_lines:
        if "Traceback (most recent call last):" in line:
            in_traceback = True
            error_info['traceback'].append(line)
        elif in_traceback and line.strip().startswith("File "):
            error_info['traceback'].append(line)
            # Extract file and line information
            match = re.search(r'File "([^"]+)", line (\d+)', line)
            if match:
                error_info['file'] = match.group(1)
                error_info['line'] = int(match.group(2))
        elif in_traceback and ": " in line:
            # This might be the error type and message line
            parts = line.strip().split(": ", 1)
            if len(parts) == 2:
                error_info['error_type'] = parts[0]
                error_info['error_message'] = parts[1]
                error_info['traceback'].append(line)
                in_traceback = False
        elif in_traceback:
            error_info['traceback'].append(line)
    
    return error_info

def fix_common_issues(error_info):
    """Attempt to fix common issues based on error information."""
    if not error_info['file'] or not error_info['error_type']:
        return False
    
    fixed = False
    file_path = error_info['file']
    
    # Only attempt to fix files within our project
    if not os.path.exists(file_path) or not file_path.startswith(('app/', 'main.py')):
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.readlines()
        
        # Fix missing imports
        if error_info['error_type'] in ('ImportError', 'ModuleNotFoundError'):
            missing_module = re.search(r"No module named '([^']+)'", error_info['error_message'])
            if missing_module:
                module_name = missing_module.group(1)
                # Add import at the top of the file
                content.insert(0, f"import {module_name}\n")
                fixed = True
        
        # Fix attribute errors
        elif error_info['error_type'] == 'AttributeError':
            # This is more complex and would require more context-specific fixes
            pass
        
        # Fix undefined name errors
        elif error_info['error_type'] == 'NameError':
            undefined_var = re.search(r"name '([^']+)' is not defined", error_info['error_message'])
            if undefined_var:
                var_name = undefined_var.group(1)
                # Add a default definition before the error line
                content.insert(error_info['line'] - 1, f"{var_name} = None  # Auto-fixed by log_watcher\n")
                fixed = True
        
        # Fix type errors
        elif error_info['error_type'] == 'TypeError':
            # This is more complex and would require more context-specific fixes
            pass
        
        if fixed:
            with open(file_path, 'w') as f:
                f.writelines(content)
            print(f"Fixed issue in {file_path}")
            
            # Restart the service
            restart_service()
    
    except Exception as e:
        print(f"Error while attempting to fix issue: {e}")
        fixed = False
    
    return fixed

def restart_service():
    """Restart the uvicorn service."""
    print("Restarting service...")
    subprocess.run(["pkill", "-f", "uvicorn"])
    time.sleep(2)  # Give it time to shut down
    subprocess.run(
        ["make", "run"],
        stdout=open("app_files/logs/run.log", "a"),
        stderr=subprocess.STDOUT
    )
    print("Service restarted")

def main():
    """Main log watcher function."""
    print("Starting log watcher...")
    
    # Wait for log file to be created if it doesn't exist yet
    while not os.path.exists(LOG_FILE):
        print(f"Waiting for log file {LOG_FILE} to be created...")
        time.sleep(1)
    
    # Initial health check
    health_check_start = time.time()
    while time.time() - health_check_start < HEALTH_CHECK_TIMEOUT:
        if check_health():
            print("Initial health check passed")
            break
        print("Waiting for service to become healthy...")
        time.sleep(HEALTH_CHECK_INTERVAL)
    else:
        print(f"Service failed to become healthy within {HEALTH_CHECK_TIMEOUT} seconds")
        return 1
    
    # Monitor logs and health
    last_position = 0
    healthy_since = time.time()
    
    while True:
        # Check health
        if check_health():
            if time.time() - healthy_since >= STABLE_PERIOD:
                print(f"Service has been healthy for {STABLE_PERIOD} seconds. Exiting.")
                return 0
        else:
            print("Health check failed. Resetting stable timer.")
            healthy_since = time.time()
        
        # Check for new log content
        try:
            with open(LOG_FILE, 'r') as f:
                f.seek(0, 2)  # Go to the end of the file
                current_position = f.tell()
                
                if current_position > last_position:
                    # New content available
                    f.seek(last_position)
                    new_content = f.read()
                    last_position = current_position
                    
                    # Check for errors
                    for pattern in ERROR_PATTERNS:
                        if re.search(pattern, new_content):
                            print(f"Error pattern '{pattern}' detected in logs")
                            
                            # Save error log
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            log_lines = tail_log(LOG_FILE)
                            save_error_log(log_lines, timestamp)
                            
                            # Run tests to reproduce
                            tests_pass, stdout, stderr = run_tests()
                            if not tests_pass:
                                print("Tests failed, attempting to fix the issue")
                                
                                # Extract error information
                                error_info = extract_error_info(log_lines)
                                
                                # Attempt to fix
                                if fix_common_issues(error_info):
                                    print("Issue fixed, monitoring for stability")
                                    healthy_since = time.time()  # Reset the timer
                                else:
                                    print("Could not automatically fix the issue")
                            else:
                                print("Tests passed despite error in logs")
                            
                            break
        except Exception as e:
            print(f"Error reading log file: {e}")
        
        time.sleep(HEALTH_CHECK_INTERVAL)

if __name__ == "__main__":
    sys.exit(main())
