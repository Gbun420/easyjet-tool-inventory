"""
Unit tests for database functionality
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
import pandas as pd

from src.database.database import ToolInventoryDatabase

@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name
    
    db = ToolInventoryDatabase(db_path)
    yield db
    
    # Cleanup
    os.unlink(db_path)

@pytest.fixture
def sample_tool_data():
    """Sample tool data for testing"""
    return {
        'tool_code': 'TEST-001',
        'tool_name': 'Test Pneumatic Drill',
        'category': 'Power Tools',
        'location': 'Test Workshop',
        'purchase_date': '2023-01-15',
        'next_maintenance_due': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        'condition_score': 8.5
    }

class TestToolInventoryDatabase:
    
    def test_database_initialization(self, temp_db):
        """Test database initialization"""
        assert temp_db is not None
        assert os.path.exists(temp_db.db_path)
    
    def test_add_tool(self, temp_db, sample_tool_data):
        """Test adding a new tool"""
        result = temp_db.add_tool(sample_tool_data)
        assert result is True
        
        # Verify tool was added
        tool = temp_db.get_tool(sample_tool_data['tool_code'])
        assert tool is not None
        assert tool['tool_name'] == sample_tool_data['tool_name']
        assert tool['category'] == sample_tool_data['category']
    
    def test_add_duplicate_tool(self, temp_db, sample_tool_data):
        """Test adding duplicate tool should fail"""
        temp_db.add_tool(sample_tool_data)
        result = temp_db.add_tool(sample_tool_data)  # Duplicate
        assert result is False
    
    def test_get_tool(self, temp_db, sample_tool_data):
        """Test retrieving a tool"""
        temp_db.add_tool(sample_tool_data)
        
        tool = temp_db.get_tool(sample_tool_data['tool_code'])
        assert tool is not None
        assert tool['tool_code'] == sample_tool_data['tool_code']
        
        # Test non-existent tool
        non_existent = temp_db.get_tool('NON-EXISTENT')
        assert non_existent is None
    
    def test_get_all_tools(self, temp_db, sample_tool_data):
        """Test retrieving all tools"""
        # Initially empty
        all_tools = temp_db.get_all_tools()
        assert len(all_tools) == 0
        
        # Add a tool
        temp_db.add_tool(sample_tool_data)
        all_tools = temp_db.get_all_tools()
        assert len(all_tools) == 1
        assert all_tools.iloc[0]['tool_code'] == sample_tool_data['tool_code']
    
    def test_update_tool_status(self, temp_db, sample_tool_data):
        """Test updating tool status"""
        temp_db.add_tool(sample_tool_data)
        
        # Update status
        result = temp_db.update_tool_status(sample_tool_data['tool_code'], 'in_use')
        assert result is True
        
        # Verify status was updated
        tool = temp_db.get_tool(sample_tool_data['tool_code'])
        assert tool['status'] == 'in_use'
        
        # Test updating non-existent tool
        result = temp_db.update_tool_status('NON-EXISTENT', 'in_use')
        assert result is False
    
    def test_record_usage(self, temp_db, sample_tool_data):
        """Test recording tool usage"""
        temp_db.add_tool(sample_tool_data)
        
        usage_data = {
            'tool_code': sample_tool_data['tool_code'],
            'user_id': 'test_user',
            'checkout_time': datetime.now().isoformat(),
            'usage_duration': 2.5,
            'usage_type': 'checkout',
            'notes': 'Test usage'
        }
        
        result = temp_db.record_usage(usage_data)
        assert result is True
        
        # Verify usage was recorded
        usage_stats = temp_db.get_usage_stats(sample_tool_data['tool_code'])
        assert len(usage_stats) == 1
        assert usage_stats.iloc[0]['user_id'] == 'test_user'
    
    def test_record_maintenance(self, temp_db, sample_tool_data):
        """Test recording maintenance activity"""
        temp_db.add_tool(sample_tool_data)
        
        maintenance_data = {
            'tool_code': sample_tool_data['tool_code'],
            'maintenance_date': datetime.now().strftime('%Y-%m-%d'),
            'maintenance_type': 'Preventive',
            'description': 'Routine maintenance',
            'cost': 150.0,
            'technician': 'John Doe',
            'condition_before': 8.5,
            'condition_after': 9.5
        }
        
        result = temp_db.record_maintenance(maintenance_data)
        assert result is True
        
        # Verify tool condition was updated
        tool = temp_db.get_tool(sample_tool_data['tool_code'])
        assert tool['condition_score'] == 9.5
        assert tool['maintenance_cost'] == 150.0
    
    def test_get_tools_due_for_maintenance(self, temp_db):
        """Test retrieving tools due for maintenance"""
        # Add tool due for maintenance soon
        tool_data_soon = {
            'tool_code': 'SOON-001',
            'tool_name': 'Due Soon Tool',
            'category': 'Test Category',
            'location': 'Test Location',
            'next_maintenance_due': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'condition_score': 7.0
        }
        
        # Add tool due later
        tool_data_later = {
            'tool_code': 'LATER-001', 
            'tool_name': 'Due Later Tool',
            'category': 'Test Category',
            'location': 'Test Location',
            'next_maintenance_due': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'condition_score': 9.0
        }
        
        temp_db.add_tool(tool_data_soon)
        temp_db.add_tool(tool_data_later)
        
        # Get tools due within 7 days
        due_tools = temp_db.get_tools_due_for_maintenance(7)
        assert len(due_tools) == 1
        assert due_tools.iloc[0]['tool_code'] == 'SOON-001'
        
        # Get tools due within 45 days
        due_tools_extended = temp_db.get_tools_due_for_maintenance(45)
        assert len(due_tools_extended) == 2
    
    def test_store_and_get_predictions(self, temp_db, sample_tool_data):
        """Test storing and retrieving AI predictions"""
        temp_db.add_tool(sample_tool_data)
        
        prediction_data = {
            'tool_code': sample_tool_data['tool_code'],
            'prediction_date': datetime.now().strftime('%Y-%m-%d'),
            'predicted_failure_date': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
            'confidence_score': 0.85,
            'maintenance_priority': 'High',
            'model_version': '1.0'
        }
        
        result = temp_db.store_prediction(prediction_data)
        assert result is True
        
        # Verify prediction was stored
        predictions = temp_db.get_predictions(sample_tool_data['tool_code'])
        assert len(predictions) == 1
        assert predictions.iloc[0]['confidence_score'] == 0.85
        assert predictions.iloc[0]['maintenance_priority'] == 'High'
        
        # Test getting all predictions
        all_predictions = temp_db.get_predictions()
        assert len(all_predictions) == 1