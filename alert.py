from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.machine import Alert, Notification, Machine, Sensor
from datetime import datetime

alert_bp = Blueprint('alert', __name__)

# Alert CRUD operations
@alert_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts with optional filtering"""
    try:
        # Query parameters for filtering
        machine_id = request.args.get('machine_id', type=int)
        severity = request.args.get('severity')
        status = request.args.get('status')
        alert_type = request.args.get('type')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = Alert.query
        
        # Apply filters
        if machine_id:
            query = query.filter_by(machine_id=machine_id)
        if severity:
            query = query.filter_by(severity=severity)
        if status:
            query = query.filter_by(status=status)
        if alert_type:
            query = query.filter_by(type=alert_type)
        
        # Order by timestamp descending and apply pagination
        alerts = query.order_by(Alert.timestamp.desc()).offset(offset).limit(limit).all()
        
        # Enrich alerts with machine and sensor information
        enriched_alerts = []
        for alert in alerts:
            alert_dict = alert.to_dict()
            
            # Add machine information
            if alert.machine:
                alert_dict['machine_name'] = alert.machine.name
                alert_dict['machine_location'] = alert.machine.location
            
            # Add sensor information if applicable
            if alert.sensor_id:
                sensor = Sensor.query.get(alert.sensor_id)
                if sensor:
                    alert_dict['sensor_name'] = sensor.name
                    alert_dict['sensor_type'] = sensor.type
            
            enriched_alerts.append(alert_dict)
        
        return jsonify({
            'success': True,
            'alerts': enriched_alerts
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@alert_bp.route('/alerts', methods=['POST'])
def create_alert():
    """Create a new alert"""
    try:
        data = request.get_json()
        
        if not data or not data.get('machine_id') or not data.get('type') or not data.get('message'):
            return jsonify({'success': False, 'error': 'Machine ID, type, and message are required'}), 400
        
        # Verify machine exists
        machine = Machine.query.get(data['machine_id'])
        if not machine:
            return jsonify({'success': False, 'error': 'Machine not found'}), 404
        
        # Verify sensor exists if sensor_id is provided
        if data.get('sensor_id'):
            sensor = Sensor.query.get(data['sensor_id'])
            if not sensor:
                return jsonify({'success': False, 'error': 'Sensor not found'}), 404
        
        alert = Alert(
            machine_id=data['machine_id'],
            sensor_id=data.get('sensor_id'),
            type=data['type'],
            message=data['message'],
            severity=data.get('severity', 'medium'),
            status=data.get('status', 'active')
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alert created successfully',
            'alert': alert.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@alert_bp.route('/alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get a specific alert"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        alert_dict = alert.to_dict()
        
        # Add machine information
        if alert.machine:
            alert_dict['machine_name'] = alert.machine.name
            alert_dict['machine_location'] = alert.machine.location
        
        # Add sensor information if applicable
        if alert.sensor_id:
            sensor = Sensor.query.get(alert.sensor_id)
            if sensor:
                alert_dict['sensor_name'] = sensor.name
                alert_dict['sensor_type'] = sensor.type
        
        return jsonify({
            'success': True,
            'alert': alert_dict
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@alert_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """Update an alert (typically to change status)"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        data = request.get_json()
        
        if data.get('status'):
            alert.status = data['status']
        if data.get('severity'):
            alert.severity = data['severity']
        if data.get('message'):
            alert.message = data['message']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alert updated successfully',
            'alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@alert_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete an alert"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alert deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Notification operations
@alert_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get notifications for a user"""
    try:
        user_id = request.args.get('user_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        status = request.args.get('status')
        
        query = Notification.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        
        notifications = query.order_by(Notification.sent_at.desc()).offset(offset).limit(limit).all()
        
        # Enrich notifications with alert information
        enriched_notifications = []
        for notification in notifications:
            notification_dict = notification.to_dict()
            
            # Add alert information
            if notification.alert:
                notification_dict['alert_message'] = notification.alert.message
                notification_dict['alert_severity'] = notification.alert.severity
                notification_dict['alert_type'] = notification.alert.type
                
                # Add machine information
                if notification.alert.machine:
                    notification_dict['machine_name'] = notification.alert.machine.name
            
            enriched_notifications.append(notification_dict)
        
        return jsonify({
            'success': True,
            'notifications': enriched_notifications
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@alert_bp.route('/notifications', methods=['POST'])
def create_notification():
    """Create a new notification"""
    try:
        data = request.get_json()
        
        if not data or not data.get('user_id') or not data.get('alert_id') or not data.get('method'):
            return jsonify({'success': False, 'error': 'User ID, alert ID, and method are required'}), 400
        
        # Verify user and alert exist
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        alert = Alert.query.get(data['alert_id'])
        if not alert:
            return jsonify({'success': False, 'error': 'Alert not found'}), 404
        
        notification = Notification(
            user_id=data['user_id'],
            alert_id=data['alert_id'],
            method=data['method'],
            status=data.get('status', 'sent')
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification created successfully',
            'notification': notification.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@alert_bp.route('/notifications/<int:notification_id>', methods=['PUT'])
def update_notification(notification_id):
    """Update a notification (typically to mark as read)"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        data = request.get_json()
        
        if data.get('status'):
            notification.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification updated successfully',
            'notification': notification.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Bulk notification creation for alerts
@alert_bp.route('/alerts/<int:alert_id>/notify', methods=['POST'])
def notify_users_for_alert(alert_id):
    """Send notifications to users for a specific alert"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        data = request.get_json()
        
        user_ids = data.get('user_ids', [])
        method = data.get('method', 'in_app')
        
        if not user_ids:
            # If no specific users provided, notify all engineers and admins
            users = User.query.filter(User.role.in_(['engineer', 'admin'])).all()
            user_ids = [user.id for user in users]
        
        notifications_created = []
        for user_id in user_ids:
            # Check if user exists
            user = User.query.get(user_id)
            if not user:
                continue
            
            # Check if notification already exists for this user and alert
            existing_notification = Notification.query.filter_by(
                user_id=user_id,
                alert_id=alert_id,
                method=method
            ).first()
            
            if existing_notification:
                continue
            
            notification = Notification(
                user_id=user_id,
                alert_id=alert_id,
                method=method,
                status='sent'
            )
            
            db.session.add(notification)
            notifications_created.append(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(notifications_created)} notifications sent successfully',
            'notifications': [n.to_dict() for n in notifications_created]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Dashboard statistics
@alert_bp.route('/alerts/stats', methods=['GET'])
def get_alert_stats():
    """Get alert statistics for dashboard"""
    try:
        # Count alerts by status
        active_alerts = Alert.query.filter_by(status='active').count()
        resolved_alerts = Alert.query.filter_by(status='resolved').count()
        acknowledged_alerts = Alert.query.filter_by(status='acknowledged').count()
        
        # Count alerts by severity
        critical_alerts = Alert.query.filter_by(severity='critical').count()
        high_alerts = Alert.query.filter_by(severity='high').count()
        medium_alerts = Alert.query.filter_by(severity='medium').count()
        low_alerts = Alert.query.filter_by(severity='low').count()
        
        # Count alerts by type
        predictive_failure_alerts = Alert.query.filter_by(type='predictive_failure').count()
        threshold_exceeded_alerts = Alert.query.filter_by(type='threshold_exceeded').count()
        anomaly_alerts = Alert.query.filter_by(type='anomaly').count()
        
        # Recent alerts (last 24 hours)
        from datetime import datetime, timedelta
        recent_alerts = Alert.query.filter(
            Alert.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'by_status': {
                    'active': active_alerts,
                    'resolved': resolved_alerts,
                    'acknowledged': acknowledged_alerts
                },
                'by_severity': {
                    'critical': critical_alerts,
                    'high': high_alerts,
                    'medium': medium_alerts,
                    'low': low_alerts
                },
                'by_type': {
                    'predictive_failure': predictive_failure_alerts,
                    'threshold_exceeded': threshold_exceeded_alerts,
                    'anomaly': anomaly_alerts
                },
                'recent_24h': recent_alerts
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

