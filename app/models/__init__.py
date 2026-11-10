from app import db
from datetime import datetime, timezone


class Message(db.Model):
    __tablename__ = "messages"
    id           = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(50),  nullable=False, index=True)
    direction    = db.Column(db.String(10),  nullable=False)
    content      = db.Column(db.Text,        nullable=True)
    intent       = db.Column(db.String(50),  nullable=True, index=True)
    channel      = db.Column(db.String(20),  nullable=True)
    created_at   = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

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


class User(db.Model):
    __tablename__ = "users"
    id                = db.Column(db.Integer,     primary_key=True)
    phone_number      = db.Column(db.String(50),  unique=True, nullable=False, index=True)
    name              = db.Column(db.String(100), nullable=True)
    preferred_lang    = db.Column(db.String(20),  default="english")
    preferred_channel = db.Column(db.String(20),  default="whatsapp")
    due_date          = db.Column(db.Date,        nullable=True)
    village           = db.Column(db.String(100), nullable=True)
    last_intent       = db.Column(db.String(50),  nullable=True)
    registered_at     = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id":             self.id,
            "phone_number":   self.phone_number,
            "name":           self.name,
            "preferred_lang": self.preferred_lang,
            "due_date":       self.due_date.isoformat() if self.due_date else None,
            "village":        self.village,
            "registered_at":  self.registered_at.isoformat() if self.registered_at else None,
        }
