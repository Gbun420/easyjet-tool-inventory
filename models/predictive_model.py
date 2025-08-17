import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import joblib
import os

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
DATA_FILE = os.path.join(PROJECT_ROOT, 'data', 'inventory.csv')
MODEL_FILE = os.path.join(MODELS_DIR, 'predictive_model.pkl')

# --- Ensure Models Directory Exists ---
os.makedirs(MODELS_DIR, exist_ok=True)

def train_predictive_model():
    """
    Trains a machine learning model to predict tool usage frequency.
    The model is saved to a .pkl file.
    """
    try:
        # Load data
        df = pd.read_csv(DATA_FILE)

        # --- Feature Engineering ---
        # Convert date columns to datetime objects
        df['Last_Calibration'] = pd.to_datetime(df['Last_Calibration'])
        df['Next_Maintenance'] = pd.to_datetime(df['Next_Maintenance'])

        # Create features from dates (e.g., days since last calibration)
        df['days_since_calibration'] = (pd.to_datetime('today') - df['Last_Calibration']).dt.days
        df['days_to_maintenance'] = (df['Next_Maintenance'] - pd.to_datetime('today')).dt.days

        # Convert categorical variables to numerical
        df_dummies = pd.get_dummies(df, columns=['Location', 'Checked_Out_By'], drop_first=True)

        # Define features (X) and target (y)
        features = [
            'days_since_calibration', 'days_to_maintenance',
        ] + [col for col in df_dummies.columns if 'Location_' in col or 'Checked_Out_By_' in col]
        target = 'Usage_Frequency'

        X = df_dummies[features]
        y = df_dummies[target]

        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # --- Model Training ---
        # Initialize and train the model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # --- Model Evaluation ---
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        print(f"Model Mean Squared Error: {mse:.2f}")

        # --- Save the Model and Columns ---
        joblib.dump(model, MODEL_FILE)
        joblib.dump(X.columns.tolist(), f"{MODEL_FILE}.columns")
        print(f"Model saved successfully to {MODEL_FILE}")

    except FileNotFoundError:
        print(f"Error: The data file was not found at {DATA_FILE}")
    except Exception as e:
        print(f"An error occurred during model training: {e}")

def predict_usage(tool_data):
    """
    Predicts the usage frequency for a given tool.

    Args:
        tool_data (dict): A dictionary of tool features.

    Returns:
        float: The predicted usage frequency.
    """
    try:
        # Load the trained model and columns
        model = joblib.load(MODEL_FILE)
        model_columns = joblib.load(f"{MODEL_FILE}.columns")

        # Create a DataFrame from the input data
        df = pd.DataFrame([tool_data])

        # --- Feature Engineering (must match training) ---
        df['Last_Calibration'] = pd.to_datetime(df['Last_Calibration'])
        df['Next_Maintenance'] = pd.to_datetime(df['Next_Maintenance'])
        df['days_since_calibration'] = (pd.to_datetime('today') - df['Last_Calibration']).dt.days
        df['days_to_maintenance'] = (df['Next_Maintenance'] - pd.to_datetime('today')).dt.days
        df = pd.get_dummies(df, columns=['Location', 'Checked_Out_By'])

        # Align columns with the training data
        df = df.reindex(columns=model_columns, fill_value=0)

        # Make prediction
        prediction = model.predict(df)
        return prediction[0]

    except FileNotFoundError:
        print(f"Error: The model file was not found at {MODEL_FILE}")
        return None
    except Exception as e:
        print(f"An error occurred during prediction: {e}")
        return None

if __name__ == '__main__':
    print("--- Training Predictive Model ---")
    train_predictive_model()

    # --- Example Prediction ---
    print("\n--- Example Usage Prediction ---")
    sample_tool = {
        'Tool_ID': 'T011',
        'Box_Name': 'Box-F-01',
        'Location': 'Hangar 1',
        'Checked_Out_By': 'None',
        'Last_Calibration': '2025-08-01',
        'Next_Maintenance': '2026-02-01',
        'Usage_Frequency': 0  # Placeholder
    }

    # Get a prediction for the sample tool
    predicted_usage = predict_usage(sample_tool)
    if predicted_usage is not None:
        print(f"Predicted usage for new tool: {predicted_usage:.2f}")