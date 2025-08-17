# 🔧 EasyJet Tool Inventory System

QR-code based tool inventory and predictive-AI dashboard for EasyJet Engineering Malta – Streamlit UI + email alerts.

## 🚀 Features

### Core Functionality
- **QR Code Integration**: Generate and scan QR codes for instant tool identification
- **Real-time Dashboard**: Interactive Streamlit web interface with live tool status
- **Predictive AI**: Machine learning-powered maintenance prediction system
- **Email Alerts**: Automated notifications for maintenance due and high-risk tools
- **Inventory Management**: Complete tool lifecycle tracking and management

### Key Capabilities
- 📱 **Mobile-Ready QR Scanning**: Camera-based QR code scanning
- 🤖 **AI-Powered Predictions**: Predictive maintenance using Random Forest and Isolation Forest
- 📧 **Smart Alerts**: Automated email notifications for maintenance and risks
- 📊 **Analytics Dashboard**: Comprehensive reporting and visualization
- 🔒 **Enterprise Ready**: Docker support with production-ready configuration
- 💾 **SQLite Database**: Lightweight, serverless database for tool data

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EasyJet Tool Inventory System               │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Streamlit)                                           │
│  ├── Dashboard       ├── QR Scanner      ├── Analytics         │
│  ├── Tool Management ├── Maintenance     ├── Settings          │
├─────────────────────────────────────────────────────────────────┤
│  Core Services                                                  │
│  ├── Database Layer (SQLite)                                   │
│  ├── Predictive AI (ML Models)                                 │
│  ├── Email System (SMTP)                                       │
│  └── QR Code Management                                        │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Installation

### Prerequisites
- Python 3.11+
- Docker (optional)
- Camera access for QR scanning
- SMTP server access for email alerts

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/Gbun420/easyjet-tool-inventory.git
cd easyjet-tool-inventory
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the application**
```bash
# Option 1: Direct Streamlit
streamlit run app.py

# Option 2: Production runner (includes background tasks)
python run_app.py

# Option 3: Docker
docker-compose up -d
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t easyjet-tool-inventory .
docker run -p 8501:8501 -v ./data:/app/data easyjet-tool-inventory
```

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@easyjet.com
EMAIL_PASSWORD=your-app-password
NOTIFICATION_EMAILS=maintenance@easyjet.com,supervisor@easyjet.com

# Database Configuration
DATABASE_PATH=data/tool_inventory.db

# Application Configuration
APP_TITLE=EasyJet Tool Inventory System
COMPANY_LOGO=static/images/easyjet_logo.png
DEBUG_MODE=False

# Predictive AI Configuration
MODEL_UPDATE_INTERVAL=24  # hours
PREDICTION_THRESHOLD=0.75
MAINTENANCE_LEAD_TIME=7  # days

# QR Code Configuration
QR_CODE_SIZE=10
QR_CODE_BORDER=4
```

## 📊 Usage Guide

### 1. Tool Management
- **Add Tools**: Use the Tool Management tab to add new tools to inventory
- **Generate QR Codes**: Automatically generate QR codes for each tool
- **Update Status**: Change tool status (available, in_use, maintenance)
- **Bulk Import**: Import multiple tools from CSV files

### 2. QR Code Scanning
- **Live Scanner**: Use camera to scan QR codes in real-time
- **Upload Images**: Upload QR code images for processing
- **Quick Actions**: Check in/out tools directly from scan results

### 3. Maintenance Tracking
- **Scheduled Maintenance**: View tools due for maintenance
- **AI Predictions**: See predictive maintenance recommendations
- **Maintenance History**: Track all maintenance activities
- **Cost Tracking**: Monitor maintenance costs and efficiency

### 4. Analytics & Reporting
- **Dashboard Overview**: Real-time metrics and status visualization
- **Usage Statistics**: Tool utilization patterns and trends
- **Condition Monitoring**: Track tool condition scores over time
- **Predictive Insights**: AI-powered maintenance forecasting

## 🤖 AI Predictive Maintenance

The system uses advanced machine learning algorithms to predict maintenance needs:

### Models Used
- **Random Forest Regressor**: Predicts condition degradation
- **Isolation Forest**: Detects anomalous usage patterns
- **Feature Engineering**: 15+ engineered features including usage intensity, maintenance frequency, and condition trends

### Prediction Features
- Tool condition score and usage hours
- Days since purchase and last maintenance
- Usage intensity and patterns
- Maintenance cost and frequency
- Category and location factors

### Risk Assessment
- **Critical (>90%)**: Immediate maintenance required
- **High (80-90%)**: Schedule within 3 days
- **Medium (60-80%)**: Plan within 1 week
- **Low (<60%)**: Continue monitoring

## 📧 Email Alert System

### Alert Types
1. **Maintenance Due**: Tools requiring scheduled maintenance
2. **High Risk**: AI-predicted high failure risk tools
3. **Daily Summary**: Comprehensive daily system overview
4. **System Alerts**: Critical system events and errors

### Email Templates
- HTML-formatted professional emails
- EasyJet branding and styling
- Detailed tool information and recommendations
- Actionable insights and next steps

## 🗄️ Database Schema

### Tables
- **tools**: Main tool inventory with condition and usage data
- **usage_history**: Tool checkout/checkin records
- **maintenance_history**: Maintenance activities and costs
- **predictions**: AI prediction results and confidence scores

### Key Fields
```sql
tools:
- tool_code (PRIMARY KEY)
- tool_name, category, location
- condition_score, usage_hours
- maintenance dates and status

usage_history:
- tool_code, user_id
- checkout/checkin timestamps
- usage duration and type

maintenance_history:
- tool_code, maintenance_date
- maintenance_type, cost
- condition before/after

predictions:
- tool_code, prediction_date
- confidence_score, priority
- predicted_failure_date
```

## 📁 Project Structure

```
easyjet-tool-inventory/
├── app.py                      # Main Streamlit application
├── run_app.py                  # Production runner with scheduled tasks
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose setup
├── .env.example                # Environment configuration template
├── src/
│   ├── database/
│   │   └── database.py         # Database operations
│   ├── models/
│   │   └── predictive_model.py # AI/ML prediction models
│   └── utils/
│       ├── email_alerts.py     # Email notification system
│       └── qr_scanner.py       # QR code scanning utilities
├── data/                       # SQLite database storage
├── models/                     # Trained ML model files
├── static/                     # Static assets (CSS, JS, images)
├── templates/                  # Email templates
├── tests/                      # Unit tests
└── docs/                       # Documentation
```

## 🔧 API Documentation

### Database API
```python
from src.database.database import ToolInventoryDatabase

db = ToolInventoryDatabase()

# Add new tool
tool_data = {
    'tool_code': 'EJ-001',
    'tool_name': 'Pneumatic Drill',
    'category': 'Power Tools',
    'location': 'Workshop A'
}
db.add_tool(tool_data)

# Get tool information
tool = db.get_tool('EJ-001')

# Update tool status
db.update_tool_status('EJ-001', 'in_use')

# Record usage
usage_data = {
    'tool_code': 'EJ-001',
    'user_id': 'tech001',
    'checkout_time': '2024-01-15 09:00:00'
}
db.record_usage(usage_data)
```

### Predictive Model API
```python
from src.models.predictive_model import MaintenancePredictionModel

predictor = MaintenancePredictionModel()

# Train model with data
tools_df = db.get_all_tools()
usage_df = db.get_usage_stats()
predictor.train_models(predictor.prepare_features(tools_df, usage_df, pd.DataFrame()))

# Generate predictions
predictions = predictor.predict_maintenance_needs(tools_df)
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_database.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Test Structure
- Unit tests for all core components
- Integration tests for API endpoints
- Mock data for testing scenarios
- Performance benchmarks

## 🚀 Deployment

### Production Deployment

1. **Server Setup**
```bash
# Install Docker and Docker Compose
sudo apt update
sudo apt install docker.io docker-compose

# Clone repository
git clone https://github.com/Gbun420/easyjet-tool-inventory.git
cd easyjet-tool-inventory
```

2. **Configuration**
```bash
# Set up environment
cp .env.example .env
nano .env  # Configure your settings

# Set permissions
chmod +x run_app.py
```

3. **Deploy**
```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f easyjet-tool-inventory
```

### Health Monitoring
- Built-in health checks in Docker configuration
- System logs available through Docker Compose
- Automatic restart on failure
- Resource usage monitoring

## 📱 Mobile Access

The system is fully responsive and optimized for mobile devices:
- Touch-friendly QR code scanning
- Responsive dashboard layout
- Mobile camera integration
- Offline QR code generation

## 🔐 Security Features

- Input validation and sanitization
- SQL injection protection
- Secure email configuration
- Docker container isolation
- Environment variable security
- Database backup automation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run tests before committing
python -m pytest
```

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Contact the EasyJet Engineering Malta team
- Check the documentation in the `/docs` folder

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 About EasyJet Engineering Malta

This system was designed specifically for EasyJet's engineering operations in Malta, providing advanced tool inventory management with predictive maintenance capabilities to ensure optimal aircraft maintenance efficiency and safety.

---

**Built with ❤️ for EasyJet Engineering Malta**
