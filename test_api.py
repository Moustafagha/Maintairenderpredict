#!/usr/bin/env python3
import os
import sys
import requests
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:5001"
    
    print("Testing API endpoints...")
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"Root endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Root endpoint error: {e}")
    
    # Test user registration
    try:
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "role": "engineer"
        }
        response = requests.post(f"{base_url}/api/register", json=user_data)
        print(f"User registration: {response.status_code} - {response.json()}")
        
        if response.status_code == 201:
            # Test login
            login_data = {
                "username": "testuser",
                "password": "testpass123"
            }
            response = requests.post(f"{base_url}/api/login", json=login_data)
            print(f"User login: {response.status_code} - {response.json()}")
            
            if response.status_code == 200:
                token = response.json().get('token')
                headers = {'Authorization': f'Bearer {token}'}
                
                # Test creating a machine
                machine_data = {
                    "name": "Test Machine",
                    "location": "Factory Floor",
                    "description": "Test machine for API testing"
                }
                response = requests.post(f"{base_url}/api/machines", json=machine_data, headers=headers)
                print(f"Create machine: {response.status_code} - {response.json()}")
                
                if response.status_code == 201:
                    machine_id = response.json().get('machine', {}).get('id')
                    
                    # Test creating a sensor
                    sensor_data = {
                        "name": "Temperature Sensor",
                        "type": "temperature",
                        "unit": "°C",
                        "min_value": -10,
                        "max_value": 100
                    }
                    response = requests.post(f"{base_url}/api/machines/{machine_id}/sensors", json=sensor_data, headers=headers)
                    print(f"Create sensor: {response.status_code} - {response.json()}")
                    
                    if response.status_code == 201:
                        sensor_id = response.json().get('sensor', {}).get('id')
                        
                        # Test adding sensor reading
                        reading_data = {
                            "value": 25.5
                        }
                        response = requests.post(f"{base_url}/api/sensors/{sensor_id}/readings", json=reading_data, headers=headers)
                        print(f"Add sensor reading: {response.status_code} - {response.json()}")
                
                # Test getting machines
                response = requests.get(f"{base_url}/api/machines", headers=headers)
                print(f"Get machines: {response.status_code} - {response.json()}")
    
    except Exception as e:
        print(f"API test error: {e}")

if __name__ == '__main__':
    # Start the Flask app in a separate thread
    import threading
    import time
    
    def run_app():
        app.run(host='0.0.0.0', port=5001, debug=False)
    
    # Start Flask app in background
    flask_thread = threading.Thread(target=run_app)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Wait for Flask to start
    time.sleep(2)
    
    # Run tests
    test_api()
    
    print("\nAPI testing completed!")

