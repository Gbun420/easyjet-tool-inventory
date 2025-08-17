import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# --- Add the project root to the Python path ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from scripts.inventory_management import read_inventory

# --- Email Configuration (Replace with your credentials) ---
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_SENDER = 'your_email@gmail.com'
EMAIL_PASSWORD = 'your_app_password'  # Use an app-specific password for security
EMAIL_RECIPIENT = 'recipient_email@example.com'

# --- Alert Thresholds ---
CALIBRATION_WARNING_DAYS = 30
HIGH_DEMAND_THRESHOLD = 40

def send_email(subject, body):
    """
    Sends an email using the configured SMTP settings.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
    """
    if EMAIL_SENDER == 'your_email@gmail.com':
        print("\n--- EMAIL SIMULATION ---")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print("--- END EMAIL SIMULATION ---")
        print("\nNOTE: To send actual emails, configure your credentials in alerts/email_alerts.py")
        return

    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECIPIENT
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"Successfully sent email alert: '{subject}'")

    except Exception as e:
        print(f"Failed to send email alert. Error: {e}")

def check_for_alerts():
    """
    Checks the inventory for conditions that trigger alerts and sends emails.
    """
    print("--- Checking for Alerts ---")
    df = read_inventory()

    # --- 1. Upcoming Calibration Alerts ---
    df['Next_Maintenance'] = pd.to_datetime(df['Next_Maintenance'])
    calibration_due_soon = df[
        (df['Next_Maintenance'] <= datetime.now() + timedelta(days=CALIBRATION_WARNING_DAYS)) &
        (df['Next_Maintenance'] > datetime.now())
    ]

    if not calibration_due_soon.empty:
        subject = "Calibration Alert: Tools Due for Maintenance"
        body = "The following tools are due for calibration soon:\n\n"
        for index, row in calibration_due_soon.iterrows():
            body += f"- Tool ID: {row['Tool_ID']}, Box: {row['Box_Name']}, Due: {row['Next_Maintenance'].strftime('%Y-%m-%d')}\n"
        send_email(subject, body)

    # --- 2. High-Demand Tool Alerts ---
    high_demand_tools = df[df['Usage_Frequency'] >= HIGH_DEMAND_THRESHOLD]

    if not high_demand_tools.empty:
        subject = "High-Demand Tool Alert"
        body = "The following tools are currently in high demand:\n\n"
        for index, row in high_demand_tools.iterrows():
            body += f"- Tool ID: {row['Tool_ID']}, Box: {row['Box_Name']}, Usage: {row['Usage_Frequency']}\n"
        send_email(subject, body)

    # --- 3. Missing Tools/Boxes Alerts ---
    # (Assuming 'Checked_Out_By' is not 'None' for an extended period could mean missing)
    # This is a simplified check. A more robust system would track checkout duration.
    missing_tools = df[df['Checked_Out_By'] != 'None']

    if not missing_tools.empty:
        subject = "Missing Tool/Box Alert"
        body = "The following tools have been checked out and may be missing:\n\n"
        for index, row in missing_tools.iterrows():
            body += f"- Tool ID: {row['Tool_ID']}, Box: {row['Box_Name']}, Checked Out By: {row['Checked_Out_By']}\n"
        send_email(subject, body)

if __name__ == '__main__':
    check_for_alerts()
