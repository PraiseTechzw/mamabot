"""
app/models/message.py
"""

from app import db
from datetime import datetime, timezone


class Message(db.Model):
    __tablename__ = "messages"

    id           = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(50),  nullable=False, index=True)
    direction    = db.Column(db.String(10),  nullable=False)   # 'inbound' | 'outbound'
    content      = db.Column(db.Text,        nullable=True)
    intent       = db.Column(db.String(50),  nullable=True,  index=True)
    channel      = db.Column(db.String(20),  nullable=True)   # 'whatsapp' | 'sms'
    created_at   = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Message {self.id} {self.direction} {self.intent}>"

    def to_dict(self):
        return {
            "id":           self.id,
            "phone_number": self.phone_number,
            "direction":    self.direction,
            "content":      self.content,
            "intent":       self.intent,
            "channel":      self.channel,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
        }
