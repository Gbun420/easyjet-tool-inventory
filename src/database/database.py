"""
Database management module for EasyJet Tool Inventory System
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import os

class ToolInventoryDatabase:
    """Database handler for tool inventory management"""
    
    def __init__(self, db_path: str = "data/tool_inventory.db"):
        self.db_path = db_path
        self._ensure_directory()
        self._init_database()
        
    def _ensure_directory(self):
        """Ensure the database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def _init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tools table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_code TEXT UNIQUE NOT NULL,
                    tool_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    location TEXT NOT NULL,
                    purchase_date DATE,
                    last_maintenance_date DATE,
                    next_maintenance_due DATE,
                    status TEXT DEFAULT 'available',
                    condition_score REAL DEFAULT 10.0,
                    usage_hours REAL DEFAULT 0.0,
                    maintenance_cost REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Usage history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_code TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    checkout_time TIMESTAMP,
                    checkin_time TIMESTAMP,
                    usage_duration REAL,
                    usage_type TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tool_code) REFERENCES tools (tool_code)
                )
            """)
            
            # Maintenance history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_code TEXT NOT NULL,
                    maintenance_date DATE NOT NULL,
                    maintenance_type TEXT NOT NULL,
                    description TEXT,
                    cost REAL DEFAULT 0.0,
                    technician TEXT,
                    condition_before REAL,
                    condition_after REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tool_code) REFERENCES tools (tool_code)
                )
            """)
            
            # Predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_code TEXT NOT NULL,
                    prediction_date DATE NOT NULL,
                    predicted_failure_date DATE,
                    confidence_score REAL,
                    maintenance_priority TEXT,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tool_code) REFERENCES tools (tool_code)
                )
            """)
            
            conn.commit()
            logging.info("Database initialized successfully")
    
    def add_tool(self, tool_data: Dict) -> bool:
        """Add a new tool to the inventory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tools (tool_code, tool_name, category, location, 
                                     purchase_date, last_maintenance_date, next_maintenance_due,
                                     status, condition_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tool_data['tool_code'],
                    tool_data['tool_name'],
                    tool_data['category'],
                    tool_data['location'],
                    tool_data.get('purchase_date'),
                    tool_data.get('last_maintenance_date'),
                    tool_data.get('next_maintenance_due'),
                    tool_data.get('status', 'available'),
                    tool_data.get('condition_score', 10.0)
                ))
                conn.commit()
                logging.info(f"Tool {tool_data['tool_code']} added successfully")
                return True
        except sqlite3.IntegrityError:
            logging.error(f"Tool {tool_data['tool_code']} already exists")
            return False
        except Exception as e:
            logging.error(f"Error adding tool: {e}")
            return False
    
    def get_tool(self, tool_code: str) -> Optional[Dict]:
        """Get tool information by code"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tools WHERE tool_code = ?", (tool_code,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logging.error(f"Error retrieving tool {tool_code}: {e}")
            return None
    
    def get_all_tools(self) -> pd.DataFrame:
        """Get all tools as DataFrame"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql_query("SELECT * FROM tools", conn)
        except Exception as e:
            logging.error(f"Error retrieving all tools: {e}")
            return pd.DataFrame()
    
    def update_tool_status(self, tool_code: str, status: str) -> bool:
        """Update tool status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tools 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE tool_code = ?
                """, (status, tool_code))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating tool status: {e}")
            return False
    
    def record_usage(self, usage_data: Dict) -> bool:
        """Record tool usage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO usage_history (tool_code, user_id, checkout_time, 
                                             checkin_time, usage_duration, usage_type, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    usage_data['tool_code'],
                    usage_data['user_id'],
                    usage_data.get('checkout_time'),
                    usage_data.get('checkin_time'),
                    usage_data.get('usage_duration'),
                    usage_data.get('usage_type'),
                    usage_data.get('notes')
                ))
                
                # Update tool usage hours
                if usage_data.get('usage_duration'):
                    cursor.execute("""
                        UPDATE tools 
                        SET usage_hours = usage_hours + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE tool_code = ?
                    """, (usage_data['usage_duration'], usage_data['tool_code']))
                
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error recording usage: {e}")
            return False
    
    def record_maintenance(self, maintenance_data: Dict) -> bool:
        """Record maintenance activity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO maintenance_history (tool_code, maintenance_date, 
                                                   maintenance_type, description, cost,
                                                   technician, condition_before, condition_after)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    maintenance_data['tool_code'],
                    maintenance_data['maintenance_date'],
                    maintenance_data['maintenance_type'],
                    maintenance_data.get('description'),
                    maintenance_data.get('cost', 0.0),
                    maintenance_data.get('technician'),
                    maintenance_data.get('condition_before'),
                    maintenance_data.get('condition_after')
                ))
                
                # Update tool maintenance info
                cursor.execute("""
                    UPDATE tools 
                    SET last_maintenance_date = ?, 
                        condition_score = ?,
                        maintenance_cost = maintenance_cost + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE tool_code = ?
                """, (
                    maintenance_data['maintenance_date'],
                    maintenance_data.get('condition_after', 10.0),
                    maintenance_data.get('cost', 0.0),
                    maintenance_data['tool_code']
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error recording maintenance: {e}")
            return False
    
    def get_tools_due_for_maintenance(self, days_ahead: int = 7) -> pd.DataFrame:
        """Get tools due for maintenance within specified days"""
        try:
            future_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT * FROM tools 
                    WHERE next_maintenance_due <= ? AND status != 'maintenance'
                    ORDER BY next_maintenance_due
                """
                return pd.read_sql_query(query, conn, params=(future_date,))
        except Exception as e:
            logging.error(f"Error retrieving maintenance due tools: {e}")
            return pd.DataFrame()
    
    def get_usage_stats(self, tool_code: str = None) -> pd.DataFrame:
        """Get usage statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if tool_code:
                    query = """
                        SELECT * FROM usage_history 
                        WHERE tool_code = ? 
                        ORDER BY checkout_time DESC
                    """
                    return pd.read_sql_query(query, conn, params=(tool_code,))
                else:
                    return pd.read_sql_query("SELECT * FROM usage_history ORDER BY checkout_time DESC", conn)
        except Exception as e:
            logging.error(f"Error retrieving usage stats: {e}")
            return pd.DataFrame()
    
    def store_prediction(self, prediction_data: Dict) -> bool:
        """Store AI prediction results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO predictions (tool_code, prediction_date, predicted_failure_date,
                                           confidence_score, maintenance_priority, model_version)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    prediction_data['tool_code'],
                    prediction_data['prediction_date'],
                    prediction_data.get('predicted_failure_date'),
                    prediction_data.get('confidence_score'),
                    prediction_data.get('maintenance_priority'),
                    prediction_data.get('model_version')
                ))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error storing prediction: {e}")
            return False
    
    def get_predictions(self, tool_code: str = None) -> pd.DataFrame:
        """Get AI predictions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if tool_code:
                    query = """
                        SELECT * FROM predictions 
                        WHERE tool_code = ? 
                        ORDER BY prediction_date DESC
                    """
                    return pd.read_sql_query(query, conn, params=(tool_code,))
                else:
                    return pd.read_sql_query("""
                        SELECT * FROM predictions 
                        ORDER BY confidence_score DESC, prediction_date DESC
                    """, conn)
        except Exception as e:
            logging.error(f"Error retrieving predictions: {e}")
            return pd.DataFrame()