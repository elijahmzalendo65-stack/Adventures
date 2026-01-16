# run.py (REMOVE the route definitions, keep only app setup)
import os
from dotenv import load_dotenv
from app import create_app
from app.extensions import db
from app.models.user import User

load_dotenv()

app = create_app()

def create_admin_user():
    """
    Create a default admin user if none exists.
    Admin credentials:
    email: admin456@gmail.com
    password: admin456
    """
    try:
        with app.app_context():
            admin = User.query.filter_by(email="admin456@gmail.com").first()

            if not admin:
                admin = User(
                    username="admin456",
                    email="admin456@gmail.com",
                    phone_number="254700000456",
                    is_admin=True
                )
                admin.set_password("admin456")
                db.session.add(admin)
                db.session.commit()

                print("\n✅ Admin user created:")
                print("   Email: admin456@gmail.com")
                print("   Password: admin456")
            else:
                # Ensure admin flag is always true
                if not admin.is_admin:
                    admin.is_admin = True
                    db.session.commit()
                    print("\n🔁 Existing user promoted to admin")
                else:
                    print("\nℹ️ Admin user already exists")

    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Failed to create admin user: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting Mlima Adventures Application")
    print("="*60 + "\n")
    
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables ensured")
        except Exception as e:
            print(f"❌ Database error: {e}")

        create_admin_user()
    
    print("\n" + "="*60)
    print("🌐 Application URLs:")
    print("   Frontend: http://localhost:5000/")
    print("   API:      http://localhost:5000/api/health")
    print("   Admin:    http://localhost:5000/admin")
    print("="*60 + "\n")
    
    app.run(
        debug=app.config.get("DEBUG", True),
        host="127.0.0.1",
        port=5000
    )