import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os
from typing import List, Dict, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictiveAnalytics:
    """
    Predictive analytics engine for machine failure prediction and anomaly detection.
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the predictive analytics engine.
        
        Args:
            model_path: Path to save/load trained models
        """
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), '..', 'models')
        self.anomaly_model = None
        self.scaler = None
        self.feature_columns = ['temperature', 'humidity', 'tension', 'vibration']
        self.threshold_rules = {}
        
        # Create models directory if it doesn't exist
        os.makedirs(self.model_path, exist_ok=True)
        
        # Load existing models if available
        self.load_models()
    
    def preprocess_sensor_data(self, sensor_readings: List[Dict]) -> pd.DataFrame:
        """
        Preprocess sensor data for analysis.
        
        Args:
            sensor_readings: List of sensor reading dictionaries
            
        Returns:
            Preprocessed DataFrame
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(sensor_readings)
            
            if df.empty:
                logger.warning("Empty sensor data provided")
                return pd.DataFrame()
            
            # Convert timestamp to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
            
            # Pivot data to have sensors as columns
            if 'sensor_type' in df.columns and 'value' in df.columns:
                df_pivot = df.pivot_table(
                    index='timestamp', 
                    columns='sensor_type', 
                    values='value', 
                    aggfunc='mean'
                ).reset_index()
                
                # Fill missing values with forward fill then backward fill
                df_pivot = df_pivot.fillna(method='ffill').fillna(method='bfill')
                
                return df_pivot
            
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing sensor data: {e}")
            return pd.DataFrame()
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create additional features for machine learning.
        
        Args:
            df: Preprocessed sensor data DataFrame
            
        Returns:
            DataFrame with additional features
        """
        try:
            if df.empty:
                return df
            
            feature_df = df.copy()
            
            # Calculate rolling statistics for each sensor type
            for col in self.feature_columns:
                if col in feature_df.columns:
                    # Rolling mean and std (window of 10 readings)
                    feature_df[f'{col}_rolling_mean'] = feature_df[col].rolling(window=10, min_periods=1).mean()
                    feature_df[f'{col}_rolling_std'] = feature_df[col].rolling(window=10, min_periods=1).std()
                    
                    # Rate of change
                    feature_df[f'{col}_rate_of_change'] = feature_df[col].diff()
                    
                    # Z-score (standardized values)
                    mean_val = feature_df[col].mean()
                    std_val = feature_df[col].std()
                    if std_val > 0:
                        feature_df[f'{col}_zscore'] = (feature_df[col] - mean_val) / std_val
                    else:
                        feature_df[f'{col}_zscore'] = 0
            
            # Fill NaN values
            feature_df = feature_df.fillna(0)
            
            return feature_df
            
        except Exception as e:
            logger.error(f"Error creating features: {e}")
            return df
    
    def train_anomaly_detection_model(self, training_data: pd.DataFrame) -> bool:
        """
        Train the anomaly detection model using Isolation Forest.
        
        Args:
            training_data: Historical sensor data for training
            
        Returns:
            True if training successful, False otherwise
        """
        try:
            if training_data.empty:
                logger.warning("No training data provided")
                return False
            
            # Create features
            feature_data = self.create_features(training_data)
            
            # Select feature columns for training
            feature_cols = []
            for col in feature_data.columns:
                if any(sensor in col for sensor in self.feature_columns):
                    feature_cols.append(col)
            
            if not feature_cols:
                logger.warning("No valid feature columns found")
                return False
            
            X = feature_data[feature_cols].values
            
            # Initialize and fit the scaler
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest model
            self.anomaly_model = IsolationForest(
                contamination=0.1,  # Assume 10% of data points are anomalies
                random_state=42,
                n_estimators=100
            )
            
            self.anomaly_model.fit(X_scaled)
            
            # Save the trained models
            self.save_models()
            
            logger.info("Anomaly detection model trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training anomaly detection model: {e}")
            return False
    
    def detect_anomalies(self, sensor_data: pd.DataFrame) -> List[Dict]:
        """
        Detect anomalies in sensor data.
        
        Args:
            sensor_data: Current sensor data
            
        Returns:
            List of anomaly detection results
        """
        try:
            if self.anomaly_model is None or self.scaler is None:
                logger.warning("Anomaly detection model not trained")
                return []
            
            if sensor_data.empty:
                return []
            
            # Create features
            feature_data = self.create_features(sensor_data)
            
            # Select feature columns
            feature_cols = []
            for col in feature_data.columns:
                if any(sensor in col for sensor in self.feature_columns):
                    feature_cols.append(col)
            
            if not feature_cols:
                return []
            
            X = feature_data[feature_cols].values
            X_scaled = self.scaler.transform(X)
            
            # Predict anomalies (-1 for anomaly, 1 for normal)
            predictions = self.anomaly_model.predict(X_scaled)
            anomaly_scores = self.anomaly_model.decision_function(X_scaled)
            
            anomalies = []
            for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                if pred == -1:  # Anomaly detected
                    anomaly = {
                        'index': i,
                        'timestamp': feature_data.iloc[i].get('timestamp', datetime.now()).isoformat(),
                        'anomaly_score': float(score),
                        'severity': self._calculate_severity(score),
                        'affected_sensors': self._identify_affected_sensors(feature_data.iloc[i], feature_cols)
                    }
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def _calculate_severity(self, anomaly_score: float) -> str:
        """
        Calculate severity level based on anomaly score.
        
        Args:
            anomaly_score: Anomaly score from the model
            
        Returns:
            Severity level string
        """
        if anomaly_score < -0.5:
            return 'critical'
        elif anomaly_score < -0.3:
            return 'high'
        elif anomaly_score < -0.1:
            return 'medium'
        else:
            return 'low'
    
    def _identify_affected_sensors(self, data_row: pd.Series, feature_cols: List[str]) -> List[str]:
        """
        Identify which sensors are contributing to the anomaly.
        
        Args:
            data_row: Single row of feature data
            feature_cols: List of feature column names
            
        Returns:
            List of affected sensor types
        """
        affected_sensors = []
        
        for sensor in self.feature_columns:
            # Check if any feature related to this sensor has extreme values
            sensor_features = [col for col in feature_cols if sensor in col]
            for feature in sensor_features:
                if feature in data_row.index:
                    value = data_row[feature]
                    if abs(value) > 2:  # Z-score threshold
                        if sensor not in affected_sensors:
                            affected_sensors.append(sensor)
        
        return affected_sensors
    
    def check_thresholds(self, sensor_data: pd.DataFrame, machine_id: int) -> List[Dict]:
        """
        Check sensor values against predefined thresholds.
        
        Args:
            sensor_data: Current sensor data
            machine_id: ID of the machine
            
        Returns:
            List of threshold violations
        """
        try:
            violations = []
            
            if sensor_data.empty:
                return violations
            
            # Get the latest reading for each sensor
            latest_data = sensor_data.iloc[-1] if len(sensor_data) > 0 else None
            
            if latest_data is None:
                return violations
            
            # Default thresholds (can be customized per machine)
            default_thresholds = {
                'temperature': {'min': -10, 'max': 80},
                'humidity': {'min': 0, 'max': 100},
                'tension': {'min': 0, 'max': 1000},
                'vibration': {'min': 0, 'max': 50}
            }
            
            # Use machine-specific thresholds if available
            thresholds = self.threshold_rules.get(machine_id, default_thresholds)
            
            for sensor_type, limits in thresholds.items():
                if sensor_type in latest_data.index:
                    value = latest_data[sensor_type]
                    
                    if value < limits['min'] or value > limits['max']:
                        violation = {
                            'sensor_type': sensor_type,
                            'value': float(value),
                            'threshold_min': limits['min'],
                            'threshold_max': limits['max'],
                            'severity': 'high' if value < limits['min'] * 0.5 or value > limits['max'] * 1.5 else 'medium',
                            'timestamp': latest_data.get('timestamp', datetime.now()).isoformat()
                        }
                        violations.append(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")
            return []
    
    def predict_failure_probability(self, sensor_data: pd.DataFrame) -> Dict:
        """
        Predict the probability of machine failure based on current trends.
        
        Args:
            sensor_data: Historical sensor data
            
        Returns:
            Failure prediction results
        """
        try:
            if sensor_data.empty or len(sensor_data) < 10:
                return {
                    'failure_probability': 0.0,
                    'confidence': 0.0,
                    'time_to_failure_hours': None,
                    'contributing_factors': []
                }
            
            # Create features
            feature_data = self.create_features(sensor_data)
            
            # Calculate trend indicators
            trends = {}
            for sensor in self.feature_columns:
                if sensor in feature_data.columns:
                    # Calculate trend over last 20 readings
                    recent_data = feature_data[sensor].tail(20)
                    if len(recent_data) > 1:
                        # Linear regression slope as trend indicator
                        x = np.arange(len(recent_data))
                        slope = np.polyfit(x, recent_data, 1)[0]
                        trends[sensor] = slope
            
            # Simple heuristic-based failure prediction
            failure_indicators = 0
            contributing_factors = []
            
            # Check for concerning trends
            if 'temperature' in trends:
                if trends['temperature'] > 1.0:  # Rapidly increasing temperature
                    failure_indicators += 2
                    contributing_factors.append('Rising temperature trend')
            
            if 'vibration' in trends:
                if trends['vibration'] > 0.5:  # Increasing vibration
                    failure_indicators += 2
                    contributing_factors.append('Increasing vibration')
            
            if 'humidity' in trends:
                if abs(trends['humidity']) > 2.0:  # Rapid humidity changes
                    failure_indicators += 1
                    contributing_factors.append('Unstable humidity')
            
            # Check recent anomalies
            recent_anomalies = self.detect_anomalies(feature_data.tail(10))
            if recent_anomalies:
                failure_indicators += len(recent_anomalies)
                contributing_factors.append(f'{len(recent_anomalies)} recent anomalies detected')
            
            # Calculate failure probability (0-1 scale)
            failure_probability = min(failure_indicators / 10.0, 1.0)
            
            # Estimate time to failure (very simplified)
            time_to_failure_hours = None
            if failure_probability > 0.7:
                time_to_failure_hours = 24  # Critical - 24 hours
            elif failure_probability > 0.5:
                time_to_failure_hours = 72  # High - 3 days
            elif failure_probability > 0.3:
                time_to_failure_hours = 168  # Medium - 1 week
            
            return {
                'failure_probability': failure_probability,
                'confidence': 0.8 if len(sensor_data) > 100 else 0.6,
                'time_to_failure_hours': time_to_failure_hours,
                'contributing_factors': contributing_factors
            }
            
        except Exception as e:
            logger.error(f"Error predicting failure probability: {e}")
            return {
                'failure_probability': 0.0,
                'confidence': 0.0,
                'time_to_failure_hours': None,
                'contributing_factors': []
            }
    
    def set_threshold_rules(self, machine_id: int, thresholds: Dict):
        """
        Set custom threshold rules for a specific machine.
        
        Args:
            machine_id: ID of the machine
            thresholds: Dictionary of threshold rules
        """
        self.threshold_rules[machine_id] = thresholds
        logger.info(f"Threshold rules set for machine {machine_id}")
    
    def save_models(self):
        """Save trained models to disk."""
        try:
            if self.anomaly_model is not None:
                joblib.dump(self.anomaly_model, os.path.join(self.model_path, 'anomaly_model.pkl'))
            
            if self.scaler is not None:
                joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler.pkl'))
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self):
        """Load trained models from disk."""
        try:
            anomaly_model_path = os.path.join(self.model_path, 'anomaly_model.pkl')
            scaler_path = os.path.join(self.model_path, 'scaler.pkl')
            
            if os.path.exists(anomaly_model_path):
                self.anomaly_model = joblib.load(anomaly_model_path)
                logger.info("Anomaly detection model loaded")
            
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info("Scaler loaded")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def generate_sample_training_data(self, num_samples: int = 1000) -> pd.DataFrame:
        """
        Generate sample training data for demonstration purposes.
        
        Args:
            num_samples: Number of sample data points to generate
            
        Returns:
            DataFrame with sample sensor data
        """
        np.random.seed(42)
        
        # Generate timestamps
        start_time = datetime.now() - timedelta(days=30)
        timestamps = [start_time + timedelta(minutes=i*5) for i in range(num_samples)]
        
        # Generate normal sensor data with some patterns
        data = []
        for i, timestamp in enumerate(timestamps):
            # Add some daily and weekly patterns
            hour_factor = np.sin(2 * np.pi * i / (24 * 12))  # 12 readings per hour
            day_factor = np.sin(2 * np.pi * i / (24 * 12 * 7))  # Weekly pattern
            
            # Temperature: 20-30°C with patterns
            temperature = 25 + 3 * hour_factor + 2 * day_factor + np.random.normal(0, 1)
            
            # Humidity: 40-70% with inverse temperature correlation
            humidity = 55 - 0.5 * (temperature - 25) + np.random.normal(0, 3)
            
            # Tension: 100-200N with some random variation
            tension = 150 + 20 * np.random.normal(0, 1)
            
            # Vibration: 5-15g with occasional spikes
            vibration = 10 + 2 * np.random.normal(0, 1)
            if np.random.random() < 0.05:  # 5% chance of spike
                vibration += np.random.uniform(10, 20)
            
            data.append({
                'timestamp': timestamp,
                'temperature': max(0, temperature),
                'humidity': max(0, min(100, humidity)),
                'tension': max(0, tension),
                'vibration': max(0, vibration)
            })
        
        return pd.DataFrame(data)


# Utility functions for integration with Flask routes
def analyze_machine_health(machine_id: int, sensor_readings: List[Dict]) -> Dict:
    """
    Analyze machine health based on sensor readings.
    
    Args:
        machine_id: ID of the machine
        sensor_readings: List of sensor reading dictionaries
        
    Returns:
        Health analysis results
    """
    analytics = PredictiveAnalytics()
    
    # Preprocess data
    df = analytics.preprocess_sensor_data(sensor_readings)
    
    if df.empty:
        return {
            'status': 'no_data',
            'message': 'No sensor data available for analysis'
        }
    
    # Detect anomalies
    anomalies = analytics.detect_anomalies(df)
    
    # Check thresholds
    threshold_violations = analytics.check_thresholds(df, machine_id)
    
    # Predict failure probability
    failure_prediction = analytics.predict_failure_probability(df)
    
    # Determine overall health status
    health_status = 'healthy'
    if failure_prediction['failure_probability'] > 0.7:
        health_status = 'critical'
    elif failure_prediction['failure_probability'] > 0.5 or threshold_violations:
        health_status = 'warning'
    elif anomalies:
        health_status = 'attention'
    
    return {
        'status': 'success',
        'machine_id': machine_id,
        'health_status': health_status,
        'failure_prediction': failure_prediction,
        'anomalies': anomalies,
        'threshold_violations': threshold_violations,
        'analysis_timestamp': datetime.now().isoformat()
    }


def train_models_with_sample_data():
    """Train models with sample data for demonstration."""
    analytics = PredictiveAnalytics()
    
    # Generate sample training data
    training_data = analytics.generate_sample_training_data(2000)
    
    # Train the anomaly detection model
    success = analytics.train_anomaly_detection_model(training_data)
    
    return success

