import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.user import User, db
from src.models.machine import Alert, Notification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

class NotificationService:
    """Service for sending notifications via email and other channels"""
    
    def __init__(self):
        # Email configuration (should be moved to environment variables in production)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_user = "maintai.system@gmail.com"  # Configure with actual email
        self.email_password = "your_app_password"  # Configure with actual password
        
    def send_email_notification(self, to_email, subject, message, alert_data=None):
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Create HTML body
            html_body = self.create_email_template(message, alert_data)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            
            logger.info(f"Email notification sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def create_email_template(self, message, alert_data=None):
        """Create HTML email template"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
                .content {{ padding: 20px; }}
                .alert-info {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 15px 0; }}
                .critical {{ background-color: #fee2e2; border-left-color: #ef4444; }}
                .high {{ background-color: #fed7aa; border-left-color: #f97316; }}
                .medium {{ background-color: #fef3c7; border-left-color: #f59e0b; }}
                .low {{ background-color: #dbeafe; border-left-color: #3b82f6; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                .button {{ display: inline-block; background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏭 MaintAI Alert System</h1>
                    <p>Predictive Failure Machine Monitoring</p>
                </div>
                <div class="content">
                    <h2>Alert Notification</h2>
                    <p>{message}</p>
        """
        
        if alert_data:
            severity_class = alert_data.get('severity', 'medium')
            html += f"""
                    <div class="alert-info {severity_class}">
                        <h3>Alert Details</h3>
                        <p><strong>Machine:</strong> {alert_data.get('machine_name', 'Unknown')}</p>
                        <p><strong>Sensor:</strong> {alert_data.get('sensor_name', 'Unknown')}</p>
                        <p><strong>Type:</strong> {alert_data.get('type', 'Unknown')}</p>
                        <p><strong>Severity:</strong> {alert_data.get('severity', 'Unknown').upper()}</p>
                        <p><strong>Timestamp:</strong> {alert_data.get('timestamp', 'Unknown')}</p>
                        <p><strong>Value:</strong> {alert_data.get('value', 'N/A')} {alert_data.get('unit', '')}</p>
                    </div>
            """
        
        html += f"""
                    <p>Please log into the MaintAI system to view more details and take appropriate action.</p>
                    <a href="http://localhost:5173/dashboard" class="button">View Dashboard</a>
                </div>
                <div class="footer">
                    <p>This is an automated message from MaintAI Predictive Failure System</p>
                    <p>Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_sms_notification(self, phone_number, message):
        """Send SMS notification (placeholder - integrate with SMS service)"""
        # This would integrate with services like Twilio, AWS SNS, etc.
        logger.info(f"SMS notification would be sent to {phone_number}: {message}")
        return True
    
    def send_webhook_notification(self, webhook_url, data):
        """Send webhook notification to external systems"""
        try:
            import requests
            response = requests.post(webhook_url, json=data, timeout=10)
            response.raise_for_status()
            logger.info(f"Webhook notification sent to {webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to send webhook to {webhook_url}: {e}")
            return False

# Initialize notification service
notification_service = NotificationService()

@notifications_bp.route('/send', methods=['POST'])
def send_notification():
    """Send notification to users"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notification_type = data.get('type', 'email')
        recipients = data.get('recipients', [])
        subject = data.get('subject', 'MaintAI Alert')
        message = data.get('message', '')
        alert_data = data.get('alert_data')
        
        if not recipients or not message:
            return jsonify({'error': 'Recipients and message are required'}), 400
        
        sent_count = 0
        failed_count = 0
        
        for recipient in recipients:
            try:
                if notification_type == 'email':
                    success = notification_service.send_email_notification(
                        recipient, subject, message, alert_data
                    )
                elif notification_type == 'sms':
                    success = notification_service.send_sms_notification(
                        recipient, message
                    )
                else:
                    success = False
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send notification to {recipient}: {e}")
                failed_count += 1
        
        return jsonify({
            'status': 'completed',
            'sent': sent_count,
            'failed': failed_count,
            'total': len(recipients)
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending notifications: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notifications_bp.route('/alert/<int:alert_id>/notify', methods=['POST'])
def notify_alert(alert_id):
    """Send notifications for a specific alert"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        
        # Get users to notify based on alert severity and user roles
        users_to_notify = get_users_for_alert(alert)
        
        if not users_to_notify:
            return jsonify({'message': 'No users to notify'}), 200
        
        # Prepare alert data for notification
        alert_data = {
            'machine_name': alert.machine.name if alert.machine else 'Unknown',
            'sensor_name': alert.sensor.name if alert.sensor else 'Unknown',
            'type': alert.type,
            'severity': alert.severity,
            'timestamp': alert.timestamp.isoformat(),
            'value': getattr(alert.sensor, 'last_reading_value', 'N/A') if alert.sensor else 'N/A',
            'unit': alert.sensor.unit if alert.sensor else ''
        }
        
        subject = f"MaintAI Alert: {alert.severity.upper()} - {alert_data['machine_name']}"
        
        sent_count = 0
        failed_count = 0
        
        for user in users_to_notify:
            try:
                # Send email notification
                success = notification_service.send_email_notification(
                    user.email, subject, alert.message, alert_data
                )
                
                # Create notification record
                notification = Notification(
                    user_id=user.id,
                    alert_id=alert.id,
                    type='email',
                    status='sent' if success else 'failed',
                    message=alert.message
                )
                db.session.add(notification)
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to notify user {user.email}: {e}")
                failed_count += 1
        
        db.session.commit()
        
        return jsonify({
            'status': 'completed',
            'alert_id': alert_id,
            'sent': sent_count,
            'failed': failed_count,
            'total': len(users_to_notify)
        }), 200
        
    except Exception as e:
        logger.error(f"Error notifying alert {alert_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

def get_users_for_alert(alert):
    """Get list of users to notify based on alert severity and user roles"""
    users = []
    
    # Critical alerts: notify all engineers and admins
    if alert.severity == 'critical':
        users = User.query.filter(User.role.in_(['engineer', 'admin'])).all()
    
    # High alerts: notify engineers and admins
    elif alert.severity == 'high':
        users = User.query.filter(User.role.in_(['engineer', 'admin'])).all()
    
    # Medium alerts: notify engineers
    elif alert.severity == 'medium':
        users = User.query.filter_by(role='engineer').all()
    
    # Low alerts: log only, no notifications
    else:
        users = []
    
    return users

@notifications_bp.route('/test', methods=['POST'])
def test_notification():
    """Test notification system"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        test_alert_data = {
            'machine_name': 'Test Machine',
            'sensor_name': 'Test Temperature Sensor',
            'type': 'test',
            'severity': 'medium',
            'timestamp': datetime.utcnow().isoformat(),
            'value': '75.5',
            'unit': '°C'
        }
        
        success = notification_service.send_email_notification(
            email,
            "MaintAI Test Notification",
            "This is a test notification from the MaintAI system.",
            test_alert_data
        )
        
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'Test notification sent' if success else 'Failed to send test notification'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notifications_bp.route('/webhook', methods=['POST'])
def webhook_endpoint():
    """Webhook endpoint for external systems to send notifications"""
    try:
        data = request.get_json()
        
        # Log webhook data
        logger.info(f"Received webhook data: {data}")
        
        # Process webhook data and potentially create alerts
        # This is a placeholder for webhook processing logic
        
        return jsonify({
            'status': 'received',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notifications_bp.route('/settings', methods=['GET', 'POST'])
def notification_settings():
    """Get or update notification settings"""
    if request.method == 'GET':
        # Return current notification settings
        settings = {
            'email_enabled': True,
            'sms_enabled': False,
            'webhook_enabled': True,
            'severity_thresholds': {
                'critical': ['engineer', 'admin'],
                'high': ['engineer', 'admin'],
                'medium': ['engineer'],
                'low': []
            }
        }
        return jsonify(settings), 200
    
    elif request.method == 'POST':
        # Update notification settings
        data = request.get_json()
        
        # In a real application, you would save these settings to the database
        logger.info(f"Notification settings updated: {data}")
        
        return jsonify({
            'status': 'updated',
            'settings': data
        }), 200

