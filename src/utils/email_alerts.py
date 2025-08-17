"""
Email Alert System for EasyJet Tool Inventory System
Handles automated email notifications for maintenance alerts and system events
"""
import smtplib
import ssl
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from jinja2 import Template
import pandas as pd

class EmailAlertSystem:
    """Email alert system for maintenance notifications"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.notification_emails = os.getenv('NOTIFICATION_EMAILS', '').split(',')
        self.company_name = "EasyJet Engineering Malta"
        
    def send_maintenance_alert(self, tools_due: pd.DataFrame) -> bool:
        """Send maintenance due alert email"""
        try:
            if tools_due.empty:
                return True
            
            subject = f"🔧 {self.company_name} - Tools Maintenance Alert"
            
            # Create email content
            html_content = self._create_maintenance_alert_html(tools_due)
            text_content = self._create_maintenance_alert_text(tools_due)
            
            return self._send_email(subject, html_content, text_content)
            
        except Exception as e:
            logging.error(f"Error sending maintenance alert: {e}")
            return False
    
    def send_high_risk_alert(self, predictions: List[Dict]) -> bool:
        """Send high-risk prediction alert"""
        try:
            high_risk_predictions = [p for p in predictions if p['confidence_score'] > 0.8]
            
            if not high_risk_predictions:
                return True
            
            subject = f"🚨 {self.company_name} - High Risk Tool Alert"
            
            html_content = self._create_risk_alert_html(high_risk_predictions)
            text_content = self._create_risk_alert_text(high_risk_predictions)
            
            return self._send_email(subject, html_content, text_content)
            
        except Exception as e:
            logging.error(f"Error sending risk alert: {e}")
            return False
    
    def send_daily_summary(self, tools_df: pd.DataFrame, usage_stats: Dict, 
                          maintenance_due: pd.DataFrame) -> bool:
        """Send daily summary email"""
        try:
            subject = f"📊 {self.company_name} - Daily Tool Inventory Summary"
            
            html_content = self._create_daily_summary_html(tools_df, usage_stats, maintenance_due)
            text_content = self._create_daily_summary_text(tools_df, usage_stats, maintenance_due)
            
            return self._send_email(subject, html_content, text_content)
            
        except Exception as e:
            logging.error(f"Error sending daily summary: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """Send test email to verify configuration"""
        try:
            subject = f"✅ Test Email - {self.company_name} Tool Inventory System"
            
            html_content = """
            <html>
                <body>
                    <h2>Test Email Successful</h2>
                    <p>This is a test email from the EasyJet Tool Inventory System.</p>
                    <p>If you receive this email, the email configuration is working correctly.</p>
                    <p><strong>Timestamp:</strong> {timestamp}</p>
                </body>
            </html>
            """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            text_content = f"""
            Test Email Successful
            
            This is a test email from the EasyJet Tool Inventory System.
            If you receive this email, the email configuration is working correctly.
            
            Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """
            
            return self._send_email(subject, html_content, text_content)
            
        except Exception as e:
            logging.error(f"Error sending test email: {e}")
            return False
    
    def _send_email(self, subject: str, html_content: str, text_content: str,
                   recipients: Optional[List[str]] = None) -> bool:
        """Send email with both HTML and text content"""
        try:
            if not self.email_user or not self.email_password:
                logging.error("Email credentials not configured")
                return False
            
            recipients = recipients or [email.strip() for email in self.notification_emails if email.strip()]
            
            if not recipients:
                logging.error("No email recipients configured")
                return False
            
            # Create message
            message = MimeMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_user
            message["To"] = ", ".join(recipients)
            
            # Create text and HTML parts
            text_part = MimeText(text_content, "plain")
            html_part = MimeText(html_content, "html")
            
            # Add parts to message
            message.attach(text_part)
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_user, self.email_password)
                server.sendmail(self.email_user, recipients, message.as_string())
            
            logging.info(f"Email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return False
    
    def _create_maintenance_alert_html(self, tools_due: pd.DataFrame) -> str:
        """Create HTML content for maintenance alert"""
        html_template = """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background-color: #ff6900; color: white; padding: 15px; border-radius: 5px; }
                    .content { margin: 20px 0; }
                    .tool-item { 
                        border: 1px solid #ddd; 
                        border-radius: 5px; 
                        padding: 10px; 
                        margin: 10px 0; 
                        background-color: #f9f9f9;
                    }
                    .urgent { border-left: 5px solid #dc3545; background-color: #f8d7da; }
                    .warning { border-left: 5px solid #ffc107; background-color: #fff3cd; }
                    .footer { margin-top: 30px; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>🔧 Tool Maintenance Alert</h2>
                    <p>{{ company_name }} - Tool Inventory System</p>
                </div>
                
                <div class="content">
                    <p>The following tools require maintenance attention:</p>
                    
                    {% for tool in tools %}
                    <div class="tool-item {{ tool.urgency_class }}">
                        <h4>{{ tool.tool_name }} ({{ tool.tool_code }})</h4>
                        <p><strong>Category:</strong> {{ tool.category }}</p>
                        <p><strong>Location:</strong> {{ tool.location }}</p>
                        <p><strong>Maintenance Due:</strong> {{ tool.next_maintenance_due }}</p>
                        <p><strong>Status:</strong> {{ tool.urgency_text }}</p>
                        <p><strong>Current Condition:</strong> {{ tool.condition_score }}/10</p>
                        {% if tool.usage_hours > 0 %}
                        <p><strong>Usage Hours:</strong> {{ tool.usage_hours }}</p>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                
                <div class="footer">
                    <p>This is an automated message from the EasyJet Tool Inventory System.</p>
                    <p>Generated on: {{ timestamp }}</p>
                </div>
            </body>
        </html>
        """
        
        # Prepare tool data with urgency information
        tools_data = []
        for _, tool in tools_due.iterrows():
            due_date = pd.to_datetime(tool['next_maintenance_due'])
            days_until = (due_date - datetime.now()).days
            
            if days_until < 0:
                urgency_class = "urgent"
                urgency_text = f"OVERDUE by {abs(days_until)} days"
            elif days_until <= 3:
                urgency_class = "urgent"
                urgency_text = f"Due in {days_until} days"
            else:
                urgency_class = "warning"
                urgency_text = f"Due in {days_until} days"
            
            tool_data = tool.to_dict()
            tool_data['urgency_class'] = urgency_class
            tool_data['urgency_text'] = urgency_text
            tools_data.append(tool_data)
        
        template = Template(html_template)
        return template.render(
            company_name=self.company_name,
            tools=tools_data,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def _create_maintenance_alert_text(self, tools_due: pd.DataFrame) -> str:
        """Create text content for maintenance alert"""
        content = f"""
TOOL MAINTENANCE ALERT
{self.company_name} - Tool Inventory System

The following tools require maintenance attention:

"""
        
        for _, tool in tools_due.iterrows():
            due_date = pd.to_datetime(tool['next_maintenance_due'])
            days_until = (due_date - datetime.now()).days
            
            if days_until < 0:
                urgency_text = f"OVERDUE by {abs(days_until)} days"
            else:
                urgency_text = f"Due in {days_until} days"
            
            content += f"""
Tool: {tool['tool_name']} ({tool['tool_code']})
Category: {tool['category']}
Location: {tool['location']}
Maintenance Due: {tool['next_maintenance_due']}
Status: {urgency_text}
Condition: {tool['condition_score']}/10
Usage Hours: {tool.get('usage_hours', 0)}
---
"""
        
        content += f"""

This is an automated message from the EasyJet Tool Inventory System.
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        return content
    
    def _create_risk_alert_html(self, predictions: List[Dict]) -> str:
        """Create HTML content for risk alert"""
        html_template = """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background-color: #dc3545; color: white; padding: 15px; border-radius: 5px; }
                    .content { margin: 20px 0; }
                    .prediction-item { 
                        border: 1px solid #ddd; 
                        border-radius: 5px; 
                        padding: 10px; 
                        margin: 10px 0; 
                        background-color: #fff5f5;
                        border-left: 5px solid #dc3545;
                    }
                    .risk-score { 
                        font-weight: bold; 
                        color: #dc3545; 
                        font-size: 1.2em; 
                    }
                    .footer { margin-top: 30px; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>🚨 High Risk Tool Alert</h2>
                    <p>{{ company_name }} - AI Prediction System</p>
                </div>
                
                <div class="content">
                    <p>Our AI system has identified the following tools at high risk of failure:</p>
                    
                    {% for pred in predictions %}
                    <div class="prediction-item">
                        <h4>{{ pred.tool_code }}</h4>
                        <p class="risk-score">Risk Score: {{ (pred.confidence_score * 100)|round(1) }}%</p>
                        <p><strong>Priority:</strong> {{ pred.maintenance_priority }}</p>
                        <p><strong>Estimated Failure Date:</strong> {{ pred.predicted_failure_date }}</p>
                        <p><strong>Days Until Maintenance:</strong> {{ pred.days_until_maintenance }}</p>
                        <p><strong>Recommended Action:</strong> Immediate inspection and preventive maintenance</p>
                    </div>
                    {% endfor %}
                </div>
                
                <div class="footer">
                    <p>This alert was generated by the AI predictive maintenance system.</p>
                    <p>Please take immediate action to prevent tool failures and potential safety issues.</p>
                    <p>Generated on: {{ timestamp }}</p>
                </div>
            </body>
        </html>
        """
        
        template = Template(html_template)
        return template.render(
            company_name=self.company_name,
            predictions=predictions,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def _create_risk_alert_text(self, predictions: List[Dict]) -> str:
        """Create text content for risk alert"""
        content = f"""
HIGH RISK TOOL ALERT
{self.company_name} - AI Prediction System

Our AI system has identified the following tools at high risk of failure:

"""
        
        for pred in predictions:
            content += f"""
Tool Code: {pred['tool_code']}
Risk Score: {pred['confidence_score']*100:.1f}%
Priority: {pred['maintenance_priority']}
Estimated Failure Date: {pred['predicted_failure_date']}
Days Until Maintenance: {pred['days_until_maintenance']}
Recommended Action: Immediate inspection and preventive maintenance
---
"""
        
        content += f"""

This alert was generated by the AI predictive maintenance system.
Please take immediate action to prevent tool failures and potential safety issues.

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        return content
    
    def _create_daily_summary_html(self, tools_df: pd.DataFrame, usage_stats: Dict, 
                                  maintenance_due: pd.DataFrame) -> str:
        """Create HTML content for daily summary"""
        html_template = """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background-color: #ff6900; color: white; padding: 15px; border-radius: 5px; }
                    .metrics { display: flex; justify-content: space-around; margin: 20px 0; }
                    .metric { 
                        text-align: center; 
                        background-color: #f8f9fa; 
                        padding: 15px; 
                        border-radius: 5px; 
                        border: 1px solid #dee2e6;
                    }
                    .metric-value { font-size: 2em; font-weight: bold; color: #ff6900; }
                    .section { margin: 20px 0; }
                    .footer { margin-top: 30px; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>📊 Daily Tool Inventory Summary</h2>
                    <p>{{ company_name }} - {{ date }}</p>
                </div>
                
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{{ total_tools }}</div>
                        <div>Total Tools</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{{ available_tools }}</div>
                        <div>Available</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{{ in_use_tools }}</div>
                        <div>In Use</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{{ maintenance_count }}</div>
                        <div>Need Maintenance</div>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📈 Usage Statistics</h3>
                    <p>Total Usage Today: {{ usage_stats.total_hours|round(1) }} hours</p>
                    <p>Active Tools: {{ usage_stats.active_tools }}</p>
                    <p>Average Usage per Tool: {{ usage_stats.avg_usage|round(1) }} hours</p>
                </div>
                
                {% if urgent_maintenance|length > 0 %}
                <div class="section">
                    <h3>🚨 Urgent Maintenance Required</h3>
                    {% for tool in urgent_maintenance %}
                    <p>• {{ tool.tool_name }} ({{ tool.tool_code }}) - {{ tool.urgency_text }}</p>
                    {% endfor %}
                </div>
                {% endif %}
                
                <div class="footer">
                    <p>Daily summary generated automatically by the Tool Inventory System.</p>
                    <p>Generated on: {{ timestamp }}</p>
                </div>
            </body>
        </html>
        """
        
        # Calculate metrics
        total_tools = len(tools_df)
        available_tools = len(tools_df[tools_df['status'] == 'available']) if not tools_df.empty else 0
        in_use_tools = len(tools_df[tools_df['status'] == 'in_use']) if not tools_df.empty else 0
        maintenance_count = len(maintenance_due)
        
        # Urgent maintenance items
        urgent_maintenance = []
        if not maintenance_due.empty:
            for _, tool in maintenance_due.iterrows():
                due_date = pd.to_datetime(tool['next_maintenance_due'])
                days_until = (due_date - datetime.now()).days
                
                if days_until <= 3:  # Only urgent items
                    urgency_text = f"OVERDUE by {abs(days_until)} days" if days_until < 0 else f"Due in {days_until} days"
                    tool_data = tool.to_dict()
                    tool_data['urgency_text'] = urgency_text
                    urgent_maintenance.append(tool_data)
        
        template = Template(html_template)
        return template.render(
            company_name=self.company_name,
            date=datetime.now().strftime("%Y-%m-%d"),
            total_tools=total_tools,
            available_tools=available_tools,
            in_use_tools=in_use_tools,
            maintenance_count=maintenance_count,
            usage_stats=usage_stats,
            urgent_maintenance=urgent_maintenance,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def _create_daily_summary_text(self, tools_df: pd.DataFrame, usage_stats: Dict, 
                                  maintenance_due: pd.DataFrame) -> str:
        """Create text content for daily summary"""
        total_tools = len(tools_df)
        available_tools = len(tools_df[tools_df['status'] == 'available']) if not tools_df.empty else 0
        in_use_tools = len(tools_df[tools_df['status'] == 'in_use']) if not tools_df.empty else 0
        maintenance_count = len(maintenance_due)
        
        content = f"""
DAILY TOOL INVENTORY SUMMARY
{self.company_name} - {datetime.now().strftime("%Y-%m-%d")}

OVERVIEW:
Total Tools: {total_tools}
Available: {available_tools}
In Use: {in_use_tools}
Need Maintenance: {maintenance_count}

USAGE STATISTICS:
Total Usage Today: {usage_stats.get('total_hours', 0):.1f} hours
Active Tools: {usage_stats.get('active_tools', 0)}
Average Usage per Tool: {usage_stats.get('avg_usage', 0):.1f} hours
"""
        
        # Add urgent maintenance if any
        if not maintenance_due.empty:
            urgent_items = []
            for _, tool in maintenance_due.iterrows():
                due_date = pd.to_datetime(tool['next_maintenance_due'])
                days_until = (due_date - datetime.now()).days
                
                if days_until <= 3:
                    urgency_text = f"OVERDUE by {abs(days_until)} days" if days_until < 0 else f"Due in {days_until} days"
                    urgent_items.append(f"• {tool['tool_name']} ({tool['tool_code']}) - {urgency_text}")
            
            if urgent_items:
                content += "\n\nURGENT MAINTENANCE REQUIRED:\n"
                content += "\n".join(urgent_items)
        
        content += f"""

Daily summary generated automatically by the Tool Inventory System.
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        return content