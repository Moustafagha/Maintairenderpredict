#!/usr/bin/env python3
"""
Test script for IoT integration endpoints
"""
import requests
import json
import time
import random
from datetime import datetime

# API base URL
BASE_URL = 'http://localhost:5001'

def test_siemens_integration():
    """Test Siemens TIA Portal integration"""
    print("Testing Siemens TIA Portal Integration...")
    
    # Sample Siemens data
    siemens_data = {
        "machine_id": "SIEMENS_001",
        "timestamp": datetime.utcnow().isoformat(),
        "sensors": [
            {
                "sensor_id": "TEMP_001",
                "type": "temperature",
                "value": random.uniform(20, 80),
                "unit": "°C"
            },
            {
                "sensor_id": "HUM_001", 
                "type": "humidity",
                "value": random.uniform(30, 70),
                "unit": "%"
            },
            {
                "sensor_id": "VIB_001",
                "type": "vibration", 
                "value": random.uniform(0, 20),
                "unit": "mm/s"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/iot/siemens/data",
            json=siemens_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_schneider_integration():
    """Test Schneider integration"""
    print("\nTesting Schneider Integration...")
    
    # Sample Schneider data (different format)
    schneider_data = {
        "device_id": "SCHNEIDER_001",
        "timestamp": datetime.utcnow().isoformat(),
        "measurements": [
            {
                "id": "TEMP_SCH_001",
                "parameter": "temperature",
                "value": random.uniform(25, 75),
                "unit": "°C"
            },
            {
                "id": "PRESS_SCH_001",
                "parameter": "tension",
                "value": random.uniform(100, 500),
                "unit": "kPa"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/iot/schneider/data",
            json=schneider_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_generic_integration():
    """Test generic IoT integration"""
    print("\nTesting Generic IoT Integration...")
    
    # Sample generic data
    generic_data = {
        "equipment_id": "GENERIC_001",
        "timestamp": datetime.utcnow().isoformat(),
        "readings": [
            {
                "name": "temp_sensor_1",
                "measurement_type": "temperature",
                "measurement": random.uniform(15, 85),
                "unit": "°C"
            },
            {
                "name": "humidity_sensor_1",
                "measurement_type": "humidity",
                "measurement": random.uniform(20, 80),
                "unit": "%"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/iot/generic/data",
            json=generic_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_notification_system():
    """Test notification system"""
    print("\nTesting Notification System...")
    
    # Test notification data
    notification_data = {
        "type": "email",
        "recipients": ["test@example.com"],
        "subject": "Test Alert from MaintAI",
        "message": "This is a test alert message from the IoT integration test.",
        "alert_data": {
            "machine_name": "Test Machine",
            "sensor_name": "Test Temperature Sensor",
            "type": "threshold_violation",
            "severity": "medium",
            "timestamp": datetime.utcnow().isoformat(),
            "value": "85.5",
            "unit": "°C"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/notifications/send",
            json=notification_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_health_check():
    """Test IoT health check"""
    print("\nTesting IoT Health Check...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/iot/health")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def create_test_machine():
    """Create a test machine for IoT testing"""
    print("\nCreating test machines...")
    
    machines = [
        {
            "name": "Siemens Test Machine",
            "external_id": "SIEMENS_001",
            "location": "Factory Floor A",
            "type": "Industrial Robot",
            "status": "running"
        },
        {
            "name": "Schneider Test Machine", 
            "external_id": "SCHNEIDER_001",
            "location": "Factory Floor B",
            "type": "Conveyor System",
            "status": "running"
        },
        {
            "name": "Generic Test Machine",
            "external_id": "GENERIC_001", 
            "location": "Factory Floor C",
            "type": "Packaging Machine",
            "status": "running"
        }
    ]
    
    for machine_data in machines:
        try:
            response = requests.post(
                f"{BASE_URL}/api/machines",
                json=machine_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                print(f"Created machine: {machine_data['name']}")
            else:
                print(f"Failed to create machine: {machine_data['name']} - {response.text}")
                
        except Exception as e:
            print(f"Error creating machine {machine_data['name']}: {e}")

def simulate_continuous_data():
    """Simulate continuous sensor data for testing"""
    print("\nSimulating continuous sensor data...")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            # Send data to all three systems
            test_siemens_integration()
            time.sleep(2)
            
            test_schneider_integration()
            time.sleep(2)
            
            test_generic_integration()
            time.sleep(2)
            
            print("Waiting 10 seconds before next batch...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nStopped simulation.")

def main():
    """Main test function"""
    print("=== MaintAI IoT Integration Test Suite ===\n")
    
    # Create test machines first
    create_test_machine()
    
    # Test all endpoints
    tests = [
        ("Health Check", test_health_check),
        ("Siemens Integration", test_siemens_integration),
        ("Schneider Integration", test_schneider_integration),
        ("Generic Integration", test_generic_integration),
        ("Notification System", test_notification_system)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        result = test_func()
        results.append((test_name, result))
        print(f"{'='*50}")
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY:")
    print(f"{'='*50}")
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Ask if user wants to run continuous simulation
    print(f"\n{'='*50}")
    choice = input("Run continuous data simulation? (y/n): ").lower().strip()
    if choice == 'y':
        simulate_continuous_data()

if __name__ == "__main__":
    main()

