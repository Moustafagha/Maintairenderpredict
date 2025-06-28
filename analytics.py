from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.machine import Machine, Sensor, SensorReading, Alert
from src.predictive_analytics import analyze_machine_health, train_models_with_sample_data, PredictiveAnalytics
from datetime import datetime, timedelta
import logging

analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)

@analytics_bp.route('/analytics/health/<int:machine_id>', methods=['GET'])
def get_machine_health(machine_id):
    """Get health analysis for a specific machine"""
    try:
        # Verify machine exists
        machine = Machine.query.get_or_404(machine_id)
        
        # Get query parameters
        hours = request.args.get('hours', 24, type=int)  # Default to last 24 hours
        
        # Get sensor readings for the specified time period
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Query sensor readings
        sensor_readings = []
        for sensor in machine.sensors:
            readings = SensorReading.query.filter(
                SensorReading.sensor_id == sensor.id,
                SensorReading.timestamp >= start_time
            ).order_by(SensorReading.timestamp.asc()).all()
            
            for reading in readings:
                sensor_readings.append({
                    'sensor_id': reading.sensor_id,
                    'sensor_type': sensor.type,
                    'value': reading.value,
                    'timestamp': reading.timestamp.isoformat(),
                    'unit': sensor.unit
                })
        
        # Perform health analysis
        health_analysis = analyze_machine_health(machine_id, sensor_readings)
        
        # Add machine information
        health_analysis['machine'] = {
            'id': machine.id,
            'name': machine.name,
            'location': machine.location,
            'status': machine.status
        }
        
        return jsonify({
            'success': True,
            'health_analysis': health_analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting machine health: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/analytics/anomalies/<int:machine_id>', methods=['GET'])
def get_anomalies(machine_id):
    """Get anomaly detection results for a specific machine"""
    try:
        # Verify machine exists
        machine = Machine.query.get_or_404(machine_id)
        
        # Get query parameters
        hours = request.args.get('hours', 24, type=int)
        
        # Get sensor readings
        start_time = datetime.utcnow() - timedelta(hours=hours)
        sensor_readings = []
        
        for sensor in machine.sensors:
            readings = SensorReading.query.filter(
                SensorReading.sensor_id == sensor.id,
                SensorReading.timestamp >= start_time
            ).order_by(SensorReading.timestamp.asc()).all()
            
            for reading in readings:
                sensor_readings.append({
                    'sensor_type': sensor.type,
                    'value': reading.value,
                    'timestamp': reading.timestamp.isoformat()
                })
        
        # Initialize analytics engine
        analytics = PredictiveAnalytics()
        
        # Preprocess data and detect anomalies
        df = analytics.preprocess_sensor_data(sensor_readings)
        anomalies = analytics.detect_anomalies(df)
        
        return jsonify({
            'success': True,
            'machine_id': machine_id,
            'anomalies': anomalies,
            'total_anomalies': len(anomalies)
        }), 200
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/analytics/predictions/<int:machine_id>', methods=['GET'])
def get_failure_predictions(machine_id):
    """Get failure predictions for a specific machine"""
    try:
        # Verify machine exists
        machine = Machine.query.get_or_404(machine_id)
        
        # Get query parameters
        hours = request.args.get('hours', 168, type=int)  # Default to last week
        
        # Get sensor readings
        start_time = datetime.utcnow() - timedelta(hours=hours)
        sensor_readings = []
        
        for sensor in machine.sensors:
            readings = SensorReading.query.filter(
                SensorReading.sensor_id == sensor.id,
                SensorReading.timestamp >= start_time
            ).order_by(SensorReading.timestamp.asc()).all()
            
            for reading in readings:
                sensor_readings.append({
                    'sensor_type': sensor.type,
                    'value': reading.value,
                    'timestamp': reading.timestamp.isoformat()
                })
        
        # Initialize analytics engine
        analytics = PredictiveAnalytics()
        
        # Preprocess data and predict failure
        df = analytics.preprocess_sensor_data(sensor_readings)
        prediction = analytics.predict_failure_probability(df)
        
        return jsonify({
            'success': True,
            'machine_id': machine_id,
            'prediction': prediction
        }), 200
        
    except Exception as e:
        logger.error(f"Error predicting failures: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/analytics/thresholds/<int:machine_id>', methods=['GET'])
def get_threshold_violations(machine_id):
    """Get threshold violations for a specific machine"""
    try:
        # Verify machine exists
        machine = Machine.query.get_or_404(machine_id)
        
        # Get recent sensor readings (last hour)
        start_time = datetime.utcnow() - timedelta(hours=1)
        sensor_readings = []
        
        for sensor in machine.sensors:
            readings = SensorReading.query.filter(
                SensorReading.sensor_id == sensor.id,
                SensorReading.timestamp >= start_time
            ).order_by(SensorReading.timestamp.desc()).limit(1).all()
            
            for reading in readings:
                sensor_readings.append({
                    'sensor_type': sensor.type,
                    'value': reading.value,
                    'timestamp': reading.timestamp.isoformat()
                })
        
        # Initialize analytics engine
        analytics = PredictiveAnalytics()
        
        # Preprocess data and check thresholds
        df = analytics.preprocess_sensor_data(sensor_readings)
        violations = analytics.check_thresholds(df, machine_id)
        
        return jsonify({
            'success': True,
            'machine_id': machine_id,
            'violations': violations,
            'total_violations': len(violations)
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking thresholds: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/analytics/thresholds/<int:machine_id>', methods=['POST'])
def set_machine_thresholds(machine_id):
    """Set custom thresholds for a specific machine"""
    try:
        # Verify machine exists
        machine = Machine.query.get_or_404(machine_id)
        
        data = request.get_json()
        if not data or not data.get('thresholds'):
            return jsonify({'success': False, 'error': 'Thresholds data is required'}), 400
        
        # Initialize analytics engine
        analytics = PredictiveAnalytics()
        
        # Set threshold rules
        analytics.set_threshold_rules(machine_id, data['thresholds'])
        
        return jsonify({
            'success': True,
            'message': f'Thresholds set for machine {machine_id}',
            'thresholds': data['thresholds']
        }), 200
        
    except Exception as e:
        logger.error(f"Error setting thresholds: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/analytics/train-models', methods=['POST'])
def train_models():
    """Train machine learning models with sample data"""
    try:
        # Train models with sample data
        success = train_models_with_sample_data()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Models trained successfully with sample data'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to train models'
            }), 500
            
    except Exception as e:
        logger.error(f"Error training models: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/analytics/dashboard/<int:machine_id>', methods=['GET'])
def get_analytics_dashboard(machine_id):
    """Get comprehensive analytics dashboard data for a machine"""
    try:
        # Verify machine exists
        machine = Machine.query.get_or_404(machine_id)
        
        # Get query parameters
        hours = request.args.get('hours', 24, type=int)
        
        # Get sensor readings
        start_time = datetime.utcnow() - timedelta(hours=hours)
        sensor_readings = []
        sensor_stats = {}
        
        for sensor in machine.sensors:
            readings = SensorReading.query.filter(
                SensorReading.sensor_id == sensor.id,
                SensorReading.timestamp >= start_time
            ).order_by(SensorReading.timestamp.asc()).all()
            
            sensor_values = []
            for reading in readings:
                sensor_readings.append({
                    'sensor_type': sensor.type,
                    'value': reading.value,
                    'timestamp': reading.timestamp.isoformat()
                })
                sensor_values.append(reading.value)
            
            # Calculate sensor statistics
            if sensor_values:
                sensor_stats[sensor.type] = {
                    'current': sensor_values[-1],
                    'min': min(sensor_values),
                    'max': max(sensor_values),
                    'avg': sum(sensor_values) / len(sensor_values),
                    'count': len(sensor_values)
                }
        
        # Perform comprehensive analysis
        health_analysis = analyze_machine_health(machine_id, sensor_readings)
        
        # Get recent alerts
        recent_alerts = Alert.query.filter(
            Alert.machine_id == machine_id,
            Alert.timestamp >= start_time
        ).order_by(Alert.timestamp.desc()).limit(10).all()
        
        alerts_data = []
        for alert in recent_alerts:
            alerts_data.append({
                'id': alert.id,
                'type': alert.type,
                'message': alert.message,
                'severity': alert.severity,
                'status': alert.status,
                'timestamp': alert.timestamp.isoformat()
            })
        
        dashboard_data = {
            'machine': {
                'id': machine.id,
                'name': machine.name,
                'location': machine.location,
                'status': machine.status
            },
            'sensor_stats': sensor_stats,
            'health_analysis': health_analysis,
            'recent_alerts': alerts_data,
            'analysis_period_hours': hours,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/analytics/generate-sample-data/<int:machine_id>', methods=['POST'])
def generate_sample_data(machine_id):
    """Generate sample sensor data for testing purposes"""
    try:
        # Verify machine exists
        machine = Machine.query.get_or_404(machine_id)
        
        data = request.get_json()
        num_readings = data.get('num_readings', 100) if data else 100
        
        # Initialize analytics engine
        analytics = PredictiveAnalytics()
        
        # Generate sample data
        sample_data = analytics.generate_sample_training_data(num_readings)
        
        # Insert sample readings into database
        readings_created = 0
        
        for _, row in sample_data.iterrows():
            for sensor in machine.sensors:
                if sensor.type in row.index:
                    reading = SensorReading(
                        sensor_id=sensor.id,
                        value=row[sensor.type],
                        timestamp=row['timestamp']
                    )
                    db.session.add(reading)
                    readings_created += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Generated {readings_created} sample sensor readings',
            'machine_id': machine_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating sample data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

