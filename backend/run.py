import os
from app import create_app
from app.extensions import db
from app.models.user import User
from dotenv import load_dotenv

load_dotenv()

app = create_app()

def create_admin_user():
    """Create an admin user if none exists"""
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
            print("Admin user created: username='admin', password='admin123'")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT']
    )