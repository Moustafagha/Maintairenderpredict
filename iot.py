import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from src.models.machine import Machine, Sensor, SensorReading, Alert
from src.models.user import db
from src.predictive_analytics import PredictiveAnalytics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

iot_bp = Blueprint('iot', __name__, url_prefix='/api/iot')

# Siemens TIA Portal Integration
@iot_bp.route('/siemens/data', methods=['POST'])
def receive_siemens_data():
    """
    Receive sensor data from Siemens TIA Portal systems
    Expected format:
    {
        "machine_id": "string",
        "timestamp": "ISO datetime",
        "sensors": [
            {
                "sensor_id": "string",
                "type": "temperature|humidity|tension|vibration",
                "value": float,
                "unit": "string"
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        machine_id = data.get('machine_id')
        timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        sensors_data = data.get('sensors', [])
        
        if not machine_id or not sensors_data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify machine exists
        machine = Machine.query.filter_by(external_id=machine_id).first()
        if not machine:
            return jsonify({'error': 'Machine not found'}), 404
        
        processed_readings = []
        
        for sensor_data in sensors_data:
            sensor_id = sensor_data.get('sensor_id')
            sensor_type = sensor_data.get('type')
            value = sensor_data.get('value')
            unit = sensor_data.get('unit', '')
            
            if not all([sensor_id, sensor_type, value is not None]):
                continue
            
            # Find or create sensor
            sensor = Sensor.query.filter_by(
                machine_id=machine.id,
                external_id=sensor_id
            ).first()
            
            if not sensor:
                sensor = Sensor(
                    machine_id=machine.id,
                    external_id=sensor_id,
                    name=f"{sensor_type.title()} Sensor",
                    type=sensor_type,
                    unit=unit,
                    min_value=get_default_min_value(sensor_type),
                    max_value=get_default_max_value(sensor_type)
                )
                db.session.add(sensor)
                db.session.flush()
            
            # Create sensor reading
            reading = SensorReading(
                sensor_id=sensor.id,
                value=float(value),
                timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            )
            db.session.add(reading)
            processed_readings.append({
                'sensor_id': sensor_id,
                'type': sensor_type,
                'value': value,
                'timestamp': timestamp
            })
            
            # Check for threshold violations
            check_sensor_thresholds(sensor, float(value))
        
        db.session.commit()
        
        # Run predictive analysis if enough data
        try:
            analytics = PredictiveAnalytics()
            analytics.analyze_machine_health(machine.id)
        except Exception as e:
            logger.warning(f"Predictive analysis failed: {e}")
        
        logger.info(f"Processed {len(processed_readings)} sensor readings for machine {machine_id}")
        
        return jsonify({
            'status': 'success',
            'processed_readings': len(processed_readings),
            'machine_id': machine_id,
            'timestamp': timestamp
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing Siemens data: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# Schneider Integration
@iot_bp.route('/schneider/data', methods=['POST'])
def receive_schneider_data():
    """
    Receive sensor data from Schneider systems
    Similar format to Siemens but with Schneider-specific fields
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Schneider systems might use different field names
        machine_id = data.get('device_id') or data.get('machine_id')
        timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        sensors_data = data.get('measurements', []) or data.get('sensors', [])
        
        if not machine_id or not sensors_data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Process similar to Siemens but handle Schneider-specific format
        machine = Machine.query.filter_by(external_id=machine_id).first()
        if not machine:
            return jsonify({'error': 'Machine not found'}), 404
        
        processed_readings = []
        
        for sensor_data in sensors_data:
            # Schneider might use different field names
            sensor_id = sensor_data.get('id') or sensor_data.get('sensor_id')
            sensor_type = sensor_data.get('parameter') or sensor_data.get('type')
            value = sensor_data.get('value') or sensor_data.get('reading')
            unit = sensor_data.get('unit', '')
            
            if not all([sensor_id, sensor_type, value is not None]):
                continue
            
            # Normalize sensor type names
            sensor_type = normalize_sensor_type(sensor_type)
            
            # Find or create sensor
            sensor = Sensor.query.filter_by(
                machine_id=machine.id,
                external_id=sensor_id
            ).first()
            
            if not sensor:
                sensor = Sensor(
                    machine_id=machine.id,
                    external_id=sensor_id,
                    name=f"{sensor_type.title()} Sensor",
                    type=sensor_type,
                    unit=unit,
                    min_value=get_default_min_value(sensor_type),
                    max_value=get_default_max_value(sensor_type)
                )
                db.session.add(sensor)
                db.session.flush()
            
            # Create sensor reading
            reading = SensorReading(
                sensor_id=sensor.id,
                value=float(value),
                timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            )
            db.session.add(reading)
            processed_readings.append({
                'sensor_id': sensor_id,
                'type': sensor_type,
                'value': value,
                'timestamp': timestamp
            })
            
            # Check for threshold violations
            check_sensor_thresholds(sensor, float(value))
        
        db.session.commit()
        
        # Run predictive analysis
        try:
            analytics = PredictiveAnalytics()
            analytics.analyze_machine_health(machine.id)
        except Exception as e:
            logger.warning(f"Predictive analysis failed: {e}")
        
        logger.info(f"Processed {len(processed_readings)} sensor readings for Schneider machine {machine_id}")
        
        return jsonify({
            'status': 'success',
            'processed_readings': len(processed_readings),
            'machine_id': machine_id,
            'timestamp': timestamp
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing Schneider data: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# Generic IoT endpoint for other systems
@iot_bp.route('/generic/data', methods=['POST'])
def receive_generic_data():
    """
    Generic endpoint for any IoT system
    Flexible format that can handle various data structures
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Try to extract machine identifier from various possible fields
        machine_id = (data.get('machine_id') or 
                     data.get('device_id') or 
                     data.get('equipment_id') or 
                     data.get('asset_id'))
        
        if not machine_id:
            return jsonify({'error': 'Machine identifier not found'}), 400
        
        timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        
        # Try to extract sensor data from various possible structures
        sensors_data = (data.get('sensors') or 
                       data.get('measurements') or 
                       data.get('readings') or 
                       data.get('data', []))
        
        if not sensors_data:
            return jsonify({'error': 'No sensor data found'}), 400
        
        machine = Machine.query.filter_by(external_id=machine_id).first()
        if not machine:
            return jsonify({'error': 'Machine not found'}), 404
        
        processed_readings = []
        
        for sensor_data in sensors_data:
            # Extract sensor information with flexible field names
            sensor_id = (sensor_data.get('sensor_id') or 
                        sensor_data.get('id') or 
                        sensor_data.get('name'))
            
            sensor_type = (sensor_data.get('type') or 
                          sensor_data.get('parameter') or 
                          sensor_data.get('measurement_type'))
            
            value = (sensor_data.get('value') or 
                    sensor_data.get('reading') or 
                    sensor_data.get('measurement'))
            
            unit = sensor_data.get('unit', '')
            
            if not all([sensor_id, sensor_type, value is not None]):
                continue
            
            # Normalize sensor type
            sensor_type = normalize_sensor_type(sensor_type)
            
            # Find or create sensor
            sensor = Sensor.query.filter_by(
                machine_id=machine.id,
                external_id=sensor_id
            ).first()
            
            if not sensor:
                sensor = Sensor(
                    machine_id=machine.id,
                    external_id=sensor_id,
                    name=f"{sensor_type.title()} Sensor",
                    type=sensor_type,
                    unit=unit,
                    min_value=get_default_min_value(sensor_type),
                    max_value=get_default_max_value(sensor_type)
                )
                db.session.add(sensor)
                db.session.flush()
            
            # Create sensor reading
            reading = SensorReading(
                sensor_id=sensor.id,
                value=float(value),
                timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            )
            db.session.add(reading)
            processed_readings.append({
                'sensor_id': sensor_id,
                'type': sensor_type,
                'value': value,
                'timestamp': timestamp
            })
            
            # Check for threshold violations
            check_sensor_thresholds(sensor, float(value))
        
        db.session.commit()
        
        # Run predictive analysis
        try:
            analytics = PredictiveAnalytics()
            analytics.analyze_machine_health(machine.id)
        except Exception as e:
            logger.warning(f"Predictive analysis failed: {e}")
        
        logger.info(f"Processed {len(processed_readings)} sensor readings for generic machine {machine_id}")
        
        return jsonify({
            'status': 'success',
            'processed_readings': len(processed_readings),
            'machine_id': machine_id,
            'timestamp': timestamp
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing generic IoT data: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# Utility functions
def normalize_sensor_type(sensor_type):
    """Normalize sensor type names to standard values"""
    sensor_type = sensor_type.lower().strip()
    
    # Temperature variations
    if any(term in sensor_type for term in ['temp', 'temperature', 'thermal']):
        return 'temperature'
    
    # Humidity variations
    if any(term in sensor_type for term in ['humidity', 'moisture', 'rh']):
        return 'humidity'
    
    # Tension/Pressure variations
    if any(term in sensor_type for term in ['tension', 'pressure', 'force', 'stress']):
        return 'tension'
    
    # Vibration variations
    if any(term in sensor_type for term in ['vibration', 'vibr', 'oscillation', 'shake']):
        return 'vibration'
    
    # Default to the original type if no match
    return sensor_type

def get_default_min_value(sensor_type):
    """Get default minimum values for sensor types"""
    defaults = {
        'temperature': -50.0,
        'humidity': 0.0,
        'tension': 0.0,
        'vibration': 0.0
    }
    return defaults.get(sensor_type, 0.0)

def get_default_max_value(sensor_type):
    """Get default maximum values for sensor types"""
    defaults = {
        'temperature': 150.0,
        'humidity': 100.0,
        'tension': 1000.0,
        'vibration': 100.0
    }
    return defaults.get(sensor_type, 100.0)

def check_sensor_thresholds(sensor, value):
    """Check if sensor value violates thresholds and create alerts"""
    try:
        alerts_created = []
        
        # Check minimum threshold
        if value < sensor.min_value:
            alert = Alert(
                machine_id=sensor.machine_id,
                sensor_id=sensor.id,
                type='threshold_violation',
                severity='medium',
                message=f"{sensor.name} value ({value} {sensor.unit}) is below minimum threshold ({sensor.min_value} {sensor.unit})",
                status='active'
            )
            db.session.add(alert)
            alerts_created.append('min_threshold')
        
        # Check maximum threshold
        if value > sensor.max_value:
            alert = Alert(
                machine_id=sensor.machine_id,
                sensor_id=sensor.id,
                type='threshold_violation',
                severity='high' if value > sensor.max_value * 1.2 else 'medium',
                message=f"{sensor.name} value ({value} {sensor.unit}) exceeds maximum threshold ({sensor.max_value} {sensor.unit})",
                status='active'
            )
            db.session.add(alert)
            alerts_created.append('max_threshold')
        
        # Check for critical values (sensor-specific)
        critical_alert = check_critical_thresholds(sensor, value)
        if critical_alert:
            db.session.add(critical_alert)
            alerts_created.append('critical')
        
        if alerts_created:
            logger.info(f"Created alerts for sensor {sensor.name}: {alerts_created}")
            
    except Exception as e:
        logger.error(f"Error checking thresholds for sensor {sensor.name}: {e}")

def check_critical_thresholds(sensor, value):
    """Check for critical threshold violations that require immediate attention"""
    critical_thresholds = {
        'temperature': {'min': -40, 'max': 120},
        'humidity': {'min': 5, 'max': 95},
        'tension': {'min': -100, 'max': 800},
        'vibration': {'min': -10, 'max': 80}
    }
    
    if sensor.type in critical_thresholds:
        thresholds = critical_thresholds[sensor.type]
        
        if value < thresholds['min'] or value > thresholds['max']:
            return Alert(
                machine_id=sensor.machine_id,
                sensor_id=sensor.id,
                type='critical_threshold',
                severity='critical',
                message=f"CRITICAL: {sensor.name} value ({value} {sensor.unit}) is in dangerous range. Immediate attention required!",
                status='active'
            )
    
    return None

# Health check endpoint
@iot_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for IoT integration"""
    return jsonify({
        'status': 'healthy',
        'service': 'IoT Integration',
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': {
            'siemens': '/api/iot/siemens/data',
            'schneider': '/api/iot/schneider/data',
            'generic': '/api/iot/generic/data'
        }
    }), 200

