"""
Production runner for EasyJet Tool Inventory System
Includes automated model training, email alerts, and system monitoring
"""
import os
import sys
import time
import schedule
import logging
from datetime import datetime, timedelta
import pandas as pd
import subprocess
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.database import ToolInventoryDatabase
from src.models.predictive_model import MaintenancePredictionModel
from src.utils.email_alerts import EmailAlertSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tool_inventory.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ToolInventoryRunner:
    """Main runner for the tool inventory system"""
    
    def __init__(self):
        self.db = ToolInventoryDatabase()
        self.predictor = MaintenancePredictionModel()
        self.email_system = EmailAlertSystem()
        self.streamlit_process = None
        
    def start_streamlit_app(self):
        """Start the Streamlit application"""
        try:
            logger.info("Starting Streamlit application...")
            cmd = [
                sys.executable, "-m", "streamlit", "run", "app.py",
                "--server.port=8501",
                "--server.address=0.0.0.0",
                "--server.headless=true"
            ]
            
            self.streamlit_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            logger.info("Streamlit application started successfully")
            
        except Exception as e:
            logger.error(f"Error starting Streamlit app: {e}")
    
    def check_maintenance_alerts(self):
        """Check for tools requiring maintenance and send alerts"""
        try:
            logger.info("Checking maintenance alerts...")
            
            # Get tools due for maintenance in the next 7 days
            maintenance_due = self.db.get_tools_due_for_maintenance(7)
            
            if not maintenance_due.empty:
                logger.info(f"Found {len(maintenance_due)} tools requiring maintenance")
                
                # Send maintenance alert email
                if self.email_system.send_maintenance_alert(maintenance_due):
                    logger.info("Maintenance alert email sent successfully")
                else:
                    logger.error("Failed to send maintenance alert email")
            else:
                logger.info("No tools require immediate maintenance")
                
        except Exception as e:
            logger.error(f"Error checking maintenance alerts: {e}")
    
    def run_ai_predictions(self):
        """Run AI predictions and send high-risk alerts"""
        try:
            logger.info("Running AI predictions...")
            
            # Get all tools and related data
            tools_df = self.db.get_all_tools()
            usage_df = self.db.get_usage_stats()
            
            if tools_df.empty:
                logger.info("No tools in database for predictions")
                return
            
            # Prepare features for prediction
            features_df = self.predictor.prepare_features(tools_df, usage_df, pd.DataFrame())
            
            if not features_df.empty:
                # Train model if needed (daily retraining)
                if self._should_retrain_model():
                    logger.info("Retraining AI model with latest data...")
                    maintenance_df = pd.DataFrame()  # Get from DB if available
                    
                    if self.predictor.retrain_with_new_data(tools_df, usage_df, maintenance_df):
                        logger.info("Model retrained successfully")
                    else:
                        logger.warning("Model retraining failed")
                
                # Generate predictions
                predictions = self.predictor.predict_maintenance_needs(tools_df)
                
                if predictions:
                    logger.info(f"Generated {len(predictions)} predictions")
                    
                    # Store predictions in database
                    for pred in predictions:
                        self.db.store_prediction(pred)
                    
                    # Send high-risk alerts
                    high_risk_predictions = [p for p in predictions if p['confidence_score'] > 0.8]
                    
                    if high_risk_predictions:
                        if self.email_system.send_high_risk_alert(high_risk_predictions):
                            logger.info(f"High-risk alert sent for {len(high_risk_predictions)} tools")
                        else:
                            logger.error("Failed to send high-risk alert")
                else:
                    logger.info("No predictions generated")
            
        except Exception as e:
            logger.error(f"Error running AI predictions: {e}")
    
    def send_daily_summary(self):
        """Send daily summary email"""
        try:
            logger.info("Sending daily summary...")
            
            tools_df = self.db.get_all_tools()
            maintenance_due = self.db.get_tools_due_for_maintenance(30)
            
            # Calculate usage stats for today
            usage_stats = {
                'total_hours': 0,
                'active_tools': 0,
                'avg_usage': 0
            }
            
            usage_df = self.db.get_usage_stats()
            if not usage_df.empty:
                today = datetime.now().date()
                today_usage = usage_df[
                    pd.to_datetime(usage_df['checkout_time']).dt.date == today
                ]
                
                if not today_usage.empty:
                    usage_stats['total_hours'] = today_usage['usage_duration'].sum()
                    usage_stats['active_tools'] = today_usage['tool_code'].nunique()
                    usage_stats['avg_usage'] = today_usage['usage_duration'].mean()
            
            if self.email_system.send_daily_summary(tools_df, usage_stats, maintenance_due):
                logger.info("Daily summary sent successfully")
            else:
                logger.error("Failed to send daily summary")
                
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    def _should_retrain_model(self) -> bool:
        """Check if model should be retrained"""
        try:
            # Check if model file exists and its age
            model_path = "models/regression_model.joblib"
            
            if not os.path.exists(model_path):
                return True
            
            # Retrain if model is older than 24 hours
            model_age = time.time() - os.path.getmtime(model_path)
            return model_age > 86400  # 24 hours in seconds
            
        except Exception as e:
            logger.error(f"Error checking model retrain condition: {e}")
            return False
    
    def setup_scheduled_tasks(self):
        """Setup scheduled background tasks"""
        logger.info("Setting up scheduled tasks...")
        
        # Check maintenance alerts every 2 hours
        schedule.every(2).hours.do(self.check_maintenance_alerts)
        
        # Run AI predictions every 6 hours
        schedule.every(6).hours.do(self.run_ai_predictions)
        
        # Send daily summary at 8 AM
        schedule.every().day.at("08:00").do(self.send_daily_summary)
        
        logger.info("Scheduled tasks configured")
    
    def run_scheduled_tasks(self):
        """Run the scheduled task loop"""
        logger.info("Starting scheduled task runner...")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                logger.info("Scheduled task runner stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduled task runner: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def initialize_sample_data(self):
        """Initialize sample data if database is empty"""
        try:
            tools_df = self.db.get_all_tools()
            
            if tools_df.empty:
                logger.info("Database is empty, initializing sample data...")
                
                sample_tools = [
                    {
                        'tool_code': 'EJ-PWR-001',
                        'tool_name': 'Pneumatic Drill',
                        'category': 'Power Tools',
                        'location': 'Workshop A - Bay 1',
                        'purchase_date': '2023-01-15',
                        'next_maintenance_due': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                        'condition_score': 8.5
                    },
                    {
                        'tool_code': 'EJ-PWR-002',
                        'tool_name': 'Impact Wrench',
                        'category': 'Power Tools',
                        'location': 'Workshop A - Bay 2',
                        'purchase_date': '2023-02-20',
                        'next_maintenance_due': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
                        'condition_score': 9.2
                    },
                    {
                        'tool_code': 'EJ-HND-001',
                        'tool_name': 'Torque Wrench Set',
                        'category': 'Hand Tools',
                        'location': 'Workshop B - Bay 1',
                        'purchase_date': '2023-03-10',
                        'next_maintenance_due': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),
                        'condition_score': 9.8
                    },
                    {
                        'tool_code': 'EJ-MSR-001',
                        'tool_name': 'Digital Multimeter',
                        'category': 'Measuring Tools',
                        'location': 'Electronics Lab',
                        'purchase_date': '2023-04-05',
                        'next_maintenance_due': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
                        'condition_score': 9.5
                    },
                    {
                        'tool_code': 'EJ-SFT-001',
                        'tool_name': 'Safety Harness',
                        'category': 'Safety Equipment',
                        'location': 'Safety Equipment Room',
                        'purchase_date': '2023-05-12',
                        'next_maintenance_due': (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
                        'condition_score': 9.0
                    }
                ]
                
                for tool_data in sample_tools:
                    self.db.add_tool(tool_data)
                
                logger.info(f"Added {len(sample_tools)} sample tools to database")
        
        except Exception as e:
            logger.error(f"Error initializing sample data: {e}")
    
    def run(self):
        """Main run method"""
        logger.info("Starting EasyJet Tool Inventory System...")
        
        try:
            # Initialize sample data if needed
            self.initialize_sample_data()
            
            # Start Streamlit app in background
            self.start_streamlit_app()
            
            # Setup and run scheduled tasks
            self.setup_scheduled_tasks()
            
            # Run initial checks
            self.check_maintenance_alerts()
            self.run_ai_predictions()
            
            # Start scheduled task loop
            self.run_scheduled_tasks()
            
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            if self.streamlit_process:
                self.streamlit_process.terminate()
            logger.info("Application shutdown complete")

def main():
    """Main entry point"""
    runner = ToolInventoryRunner()
    runner.run()

if __name__ == "__main__":
    main()