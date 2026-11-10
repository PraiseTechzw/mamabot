import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    SECRET_KEY             = os.environ.get("SECRET_KEY")
    # Twilio — WhatsApp
    TWILIO_ACCOUNT_SID     = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN      = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    TWILIO_WHATSAPP_REMINDER_CONTENT_SID = os.environ.get("TWILIO_WHATSAPP_REMINDER_CONTENT_SID")
    # SMSPoP — outbound Zimbabwe SMS
    SMSPOP_API_TOKEN       = os.environ.get("SMSPOP_API_TOKEN")
    SMSPOP_SENDER_ID       = os.environ.get("SMSPOP_SENDER_ID")
    SMSPOP_WEBHOOK_SECRET  = os.environ.get("SMSPOP_WEBHOOK_SECRET")
    SMSPOP_DELIVERY_REPORT_URL = os.environ.get("SMSPOP_DELIVERY_REPORT_URL")
    # Supabase
    SUPABASE_URL           = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY           = os.environ.get("SUPABASE_KEY")
    # Admin
    ADMIN_PASSWORD         = os.environ.get("ADMIN_PASSWORD")
    CONFIDENCE_THRESHOLD   = float(os.environ.get("CONFIDENCE_THRESHOLD", 0.38))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
