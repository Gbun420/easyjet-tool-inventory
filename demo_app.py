#!/usr/bin/env python3
"""
Demo version of EasyJet Tool Inventory System
Simplified version showcasing core functionality without heavy dependencies
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.parse
import socketserver

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Simple HTTP server to demonstrate the system
class ToolInventoryHandler(SimpleHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        # Initialize database
        sys.path.append('src')
        from database.database import ToolInventoryDatabase
        self.db = ToolInventoryDatabase()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.send_dashboard()
        elif self.path == '/api/tools':
            self.send_tools_api()
        elif self.path == '/api/status':
            self.send_status_api()
        elif self.path.startswith('/qr/'):
            self.send_qr_code()
        else:
            super().do_GET()
    
    def send_dashboard(self):
        """Send main dashboard HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>🔧 EasyJet Tool Inventory System</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #ff6900 0%, #e55a00 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .header p {{
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .metric {{
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 5px solid #ff6900;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #ff6900;
            margin-bottom: 0.5rem;
        }}
        .metric-label {{
            color: #666;
            font-weight: 500;
        }}
        .section {{
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .section h3 {{
            color: #ff6900;
            margin-top: 0;
        }}
        .tool-item {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            background: #f9f9f9;
        }}
        .status-available {{ background: #d4edda; color: #155724; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; }}
        .status-in-use {{ background: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; }}
        .status-maintenance {{ background: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; }}
        .refresh-btn {{
            background: #ff6900;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
        }}
        .refresh-btn:hover {{
            background: #e55a00;
        }}
        .demo-note {{
            background: #e7f3ff;
            border: 1px solid #b3d9ff;
            color: #0066cc;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }}
        .footer {{
            text-align: center;
            margin-top: 2rem;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔧 EasyJet Tool Inventory System</h1>
        <p>QR-based tool tracking with predictive maintenance</p>
    </div>

    <div class="demo-note">
        <strong>📋 Demo Version:</strong> This is a simplified demonstration of the EasyJet Tool Inventory System. 
        The full version includes Streamlit UI, QR code scanning, AI predictions, and email alerts.
    </div>

    <div class="metrics" id="metrics">
        <div class="metric">
            <div class="metric-value" id="total-tools">-</div>
            <div class="metric-label">Total Tools</div>
        </div>
        <div class="metric">
            <div class="metric-value" id="available-tools">-</div>
            <div class="metric-label">Available</div>
        </div>
        <div class="metric">
            <div class="metric-value" id="in-use-tools">-</div>
            <div class="metric-label">In Use</div>
        </div>
        <div class="metric">
            <div class="metric-value" id="maintenance-due">-</div>
            <div class="metric-label">Maintenance Due</div>
        </div>
    </div>

    <div class="section">
        <h3>🛠️ Tool Inventory</h3>
        <button class="refresh-btn" onclick="loadData()">🔄 Refresh Data</button>
        <div id="tools-list">
            <p>Loading tools...</p>
        </div>
    </div>

    <div class="section">
        <h3>🚀 System Features</h3>
        <div class="tool-item">
            <h4>📱 QR Code Integration</h4>
            <p>Generate and scan QR codes for instant tool identification. Each tool gets a unique QR code for easy tracking.</p>
        </div>
        <div class="tool-item">
            <h4>🤖 AI-Powered Predictions</h4>
            <p>Machine learning algorithms predict maintenance needs using Random Forest and Isolation Forest models.</p>
        </div>
        <div class="tool-item">
            <h4>📧 Smart Email Alerts</h4>
            <p>Automated notifications for maintenance due dates, high-risk tools, and daily summaries.</p>
        </div>
        <div class="tool-item">
            <h4>📊 Real-time Analytics</h4>
            <p>Comprehensive dashboard with usage statistics, condition monitoring, and predictive insights.</p>
        </div>
    </div>

    <div class="footer">
        <p><strong>Built for EasyJet Engineering Malta</strong><br>
        Advanced tool inventory management with predictive maintenance</p>
        <p>Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <script>
        function loadData() {{
            fetch('/api/tools')
                .then(response => response.json())
                .then(data => {{
                    updateMetrics(data);
                    updateToolsList(data.tools);
                }})
                .catch(error => {{
                    console.error('Error loading data:', error);
                    document.getElementById('tools-list').innerHTML = 
                        '<p style="color: red;">Error loading tools data</p>';
                }});
        }}

        function updateMetrics(data) {{
            document.getElementById('total-tools').textContent = data.total;
            document.getElementById('available-tools').textContent = data.available;
            document.getElementById('in-use-tools').textContent = data.in_use;
            document.getElementById('maintenance-due').textContent = data.maintenance_due;
        }}

        function updateToolsList(tools) {{
            const toolsList = document.getElementById('tools-list');
            
            if (tools.length === 0) {{
                toolsList.innerHTML = '<p>No tools in inventory.</p>';
                return;
            }}

            let html = '';
            tools.forEach(tool => {{
                const statusClass = 'status-' + tool.status.replace(' ', '-');
                html += `
                    <div class="tool-item">
                        <h4>${{tool.tool_name}} (${{tool.tool_code}})</h4>
                        <p>
                            <span class="${{statusClass}}">${{tool.status.toUpperCase()}}</span> | 
                            ${{tool.category}} | ${{tool.location}}<br>
                            <small>Condition: ${{tool.condition_score}}/10 | 
                            Usage: ${{tool.usage_hours}}h</small>
                        </p>
                    </div>
                `;
            }});
            
            toolsList.innerHTML = html;
        }}

        // Load data on page load
        loadData();
        
        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_tools_api(self):
        """Send tools data as JSON API"""
        try:
            tools_df = self.db.get_all_tools()
            
            tools_data = []
            for _, tool in tools_df.iterrows():
                tools_data.append({
                    'tool_code': tool['tool_code'],
                    'tool_name': tool['tool_name'],
                    'category': tool['category'],
                    'location': tool['location'],
                    'status': tool['status'],
                    'condition_score': tool['condition_score'],
                    'usage_hours': tool['usage_hours']
                })
            
            # Calculate metrics
            total = len(tools_data)
            available = len([t for t in tools_data if t['status'] == 'available'])
            in_use = len([t for t in tools_data if t['status'] == 'in_use'])
            maintenance = len([t for t in tools_data if t['status'] == 'maintenance'])
            
            response = {
                'total': total,
                'available': available,
                'in_use': in_use,
                'maintenance_due': maintenance,
                'tools': tools_data
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def send_status_api(self):
        """Send system status"""
        status = {
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(status).encode())

def main():
    """Run the demo server"""
    port = 8501
    
    print(f"🔧 Starting EasyJet Tool Inventory Demo Server...")
    print(f"🌐 Server will be available at: http://localhost:{port}")
    print(f"📊 Dashboard: http://localhost:{port}/")
    print(f"🔌 API: http://localhost:{port}/api/tools")
    
    try:
        with socketserver.TCPServer(("", port), ToolInventoryHandler) as httpd:
            print(f"✅ Server started successfully on port {port}")
            print(f"🚀 Press Ctrl+C to stop the server")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()