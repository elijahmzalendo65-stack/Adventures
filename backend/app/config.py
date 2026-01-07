import os
from decouple import config

class Config:
    # Flask
    SECRET_KEY = config('SECRET_KEY', default='dev-secret-key')
    DEBUG = config('DEBUG', default=True, cast=bool)
    
    # Database
    SQLALCHEMY_DATABASE_URI = config(
        'DATABASE_URL', 
        default='postgresql://postgres:newpassword@localhost:5432/adventures_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
   
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds
    
   
    MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='')
    MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
    MPESA_PASSKEY = config('MPESA_PASSKEY', default='')
    MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='174379')
    MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default='')
    
    HOST = config('HOST', default='0.0.0.0')
    PORT = config('PORT', default=5000, cast=int)
