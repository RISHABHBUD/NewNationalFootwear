from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str

    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_FROM: str
    OWNER_WHATSAPP: str
    TWILIO_CONTENT_SID: str = ""  # HX... content template SID

    APP_NAME: str = "NewNational Footwear Stores"
    DELIVERY_CHARGE: int = 150
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    # Email notifications
    SMTP_EMAIL: str = ""       # Gmail address you send FROM
    SMTP_APP_PASSWORD: str = ""  # Gmail App Password (not your login password)
    NOTIFY_ADMIN_EMAIL: str = ""  # Admin email to receive order notifications

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
