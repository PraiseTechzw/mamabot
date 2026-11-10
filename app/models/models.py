from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    channel = db.Column(db.String(10), default="sms")  # 'sms' or 'whatsapp'
    preferred_language = db.Column(db.String(5), default="en")  # 'en', 'sn', 'nd'
    gestational_age_weeks = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = db.relationship("Message", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.phone_number}>"


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    direction = db.Column(db.String(3))  # 'in' or 'out'
    content = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(50), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    detected_language = db.Column(db.String(5), nullable=True)
    channel = db.Column(db.String(10), default="sms")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Message {self.direction} | {self.intent} | {self.timestamp}>"


class EscalationLog(db.Model):
    __tablename__ = "escalation_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trigger_message = db.Column(db.Text, nullable=False)
    action_taken = db.Column(db.String(100))  # e.g. "emergency_sms_sent"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Make importable as: from app.models import Message
Message = Message   # already defined above
User = User         # already defined above
