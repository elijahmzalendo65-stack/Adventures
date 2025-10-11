# run.py

import os
from dotenv import load_dotenv
from app import create_app
from app.extensions import db
from app.models.user import User

# Load environment variables from .env
load_dotenv()

# Create the Flask app
app = create_app()


def create_admin_user():
    """Create a default admin user if none exists."""
    try:
        with app.app_context():
            admin_exists = User.query.filter_by(is_admin=True).first()
            if not admin_exists:
                admin_user = User(
                    username='admin',
                    email='admin@adventures.com',
                    phone_number='254700000000',
                    is_admin=True
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Admin user created: username='admin', password='admin123'")
            else:
                print("ℹ️ Admin user already exists.")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to create admin user: {e}")


if __name__ == '__main__':
    with app.app_context():
        # Create all tables if they do not exist
        try:
            db.create_all()
            print("✅ All tables created successfully.")
        except Exception as e:
            print(f"❌ Failed to create tables: {e}")

        # Ensure there is a default admin user
        create_admin_user()

    # Run the Flask app
    app.run(
        debug=app.config.get('DEBUG', True),
        host=app.config.get('HOST', '127.0.0.1'),
        port=int(app.config.get('PORT', 5000))
    )
