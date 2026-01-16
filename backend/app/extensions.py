# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
cors = CORS()

# Configure Flask-Login
login_manager.login_view = 'auth.login'  # This should match your login route
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login user loader callback.
    This function loads a user from the database given their user_id.
    """
    from .models.user import User  # Import inside function to avoid circular imports
    
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None