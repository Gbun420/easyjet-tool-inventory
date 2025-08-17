import pandas as pd
import os
from datetime import datetime
import json

# --- Configuration ---
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIT_LOG_FILE = os.path.join(LOG_DIR, 'audit.csv')

# --- Ensure Log Directory Exists ---
os.makedirs(LOG_DIR, exist_ok=True)

def log_action(action: str, user: str, tool_id: str = None, details: dict = None):
    """
    Logs an action to the audit trail.

    Args:
        action (str): The type of action (e.g., "tool_checkout", "tool_checkin", "calibration_update").
        user (str): The user who performed the action.
        tool_id (str, optional): The ID of the tool involved. Defaults to None.
        details (dict, optional): Additional details about the action. Defaults to None.
    """
    timestamp = datetime.utcnow().isoformat() + 'Z'  # UTC timestamp
    log_entry = {
        'timestamp': timestamp,
        'user': user,
        'action': action,
        'tool_id': tool_id,
        'details': json.dumps(details) if details else '{}'  # Store details as JSON string
    }

    # Check if file exists to write header only once
    file_exists = os.path.exists(AUDIT_LOG_FILE)

    with open(AUDIT_LOG_FILE, 'a', newline='') as f:
        df = pd.DataFrame([log_entry])
        df.to_csv(f, header=not file_exists, index=False)

def read_audit_log():
    """
    Reads the audit log from the CSV file.

    Returns:
        pandas.DataFrame: The audit log data.
    """
    if not os.path.exists(AUDIT_LOG_FILE):
        return pd.DataFrame(columns=['timestamp', 'user', 'action', 'tool_id', 'details'])
    return pd.read_csv(AUDIT_LOG_FILE)

if __name__ == '__main__':
    # Example Usage
    print("--- Logging example actions ---")
    log_action("app_start", "system")
    log_action("tool_checkout", "admin", "T001", {"from": "Hangar 1", "to": "John Doe"})
    log_action("tool_checkin", "admin", "T001", {"from": "John Doe", "to": "Hangar 1"})
    log_action("calibration_update", "technician", "T002", {"old_date": "2025-02-20", "new_date": "2025-08-20"})

    print("--- Reading audit log ---")
    audit_df = read_audit_log()
    print(audit_df)
