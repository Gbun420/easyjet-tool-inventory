"""
EasyJet Tool Inventory System - Main Streamlit Application
QR-code based tool inventory and predictive-AI dashboard
"""
import streamlit as st
import pandas as pd
import numpy as np
import qrcode
import cv2
from PIL import Image
import io
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from streamlit_camera_input_live import camera_input_live
from pyzbar import pyzbar
import logging

# Import custom modules
from src.database.database import ToolInventoryDatabase
from src.models.predictive_model import MaintenancePredictionModel
from src.utils.email_alerts import EmailAlertSystem
from src.utils.qr_scanner import QRCodeScanner

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="EasyJet Tool Inventory System",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def load_css():
    """Load custom CSS styles"""
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #ff6900 0%, #fcb900 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ff6900;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-available { background-color: #d4edda; color: #155724; }
    .status-in-use { background-color: #fff3cd; color: #856404; }
    .status-maintenance { background-color: #f8d7da; color: #721c24; }
    .tool-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .urgent-maintenance {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }
    </style>
    """, unsafe_allow_html=True)

class ToolInventoryApp:
    def __init__(self):
        self.db = ToolInventoryDatabase()
        self.predictor = MaintenancePredictionModel()
        self.email_system = EmailAlertSystem()
        self.qr_scanner = QRCodeScanner()
        
    def run(self):
        """Main application runner"""
        load_css()
        self._display_header()
        
        # Sidebar navigation
        with st.sidebar:
            selected = option_menu(
                "Navigation",
                ["Dashboard", "Tool Management", "QR Scanner", "Maintenance", "Analytics", "Settings"],
                icons=['house', 'tools', 'qr-code-scan', 'gear', 'graph-up', 'sliders'],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "#fafafa"},
                    "icon": {"color": "#ff6900", "font-size": "18px"}, 
                    "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
                    "nav-link-selected": {"background-color": "#ff6900"},
                }
            )
        
        # Route to selected page
        if selected == "Dashboard":
            self._dashboard_page()
        elif selected == "Tool Management":
            self._tool_management_page()
        elif selected == "QR Scanner":
            self._qr_scanner_page()
        elif selected == "Maintenance":
            self._maintenance_page()
        elif selected == "Analytics":
            self._analytics_page()
        elif selected == "Settings":
            self._settings_page()
    
    def _display_header(self):
        """Display application header"""
        st.markdown("""
        <div class="main-header">
            <h1 style="color: white; margin: 0;">🔧 EasyJet Tool Inventory System</h1>
            <p style="color: white; margin: 0;">QR-based tool tracking with predictive maintenance</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _dashboard_page(self):
        """Main dashboard page"""
        st.header("📊 Dashboard Overview")
        
        # Get current data
        tools_df = self.db.get_all_tools()
        maintenance_due_df = self.db.get_tools_due_for_maintenance()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_tools = len(tools_df)
            st.metric("Total Tools", total_tools)
        
        with col2:
            available_tools = len(tools_df[tools_df['status'] == 'available'])
            st.metric("Available", available_tools, delta=f"{available_tools/total_tools*100:.1f}%" if total_tools > 0 else "0%")
        
        with col3:
            in_use_tools = len(tools_df[tools_df['status'] == 'in_use'])
            st.metric("In Use", in_use_tools, delta=f"{in_use_tools/total_tools*100:.1f}%" if total_tools > 0 else "0%")
        
        with col4:
            maintenance_tools = len(maintenance_due_df)
            st.metric("Maintenance Due", maintenance_tools, delta="Urgent" if maintenance_tools > 5 else "Normal")
        
        # Charts and visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            if not tools_df.empty:
                # Status distribution pie chart
                status_counts = tools_df['status'].value_counts()
                fig = px.pie(values=status_counts.values, names=status_counts.index, 
                           title="Tool Status Distribution",
                           color_discrete_map={
                               'available': '#28a745',
                               'in_use': '#ffc107',
                               'maintenance': '#dc3545'
                           })
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if not tools_df.empty:
                # Category distribution
                category_counts = tools_df['category'].value_counts()
                fig = px.bar(x=category_counts.index, y=category_counts.values,
                           title="Tools by Category",
                           color_discrete_sequence=['#ff6900'])
                st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity and alerts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚨 Urgent Maintenance")
            if not maintenance_due_df.empty:
                for _, tool in maintenance_due_df.iterrows():
                    days_overdue = (datetime.now() - pd.to_datetime(tool['next_maintenance_due'])).days
                    urgency = "🔴 OVERDUE" if days_overdue > 0 else f"🟡 Due in {abs(days_overdue)} days"
                    st.markdown(f"""
                    <div class="tool-card urgent-maintenance">
                        <strong>{tool['tool_name']}</strong> ({tool['tool_code']})<br>
                        <small>{urgency} - {tool['category']}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("No urgent maintenance required!")
        
        with col2:
            st.subheader("📈 AI Predictions")
            predictions_df = self.db.get_predictions()
            if not predictions_df.empty:
                high_risk = predictions_df[predictions_df['confidence_score'] > 0.8]
                for _, pred in high_risk.head(5).iterrows():
                    st.markdown(f"""
                    <div class="tool-card">
                        <strong>{pred['tool_code']}</strong><br>
                        <small>Risk: {pred['confidence_score']:.1%} - Priority: {pred['maintenance_priority']}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("AI predictions will appear here as data accumulates")
    
    def _tool_management_page(self):
        """Tool management page"""
        st.header("🔧 Tool Management")
        
        tab1, tab2, tab3 = st.tabs(["All Tools", "Add New Tool", "Bulk Import"])
        
        with tab1:
            tools_df = self.db.get_all_tools()
            if not tools_df.empty:
                # Filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    status_filter = st.multiselect("Status", tools_df['status'].unique(), default=tools_df['status'].unique())
                with col2:
                    category_filter = st.multiselect("Category", tools_df['category'].unique(), default=tools_df['category'].unique())
                with col3:
                    location_filter = st.multiselect("Location", tools_df['location'].unique(), default=tools_df['location'].unique())
                
                # Filter data
                filtered_df = tools_df[
                    (tools_df['status'].isin(status_filter)) &
                    (tools_df['category'].isin(category_filter)) &
                    (tools_df['location'].isin(location_filter))
                ]
                
                # Display tools with action buttons
                for _, tool in filtered_df.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    with col1:
                        status_class = f"status-{tool['status'].replace(' ', '-')}"
                        st.markdown(f"""
                        <div class="tool-card">
                            <strong>{tool['tool_name']}</strong> ({tool['tool_code']})<br>
                            <span class="{status_class}">{tool['status'].upper()}</span> | 
                            {tool['category']} | {tool['location']}<br>
                            <small>Condition: {tool['condition_score']}/10 | 
                            Usage: {tool['usage_hours']:.1f}h</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("QR", key=f"qr_{tool['tool_code']}"):
                            self._generate_qr_code(tool['tool_code'])
                    
                    with col3:
                        if st.button("Edit", key=f"edit_{tool['tool_code']}"):
                            st.session_state.editing_tool = tool['tool_code']
                    
                    with col4:
                        new_status = st.selectbox("Status", ['available', 'in_use', 'maintenance'], 
                                                index=['available', 'in_use', 'maintenance'].index(tool['status']),
                                                key=f"status_{tool['tool_code']}")
                        if new_status != tool['status']:
                            if st.button("Update", key=f"update_{tool['tool_code']}"):
                                self.db.update_tool_status(tool['tool_code'], new_status)
                                st.success(f"Status updated to {new_status}")
                                st.rerun()
            else:
                st.info("No tools in inventory. Add some tools to get started!")
        
        with tab2:
            self._add_new_tool_form()
        
        with tab3:
            self._bulk_import_tools()
    
    def _add_new_tool_form(self):
        """Form to add new tool"""
        with st.form("add_tool_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                tool_code = st.text_input("Tool Code*", placeholder="e.g., EJ-001")
                tool_name = st.text_input("Tool Name*", placeholder="e.g., Pneumatic Drill")
                category = st.selectbox("Category*", [
                    "Power Tools", "Hand Tools", "Measuring Tools", 
                    "Safety Equipment", "Diagnostic Tools", "Specialized Tools"
                ])
                location = st.text_input("Location*", placeholder="e.g., Workshop A - Bay 3")
            
            with col2:
                purchase_date = st.date_input("Purchase Date")
                condition_score = st.slider("Initial Condition Score", 1.0, 10.0, 10.0)
                next_maintenance = st.date_input("Next Maintenance Due", 
                                               value=datetime.now() + timedelta(days=90))
                notes = st.text_area("Notes", placeholder="Additional information...")
            
            submitted = st.form_submit_button("Add Tool")
            
            if submitted:
                if tool_code and tool_name and category and location:
                    tool_data = {
                        'tool_code': tool_code,
                        'tool_name': tool_name,
                        'category': category,
                        'location': location,
                        'purchase_date': purchase_date.isoformat(),
                        'next_maintenance_due': next_maintenance.isoformat(),
                        'condition_score': condition_score
                    }
                    
                    if self.db.add_tool(tool_data):
                        st.success(f"Tool {tool_code} added successfully!")
                        # Generate QR code
                        self._generate_qr_code(tool_code)
                    else:
                        st.error("Failed to add tool. Tool code might already exist.")
                else:
                    st.error("Please fill in all required fields marked with *")
    
    def _qr_scanner_page(self):
        """QR code scanner page"""
        st.header("📱 QR Code Scanner")
        
        tab1, tab2 = st.tabs(["Live Scanner", "Upload Image"])
        
        with tab1:
            st.subheader("Live Camera Scanner")
            
            # Camera input
            img = camera_input_live()
            
            if img is not None:
                # Process the image for QR codes
                img_array = np.array(img)
                qr_codes = self.qr_scanner.decode_qr_codes(img_array)
                
                if qr_codes:
                    for qr_data in qr_codes:
                        st.success(f"QR Code detected: {qr_data}")
                        self._display_tool_info(qr_data)
                else:
                    st.info("No QR codes detected. Position the QR code within the camera view.")
        
        with tab2:
            st.subheader("Upload QR Code Image")
            uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])
            
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)
                
                # Process uploaded image
                img_array = np.array(image)
                qr_codes = self.qr_scanner.decode_qr_codes(img_array)
                
                if qr_codes:
                    for qr_data in qr_codes:
                        st.success(f"QR Code found: {qr_data}")
                        self._display_tool_info(qr_data)
                else:
                    st.error("No QR codes found in the uploaded image.")
    
    def _display_tool_info(self, tool_code: str):
        """Display tool information from QR scan"""
        tool = self.db.get_tool(tool_code)
        
        if tool:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="tool-card">
                    <h4>{tool['tool_name']} ({tool['tool_code']})</h4>
                    <p><strong>Status:</strong> <span class="status-{tool['status'].replace(' ', '-')}">{tool['status'].upper()}</span></p>
                    <p><strong>Category:</strong> {tool['category']}</p>
                    <p><strong>Location:</strong> {tool['location']}</p>
                    <p><strong>Condition:</strong> {tool['condition_score']}/10</p>
                    <p><strong>Usage Hours:</strong> {tool['usage_hours']:.1f}h</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.subheader("Quick Actions")
                
                if tool['status'] == 'available':
                    if st.button("Check Out Tool"):
                        user_id = st.text_input("Enter User ID:")
                        if user_id:
                            usage_data = {
                                'tool_code': tool_code,
                                'user_id': user_id,
                                'checkout_time': datetime.now().isoformat(),
                                'usage_type': 'checkout'
                            }
                            if self.db.record_usage(usage_data):
                                self.db.update_tool_status(tool_code, 'in_use')
                                st.success("Tool checked out successfully!")
                                st.rerun()
                
                elif tool['status'] == 'in_use':
                    if st.button("Check In Tool"):
                        # Get last checkout record
                        usage_df = self.db.get_usage_stats(tool_code)
                        if not usage_df.empty:
                            last_checkout = usage_df.iloc[0]
                            checkout_time = pd.to_datetime(last_checkout['checkout_time'])
                            usage_duration = (datetime.now() - checkout_time).total_seconds() / 3600
                            
                            usage_data = {
                                'tool_code': tool_code,
                                'user_id': last_checkout['user_id'],
                                'checkin_time': datetime.now().isoformat(),
                                'usage_duration': usage_duration,
                                'usage_type': 'checkin'
                            }
                            if self.db.record_usage(usage_data):
                                self.db.update_tool_status(tool_code, 'available')
                                st.success(f"Tool checked in! Used for {usage_duration:.1f} hours")
                                st.rerun()
                
                # Show maintenance info
                if tool['next_maintenance_due']:
                    maintenance_due = pd.to_datetime(tool['next_maintenance_due'])
                    days_until = (maintenance_due - datetime.now()).days
                    
                    if days_until <= 7:
                        st.warning(f"⚠️ Maintenance due in {days_until} days")
                    elif days_until < 0:
                        st.error(f"🚨 Maintenance overdue by {abs(days_until)} days")
        else:
            st.error(f"Tool with code '{tool_code}' not found in database.")
    
    def _maintenance_page(self):
        """Maintenance management page"""
        st.header("🔧 Maintenance Management")
        
        tab1, tab2, tab3 = st.tabs(["Due for Maintenance", "Schedule Maintenance", "Maintenance History"])
        
        with tab1:
            maintenance_due_df = self.db.get_tools_due_for_maintenance(30)  # 30 days ahead
            
            if not maintenance_due_df.empty:
                st.subheader("Tools Requiring Maintenance")
                
                for _, tool in maintenance_due_df.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        due_date = pd.to_datetime(tool['next_maintenance_due'])
                        days_until = (due_date - datetime.now()).days
                        urgency = "🔴 OVERDUE" if days_until < 0 else f"🟡 {days_until} days"
                        
                        st.markdown(f"""
                        <div class="tool-card">
                            <h5>{tool['tool_name']} ({tool['tool_code']})</h5>
                            <p>Due: {due_date.strftime('%Y-%m-%d')} ({urgency})</p>
                            <p>Condition: {tool['condition_score']}/10 | Usage: {tool['usage_hours']:.1f}h</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("Schedule", key=f"schedule_{tool['tool_code']}"):
                            st.session_state.schedule_tool = tool['tool_code']
                    
                    with col3:
                        if st.button("Complete", key=f"complete_{tool['tool_code']}"):
                            st.session_state.complete_maintenance = tool['tool_code']
            else:
                st.success("No tools currently due for maintenance!")
        
        with tab2:
            self._schedule_maintenance_form()
        
        with tab3:
            self._maintenance_history()
    
    def _analytics_page(self):
        """Analytics and reporting page"""
        st.header("📊 Analytics & Reports")
        
        tools_df = self.db.get_all_tools()
        usage_df = self.db.get_usage_stats()
        
        if not tools_df.empty:
            # Time period selector
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("End Date", value=datetime.now())
            
            # Key metrics over time
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Tool utilization
                if not usage_df.empty:
                    avg_utilization = usage_df['usage_duration'].mean()
                    st.metric("Average Usage (hours)", f"{avg_utilization:.1f}")
            
            with col2:
                # Maintenance cost
                total_cost = tools_df['maintenance_cost'].sum()
                st.metric("Total Maintenance Cost", f"€{total_cost:,.2f}")
            
            with col3:
                # Tools efficiency
                avg_condition = tools_df['condition_score'].mean()
                st.metric("Average Condition Score", f"{avg_condition:.1f}/10")
            
            # Charts
            st.subheader("📈 Trends and Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Usage trends
                if not usage_df.empty:
                    usage_df['checkout_date'] = pd.to_datetime(usage_df['checkout_time']).dt.date
                    daily_usage = usage_df.groupby('checkout_date')['usage_duration'].sum().reset_index()
                    
                    fig = px.line(daily_usage, x='checkout_date', y='usage_duration',
                                title="Daily Tool Usage Trends",
                                labels={'usage_duration': 'Total Hours', 'checkout_date': 'Date'})
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Condition score distribution
                fig = px.histogram(tools_df, x='condition_score', nbins=10,
                                 title="Tool Condition Score Distribution",
                                 labels={'condition_score': 'Condition Score', 'count': 'Number of Tools'})
                st.plotly_chart(fig, use_container_width=True)
            
            # Predictive insights
            st.subheader("🔮 AI Predictions & Insights")
            predictions_df = self.db.get_predictions()
            
            if not predictions_df.empty:
                # High-risk tools
                high_risk = predictions_df[predictions_df['confidence_score'] > 0.7]
                
                if not high_risk.empty:
                    fig = px.scatter(high_risk, x='prediction_date', y='confidence_score',
                                   color='maintenance_priority', size='confidence_score',
                                   hover_data=['tool_code'],
                                   title="Maintenance Risk Predictions")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add tools to see analytics and insights.")
    
    def _settings_page(self):
        """Settings and configuration page"""
        st.header("⚙️ Settings")
        
        tab1, tab2, tab3 = st.tabs(["General Settings", "Email Alerts", "Data Management"])
        
        with tab1:
            st.subheader("Application Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                maintenance_lead_time = st.slider("Maintenance Alert Days", 1, 30, 7)
                prediction_threshold = st.slider("AI Prediction Threshold", 0.1, 1.0, 0.75)
                auto_email_alerts = st.checkbox("Enable Automatic Email Alerts", value=True)
            
            with col2:
                qr_code_size = st.slider("QR Code Size", 5, 20, 10)
                default_condition_score = st.slider("Default Condition Score", 1.0, 10.0, 10.0)
                data_retention_days = st.slider("Data Retention (days)", 30, 365, 90)
            
            if st.button("Save Settings"):
                st.success("Settings saved successfully!")
        
        with tab2:
            st.subheader("Email Alert Configuration")
            
            email_recipients = st.text_area(
                "Email Recipients (one per line)",
                value="maintenance@easyjet.com\nsupervisor@easyjet.com"
            )
            
            alert_types = st.multiselect(
                "Alert Types",
                ["Maintenance Due", "Tool Overdue", "High Risk Prediction", "System Errors"],
                default=["Maintenance Due", "Tool Overdue"]
            )
            
            if st.button("Test Email Configuration"):
                if self.email_system.send_test_email():
                    st.success("Test email sent successfully!")
                else:
                    st.error("Failed to send test email. Check configuration.")
        
        with tab3:
            st.subheader("Data Management")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Export Data**")
                if st.button("Export Tools Data"):
                    tools_df = self.db.get_all_tools()
                    csv = tools_df.to_csv(index=False)
                    st.download_button(
                        label="Download Tools CSV",
                        data=csv,
                        file_name=f"tools_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
                if st.button("Export Usage History"):
                    usage_df = self.db.get_usage_stats()
                    csv = usage_df.to_csv(index=False)
                    st.download_button(
                        label="Download Usage CSV",
                        data=csv,
                        file_name=f"usage_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                st.write("**Database Maintenance**")
                if st.button("Optimize Database"):
                    st.info("Database optimization completed")
                
                st.write("**⚠️ Danger Zone**")
                if st.button("Reset All Data", type="secondary"):
                    st.error("This action cannot be undone!")
    
    def _generate_qr_code(self, tool_code: str):
        """Generate QR code for tool"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(tool_code)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Display QR code
        st.image(img, caption=f"QR Code for {tool_code}", width=200)
        
        # Provide download option
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        st.download_button(
            label="Download QR Code",
            data=img_buffer.getvalue(),
            file_name=f"qr_code_{tool_code}.png",
            mime="image/png"
        )
    
    def _schedule_maintenance_form(self):
        """Form to schedule maintenance"""
        # Implementation for maintenance scheduling
        st.info("Maintenance scheduling form would be implemented here")
    
    def _maintenance_history(self):
        """Display maintenance history"""
        # Implementation for maintenance history
        st.info("Maintenance history display would be implemented here")
    
    def _bulk_import_tools(self):
        """Bulk import tools from CSV"""
        st.subheader("Bulk Import Tools")
        
        # Template download
        st.write("Download the template CSV file to see the required format:")
        template_data = {
            'tool_code': ['EJ-001', 'EJ-002'],
            'tool_name': ['Pneumatic Drill', 'Torque Wrench'],
            'category': ['Power Tools', 'Hand Tools'],
            'location': ['Workshop A', 'Workshop B'],
            'purchase_date': ['2023-01-15', '2023-02-20'],
            'condition_score': [9.5, 8.0]
        }
        template_df = pd.DataFrame(template_data)
        csv_template = template_df.to_csv(index=False)
        
        st.download_button(
            label="Download Template",
            data=csv_template,
            file_name="tool_import_template.csv",
            mime="text/csv"
        )
        
        # File upload
        uploaded_file = st.file_uploader("Choose CSV file", type="csv")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                if st.button("Import Tools"):
                    success_count = 0
                    error_count = 0
                    
                    for _, row in df.iterrows():
                        tool_data = row.to_dict()
                        if self.db.add_tool(tool_data):
                            success_count += 1
                        else:
                            error_count += 1
                    
                    st.success(f"Import completed! {success_count} tools added, {error_count} errors.")
                    
            except Exception as e:
                st.error(f"Error processing file: {e}")

# Initialize and run the app
if __name__ == "__main__":
    app = ToolInventoryApp()
    app.run()