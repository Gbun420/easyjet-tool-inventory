# EasyJet Engineering Tool Inventory & Predictive AI System

This project is a QR code-based tool inventory and predictive AI system for EasyJet Engineering Malta.

## Features

- **QR Code Generation**: Generate unique QR codes for each tool box.
- **Inventory Management**: Track tool check-in/check-out status, location, and calibration dates.
- **Predictive AI**: Forecast tool usage and identify high-demand tools.
- **Alerts**: Send email alerts for important events (e.g., calibration due, missing tools).
- **Streamlit Dashboard**: A professional and intuitive web-based UI for managing the inventory.

## Project Structure

```
.
├── data/               # Stores the inventory CSV file
│   └── inventory.csv
├── models/             # Stores the trained machine learning model
│   └── predictive_model.pkl
├── dashboards/         # Contains the Streamlit dashboard code
│   └── main_dashboard.py
├── alerts/             # Handles email alerts
│   └── email_alerts.py
├── scripts/            # Contains various helper scripts
│   ├── qr_code_generator.py
│   ├── inventory_management.py
│   └── scanner_interface.py
├── qr_codes/           # Stores the generated QR code images
├── .gitignore          # Specifies files to be ignored by Git
└── README.md           # This file
```

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install the required Python libraries:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Email Alerts (Optional):**
    - Open `alerts/email_alerts.py`.
    - Replace the placeholder values for `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_SENDER`, `EMAIL_PASSWORD`, and `EMAIL_RECIPIENT` with your actual email credentials.
    - **Note:** It is highly recommended to use an "app password" for your email account for security reasons.

## How to Run

1.  **Generate QR Codes:**
    - Run the following command to generate QR codes for all the tools listed in `data/inventory.csv`.
    - The QR codes will be saved in the `qr_codes/` directory.
    ```bash
    python3 scripts/qr_code_generator.py
    ```

2.  **Train the Predictive Model:**
    - Run the following command to train the machine learning model.
    - The trained model will be saved as `models/predictive_model.pkl`.
    ```bash
    python3 models/predictive_model.py
    ```

3.  **Run the Streamlit Dashboard:**
    - Start the Streamlit web server by running the following command:
    ```bash
    streamlit run dashboards/main_dashboard.py
    ```
    - Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`).

4.  **Simulate QR Code Scanning:**
    - Run the interactive scanner simulation script:
    ```bash
    python3 scripts/scanner_interface.py
    ```

5.  **Check for Alerts:**
    - To manually trigger the alert-checking process, run:
    ```bash
    python3 alerts/email_alerts.py
    ```
