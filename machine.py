from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='idle')  # 'running', 'idle', 'fault', 'maintenance'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to sensors
    sensors = db.relationship('Sensor', backref='machine', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='machine', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Machine {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sensor_count': len(self.sensors)
        }

class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'temperature', 'humidity', 'tension', 'vibration'
    unit = db.Column(db.String(20), nullable=False)  # '°C', '%RH', 'N', 'g'
    min_value = db.Column(db.Float, nullable=True)
    max_value = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to sensor readings
    readings = db.relationship('SensorReading', backref='sensor', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Sensor {self.name} ({self.type})>'

    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'name': self.name,
            'type': self.type,
            'unit': self.unit,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reading_count': len(self.readings)
        }

class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SensorReading {self.value} at {self.timestamp}>'

    def to_dict(self):
        return {
            'id': self.id,
            'sensor_id': self.sensor_id,
            'value': self.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=True)  # Optional, if alert is sensor-specific
    type = db.Column(db.String(50), nullable=False)  # 'predictive_failure', 'threshold_exceeded', 'anomaly'
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    status = db.Column(db.String(20), default='active')  # 'active', 'resolved', 'acknowledged'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to notifications
    notifications = db.relationship('Notification', backref='alert', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Alert {self.type} - {self.severity}>'

    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'sensor_id': self.sensor_id,
            'type': self.type,
            'message': self.message,
            'severity': self.severity,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    alert_id = db.Column(db.Integer, db.ForeignKey('alert.id'), nullable=False)
    method = db.Column(db.String(20), nullable=False)  # 'email', 'sms', 'in_app'
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='sent')  # 'sent', 'failed', 'read'

    def __repr__(self):
        return f'<Notification {self.method} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'alert_id': self.alert_id,
            'method': self.method,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'status': self.status
        }

