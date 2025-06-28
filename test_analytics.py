#!/usr/bin/env python3
import os
import sys
import requests
import json
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app

def test_analytics_api():
    """Test the analytics API endpoints"""
    base_url = "http://localhost:5002"
    
    print("Testing Analytics API endpoints...")
    
    # First, register and login to get a token
    user_data = {
        "username": "analyticsuser",
        "email": "analytics@example.com",
        "password": "testpass123",
        "role": "engineer"
    }
    
    try:
        # Register user
        response = requests.post(f"{base_url}/api/register", json=user_data)
        print(f"User registration: {response.status_code}")
        
        # Login
        login_data = {"username": "analyticsuser", "password": "testpass123"}
        response = requests.post(f"{base_url}/api/login", json=login_data)
        
        if response.status_code != 200:
            print("Failed to login")
            return
        
        token = response.json().get('token')
        headers = {'Authorization': f'Bearer {token}'}
        
        # Create a machine
        machine_data = {
            "name": "Analytics Test Machine",
            "location": "Test Lab",
            "description": "Machine for testing analytics"
        }
        response = requests.post(f"{base_url}/api/machines", json=machine_data, headers=headers)
        print(f"Create machine: {response.status_code}")
        
        if response.status_code != 201:
            print("Failed to create machine")
            return
        
        machine_id = response.json().get('machine', {}).get('id')
        print(f"Created machine with ID: {machine_id}")
        
        # Create sensors
        sensors = [
            {"name": "Temperature Sensor", "type": "temperature", "unit": "°C", "min_value": -10, "max_value": 80},
            {"name": "Humidity Sensor", "type": "humidity", "unit": "%RH", "min_value": 0, "max_value": 100},
            {"name": "Tension Sensor", "type": "tension", "unit": "N", "min_value": 0, "max_value": 1000},
            {"name": "Vibration Sensor", "type": "vibration", "unit": "g", "min_value": 0, "max_value": 50}
        ]
        
        sensor_ids = []
        for sensor_data in sensors:
            response = requests.post(f"{base_url}/api/machines/{machine_id}/sensors", json=sensor_data, headers=headers)
            if response.status_code == 201:
                sensor_id = response.json().get('sensor', {}).get('id')
                sensor_ids.append(sensor_id)
                print(f"Created {sensor_data['type']} sensor with ID: {sensor_id}")
        
        # Generate sample data
        print("Generating sample data...")
        response = requests.post(f"{base_url}/api/analytics/generate-sample-data/{machine_id}", 
                               json={"num_readings": 200}, headers=headers)
        print(f"Generate sample data: {response.status_code} - {response.json().get('message', '')}")
        
        # Train models
        print("Training ML models...")
        response = requests.post(f"{base_url}/api/analytics/train-models", headers=headers)
        print(f"Train models: {response.status_code} - {response.json().get('message', '')}")
        
        # Test analytics endpoints
        print("\nTesting analytics endpoints:")
        
        # Get machine health
        response = requests.get(f"{base_url}/api/analytics/health/{machine_id}", headers=headers)
        print(f"Machine health: {response.status_code}")
        if response.status_code == 200:
            health = response.json().get('health_analysis', {})
            print(f"  Health status: {health.get('health_status')}")
            print(f"  Failure probability: {health.get('failure_prediction', {}).get('failure_probability', 0):.2f}")
        
        # Get anomalies
        response = requests.get(f"{base_url}/api/analytics/anomalies/{machine_id}", headers=headers)
        print(f"Anomaly detection: {response.status_code}")
        if response.status_code == 200:
            anomalies = response.json().get('anomalies', [])
            print(f"  Anomalies detected: {len(anomalies)}")
        
        # Get failure predictions
        response = requests.get(f"{base_url}/api/analytics/predictions/{machine_id}", headers=headers)
        print(f"Failure predictions: {response.status_code}")
        if response.status_code == 200:
            prediction = response.json().get('prediction', {})
            print(f"  Failure probability: {prediction.get('failure_probability', 0):.2f}")
            print(f"  Time to failure: {prediction.get('time_to_failure_hours')} hours")
        
        # Get threshold violations
        response = requests.get(f"{base_url}/api/analytics/thresholds/{machine_id}", headers=headers)
        print(f"Threshold violations: {response.status_code}")
        if response.status_code == 200:
            violations = response.json().get('violations', [])
            print(f"  Violations found: {len(violations)}")
        
        # Set custom thresholds
        custom_thresholds = {
            "thresholds": {
                "temperature": {"min": 0, "max": 60},
                "humidity": {"min": 10, "max": 90},
                "tension": {"min": 50, "max": 800},
                "vibration": {"min": 0, "max": 30}
            }
        }
        response = requests.post(f"{base_url}/api/analytics/thresholds/{machine_id}", 
                               json=custom_thresholds, headers=headers)
        print(f"Set custom thresholds: {response.status_code}")
        
        # Get analytics dashboard
        response = requests.get(f"{base_url}/api/analytics/dashboard/{machine_id}", headers=headers)
        print(f"Analytics dashboard: {response.status_code}")
        if response.status_code == 200:
            dashboard = response.json().get('dashboard', {})
            print(f"  Machine: {dashboard.get('machine', {}).get('name')}")
            print(f"  Sensor stats: {len(dashboard.get('sensor_stats', {}))}")
            print(f"  Recent alerts: {len(dashboard.get('recent_alerts', []))}")
        
    except Exception as e:
        print(f"Analytics API test error: {e}")

if __name__ == '__main__':
    # Start the Flask app in a separate thread
    import threading
    
    def run_app():
        app.run(host='0.0.0.0', port=5002, debug=False)
    
    # Start Flask app in background
    flask_thread = threading.Thread(target=run_app)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Wait for Flask to start
    time.sleep(3)
    
    # Run tests
    test_analytics_api()
    
    print("\nAnalytics API testing completed!")

