"""
Predictive Maintenance AI Model for EasyJet Tool Inventory System
Uses machine learning to predict maintenance needs and tool failures
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os

class MaintenancePredictionModel:
    """AI model for predicting maintenance needs and tool failures"""
    
    def __init__(self, model_path: str = "models/"):
        self.model_path = model_path
        self.regression_model = None
        self.anomaly_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.model_version = "1.0"
        self._ensure_model_directory()
        self._load_models()
        
    def _ensure_model_directory(self):
        """Ensure model directory exists"""
        os.makedirs(self.model_path, exist_ok=True)
        
    def prepare_features(self, tools_df: pd.DataFrame, usage_df: pd.DataFrame, 
                        maintenance_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for model training and prediction"""
        try:
            # Merge all data sources
            features_df = tools_df.copy()
            
            # Add usage statistics
            if not usage_df.empty:
                usage_stats = usage_df.groupby('tool_code').agg({
                    'usage_duration': ['sum', 'mean', 'count'],
                    'checkout_time': 'count'
                }).round(2)
                
                usage_stats.columns = [
                    'total_usage_hours', 'avg_usage_hours', 'usage_count', 'checkout_count'
                ]
                usage_stats = usage_stats.reset_index()
                
                features_df = features_df.merge(usage_stats, on='tool_code', how='left')
            else:
                features_df['total_usage_hours'] = 0
                features_df['avg_usage_hours'] = 0
                features_df['usage_count'] = 0
                features_df['checkout_count'] = 0
            
            # Add maintenance statistics
            if not maintenance_df.empty:
                maintenance_stats = maintenance_df.groupby('tool_code').agg({
                    'cost': ['sum', 'mean', 'count'],
                    'maintenance_date': 'max'
                }).round(2)
                
                maintenance_stats.columns = [
                    'total_maintenance_cost', 'avg_maintenance_cost', 'maintenance_count', 'last_maintenance'
                ]
                maintenance_stats = maintenance_stats.reset_index()
                
                features_df = features_df.merge(maintenance_stats, on='tool_code', how='left')
            else:
                features_df['total_maintenance_cost'] = 0
                features_df['avg_maintenance_cost'] = 0
                features_df['maintenance_count'] = 0
                features_df['last_maintenance'] = None
            
            # Calculate derived features
            features_df['days_since_purchase'] = (
                datetime.now() - pd.to_datetime(features_df['purchase_date'], errors='coerce')
            ).dt.days
            
            features_df['days_since_last_maintenance'] = (
                datetime.now() - pd.to_datetime(features_df['last_maintenance'], errors='coerce')
            ).dt.days
            
            features_df['usage_intensity'] = (
                features_df['total_usage_hours'] / (features_df['days_since_purchase'] + 1)
            )
            
            features_df['maintenance_frequency'] = (
                features_df['maintenance_count'] / (features_df['days_since_purchase'] + 1) * 365
            )
            
            features_df['cost_per_hour'] = (
                features_df['total_maintenance_cost'] / (features_df['total_usage_hours'] + 1)
            )
            
            # Fill missing values
            numeric_columns = features_df.select_dtypes(include=[np.number]).columns
            features_df[numeric_columns] = features_df[numeric_columns].fillna(0)
            
            return features_df
            
        except Exception as e:
            logging.error(f"Error preparing features: {e}")
            return pd.DataFrame()
    
    def _encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features"""
        categorical_columns = ['category', 'location', 'status']
        
        for col in categorical_columns:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    # Handle unseen labels
                    df[f'{col}_encoded'] = df[col].apply(
                        lambda x: self._safe_transform(self.label_encoders[col], str(x))
                    )
        
        return df
    
    def _safe_transform(self, encoder, value):
        """Safely transform value with label encoder"""
        try:
            return encoder.transform([value])[0]
        except ValueError:
            # Return -1 for unseen labels
            return -1
    
    def train_models(self, features_df: pd.DataFrame) -> Dict[str, float]:
        """Train the predictive models"""
        try:
            if features_df.empty:
                logging.warning("No data available for training")
                return {}
            
            # Encode categorical features
            features_df = self._encode_categorical_features(features_df)
            
            # Define feature columns for training
            self.feature_columns = [
                'condition_score', 'usage_hours', 'days_since_purchase',
                'days_since_last_maintenance', 'total_usage_hours', 'avg_usage_hours',
                'usage_count', 'checkout_count', 'total_maintenance_cost',
                'avg_maintenance_cost', 'maintenance_count', 'usage_intensity',
                'maintenance_frequency', 'cost_per_hour', 'category_encoded',
                'location_encoded', 'status_encoded'
            ]
            
            # Filter features that exist in the dataset
            available_features = [col for col in self.feature_columns if col in features_df.columns]
            
            if len(available_features) < 5:
                logging.warning("Insufficient features for training")
                return {}
            
            X = features_df[available_features].fillna(0)
            
            # Create target variables for different prediction tasks
            # 1. Condition degradation prediction
            y_condition = 10 - features_df['condition_score']  # Higher value = more degradation
            
            # 2. Maintenance urgency (days until next maintenance needed)
            y_maintenance_urgency = self._calculate_maintenance_urgency(features_df)
            
            metrics = {}
            
            # Train condition degradation model
            if len(X) > 10:  # Need sufficient data
                X_scaled = self.scaler.fit_transform(X)
                
                # Split data
                X_train, X_test, y_train_cond, y_test_cond = train_test_split(
                    X_scaled, y_condition, test_size=0.2, random_state=42
                )
                
                # Train regression model for condition prediction
                self.regression_model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
                self.regression_model.fit(X_train, y_train_cond)
                
                # Evaluate model
                y_pred_cond = self.regression_model.predict(X_test)
                metrics['condition_rmse'] = np.sqrt(mean_squared_error(y_test_cond, y_pred_cond))
                metrics['condition_r2'] = r2_score(y_test_cond, y_pred_cond)
                
                # Train anomaly detection model
                self.anomaly_model = IsolationForest(
                    contamination=0.1,
                    random_state=42,
                    n_jobs=-1
                )
                self.anomaly_model.fit(X_scaled)
                
                # Save models
                self._save_models()
                
                logging.info(f"Models trained successfully. Metrics: {metrics}")
                
            return metrics
            
        except Exception as e:
            logging.error(f"Error training models: {e}")
            return {}
    
    def _calculate_maintenance_urgency(self, features_df: pd.DataFrame) -> np.ndarray:
        """Calculate maintenance urgency based on multiple factors"""
        urgency_scores = []
        
        for _, row in features_df.iterrows():
            score = 0
            
            # Condition score factor (0-4 points)
            condition_factor = (10 - row['condition_score']) / 2.5
            score += condition_factor
            
            # Usage intensity factor (0-3 points)
            if row['usage_intensity'] > 0:
                usage_factor = min(row['usage_intensity'] * 3, 3)
                score += usage_factor
            
            # Days since last maintenance factor (0-3 points)
            if row['days_since_last_maintenance'] > 0:
                days_factor = min(row['days_since_last_maintenance'] / 30, 3)
                score += days_factor
            
            urgency_scores.append(score)
        
        return np.array(urgency_scores)
    
    def predict_maintenance_needs(self, tools_df: pd.DataFrame) -> List[Dict]:
        """Predict maintenance needs for tools"""
        try:
            if self.regression_model is None:
                logging.warning("Model not trained yet")
                return []
            
            # Encode categorical features
            tools_df = self._encode_categorical_features(tools_df)
            
            # Prepare features
            available_features = [col for col in self.feature_columns if col in tools_df.columns]
            X = tools_df[available_features].fillna(0)
            X_scaled = self.scaler.transform(X)
            
            # Get predictions
            condition_predictions = self.regression_model.predict(X_scaled)
            anomaly_scores = self.anomaly_model.decision_function(X_scaled)
            
            predictions = []
            
            for idx, (_, tool) in enumerate(tools_df.iterrows()):
                # Calculate risk score (0-1)
                condition_risk = min(condition_predictions[idx] / 10, 1.0)
                anomaly_risk = 1 / (1 + np.exp(anomaly_scores[idx]))  # Sigmoid normalization
                
                # Combined risk score
                risk_score = (condition_risk * 0.7 + anomaly_risk * 0.3)
                
                # Determine maintenance priority
                if risk_score > 0.8:
                    priority = "Critical"
                elif risk_score > 0.6:
                    priority = "High"
                elif risk_score > 0.4:
                    priority = "Medium"
                else:
                    priority = "Low"
                
                # Estimate days until maintenance needed
                days_until_maintenance = max(1, int(30 * (1 - risk_score)))
                predicted_failure_date = (datetime.now() + timedelta(days=days_until_maintenance)).date()
                
                prediction = {
                    'tool_code': tool['tool_code'],
                    'prediction_date': datetime.now().date(),
                    'predicted_failure_date': predicted_failure_date,
                    'confidence_score': risk_score,
                    'maintenance_priority': priority,
                    'model_version': self.model_version,
                    'days_until_maintenance': days_until_maintenance,
                    'condition_risk': condition_risk,
                    'anomaly_risk': anomaly_risk
                }
                
                predictions.append(prediction)
            
            # Sort by risk score
            predictions.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            return predictions
            
        except Exception as e:
            logging.error(f"Error making predictions: {e}")
            return []
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the trained model"""
        if self.regression_model is None:
            return {}
        
        try:
            importance_dict = {}
            available_features = [col for col in self.feature_columns 
                                if hasattr(self, 'scaler') and col in range(len(self.regression_model.feature_importances_))]
            
            for i, feature in enumerate(available_features):
                if i < len(self.regression_model.feature_importances_):
                    importance_dict[feature] = float(self.regression_model.feature_importances_[i])
            
            # Sort by importance
            return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            
        except Exception as e:
            logging.error(f"Error getting feature importance: {e}")
            return {}
    
    def _save_models(self):
        """Save trained models to disk"""
        try:
            model_files = {
                'regression_model.joblib': self.regression_model,
                'anomaly_model.joblib': self.anomaly_model,
                'scaler.joblib': self.scaler,
                'label_encoders.joblib': self.label_encoders
            }
            
            for filename, model in model_files.items():
                filepath = os.path.join(self.model_path, filename)
                joblib.dump(model, filepath)
            
            # Save metadata
            metadata = {
                'model_version': self.model_version,
                'feature_columns': self.feature_columns,
                'created_at': datetime.now().isoformat()
            }
            
            metadata_path = os.path.join(self.model_path, 'metadata.joblib')
            joblib.dump(metadata, metadata_path)
            
            logging.info("Models saved successfully")
            
        except Exception as e:
            logging.error(f"Error saving models: {e}")
    
    def _load_models(self):
        """Load trained models from disk"""
        try:
            model_files = [
                'regression_model.joblib',
                'anomaly_model.joblib', 
                'scaler.joblib',
                'label_encoders.joblib'
            ]
            
            # Check if all model files exist
            if not all(os.path.exists(os.path.join(self.model_path, f)) for f in model_files):
                logging.info("No pre-trained models found")
                return
            
            # Load models
            self.regression_model = joblib.load(os.path.join(self.model_path, 'regression_model.joblib'))
            self.anomaly_model = joblib.load(os.path.join(self.model_path, 'anomaly_model.joblib'))
            self.scaler = joblib.load(os.path.join(self.model_path, 'scaler.joblib'))
            self.label_encoders = joblib.load(os.path.join(self.model_path, 'label_encoders.joblib'))
            
            # Load metadata
            metadata_path = os.path.join(self.model_path, 'metadata.joblib')
            if os.path.exists(metadata_path):
                metadata = joblib.load(metadata_path)
                self.feature_columns = metadata.get('feature_columns', [])
                self.model_version = metadata.get('model_version', '1.0')
            
            logging.info(f"Models loaded successfully (version {self.model_version})")
            
        except Exception as e:
            logging.error(f"Error loading models: {e}")
            self.regression_model = None
            self.anomaly_model = None
    
    def retrain_with_new_data(self, tools_df: pd.DataFrame, usage_df: pd.DataFrame, 
                             maintenance_df: pd.DataFrame) -> bool:
        """Retrain models with new data"""
        try:
            # Prepare features
            features_df = self.prepare_features(tools_df, usage_df, maintenance_df)
            
            if features_df.empty:
                logging.warning("No data available for retraining")
                return False
            
            # Train models
            metrics = self.train_models(features_df)
            
            if metrics:
                logging.info("Model retrained successfully")
                return True
            else:
                logging.warning("Model retraining failed")
                return False
                
        except Exception as e:
            logging.error(f"Error retraining models: {e}")
            return False
    
    def generate_maintenance_recommendations(self, predictions: List[Dict]) -> List[Dict]:
        """Generate actionable maintenance recommendations"""
        recommendations = []
        
        for pred in predictions:
            if pred['confidence_score'] > 0.6:
                recommendation = {
                    'tool_code': pred['tool_code'],
                    'priority': pred['maintenance_priority'],
                    'recommended_action': self._get_recommended_action(pred),
                    'estimated_cost': self._estimate_maintenance_cost(pred),
                    'suggested_date': pred['predicted_failure_date'],
                    'reasoning': self._get_reasoning(pred)
                }
                recommendations.append(recommendation)
        
        return recommendations
    
    def _get_recommended_action(self, prediction: Dict) -> str:
        """Get recommended maintenance action based on prediction"""
        risk_score = prediction['confidence_score']
        
        if risk_score > 0.9:
            return "Immediate inspection and preventive maintenance required"
        elif risk_score > 0.8:
            return "Schedule comprehensive maintenance within 3 days"
        elif risk_score > 0.7:
            return "Plan preventive maintenance within 1 week"
        elif risk_score > 0.6:
            return "Monitor closely and schedule routine maintenance"
        else:
            return "Continue normal usage and monitoring"
    
    def _estimate_maintenance_cost(self, prediction: Dict) -> float:
        """Estimate maintenance cost based on prediction"""
        base_cost = 100.0  # Base maintenance cost
        risk_multiplier = 1 + (prediction['confidence_score'] * 2)
        
        return round(base_cost * risk_multiplier, 2)
    
    def _get_reasoning(self, prediction: Dict) -> str:
        """Get reasoning for the prediction"""
        reasons = []
        
        if prediction['condition_risk'] > 0.7:
            reasons.append("Poor tool condition")
        
        if prediction['anomaly_risk'] > 0.7:
            reasons.append("Unusual usage pattern detected")
        
        if prediction['confidence_score'] > 0.8:
            reasons.append("High probability of failure")
        
        return "; ".join(reasons) if reasons else "Based on usage patterns and condition"