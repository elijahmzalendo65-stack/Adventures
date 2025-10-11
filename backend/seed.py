# seed.py
from app import create_app
from app.extensions import db
from app.models.adventure import Adventure
from app.models.user import User
from datetime import datetime

app = create_app()
app.app_context().push()

def seed_adventures():
    """Seed default adventures into the database."""
    # Ensure there is at least one user to assign as creator
    creator = User.query.first()
    if not creator:
        print("No users found. Please create a user first.")
        return

    adventures_data = [
        {
            "id": 101,
            "title": "Budget Package",
            "description": "Perfect for a quick escape from the city",
            "location": "Nairobi & surroundings",
            "price": 7500,
            "duration": "2 days 1 night",
            "difficulty": "Easy",
            "image_url": "https://example.com/budget.jpg",
            "max_capacity": 10,
            "is_active": True,
        },
        {
            "id": 102,
            "title": "Mid-Range Package",
            "description": "Immerse yourself in culture and adventure",
            "location": "Nairobi & nearby counties",
            "price": 14000,
            "duration": "3 days 2 nights",
            "difficulty": "Medium",
            "image_url": "https://example.com/midrange.jpg",
            "max_capacity": 12,
            "is_active": True,
        },
        {
            "id": 103,
            "title": "Premium Package",
            "description": "Complete immersion with overnight stay",
            "location": "Nairobi, Rift Valley & beyond",
            "price": 42000,
            "duration": "4 days 3 nights",
            "difficulty": "Hard",
            "image_url": "https://example.com/premium.jpg",
            "max_capacity": 15,
            "is_active": True,
        },
    ]

    for adv_data in adventures_data:
        # Check if adventure already exists by ID or title
        adventure = Adventure.query.filter(
            (Adventure.id == adv_data["id"]) | (Adventure.title == adv_data["title"])
        ).first()
        if adventure:
            print(f"Adventure '{adv_data['title']}' already exists, skipping...")
            continue

        adventure = Adventure(
            id=adv_data["id"],
            title=adv_data["title"],
            description=adv_data["description"],
            location=adv_data["location"],
            price=adv_data["price"],
            duration=adv_data["duration"],
            difficulty=adv_data["difficulty"],
            image_url=adv_data["image_url"],
            max_capacity=adv_data["max_capacity"],
            is_active=adv_data["is_active"],
            user_id=creator.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(adventure)
        print(f"Added adventure: {adv_data['title']}")

    db.session.commit()
    print("Seeding completed!")

if __name__ == "__main__":
    seed_adventures()
