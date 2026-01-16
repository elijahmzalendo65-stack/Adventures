# app/routes/adventures.py - UPDATED VERSION
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from ..extensions import db
from ..models.adventure import Adventure
from ..models.user import User
from ..utils.helpers import login_required, admin_required, validate_required_fields
import logging
import traceback

logger = logging.getLogger(__name__)

adventures_bp = Blueprint('adventures', __name__, url_prefix='/api/adventures')


# -----------------------------
# Helper Functions
# -----------------------------
def get_all_adventure_ids():
    """Get all adventure IDs and basic info."""
    try:
        adventures = Adventure.query.with_entities(
            Adventure.id, 
            Adventure.title, 
            Adventure.is_active, 
            Adventure.price,
            Adventure.max_capacity,
            Adventure.created_at
        ).all()
        
        return [
            {
                "id": adv.id,
                "title": adv.title,
                "is_active": adv.is_active,
                "price": float(adv.price) if adv.price else 0,
                "max_capacity": adv.max_capacity,
                "created_at": adv.created_at.isoformat() if adv.created_at else None
            }
            for adv in adventures
        ]
    except Exception as e:
        logger.error(f"Error getting adventure IDs: {str(e)}")
        return []


# -----------------------------
# Debug: Check adventure exists
# -----------------------------
@adventures_bp.route('/debug/check/<int:adventure_id>', methods=['GET'])
def check_adventure_exists(adventure_id):
    """Check if an adventure exists and is active."""
    try:
        logger.debug(f"Checking adventure ID: {adventure_id}")
        
        adventure = Adventure.query.filter_by(id=adventure_id).first()
        
        if not adventure:
            return jsonify({
                "exists": False,
                "active": False,
                "message": f"Adventure with ID {adventure_id} not found in database",
                "available_ids": get_all_adventure_ids()
            }), 404
        
        return jsonify({
            "exists": True,
            "active": adventure.is_active,
            "adventure": adventure.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking adventure {adventure_id}: {str(e)}")
        return jsonify({
            "error": "Failed to check adventure",
            "details": str(e)
        }), 500


# -----------------------------
# Debug: Get all adventure IDs
# -----------------------------
@adventures_bp.route('/debug/all-ids', methods=['GET'])
def debug_all_adventure_ids():
    """Get all adventure IDs and names."""
    try:
        adventures = Adventure.query.all()
        
        adventures_list = []
        for adv in adventures:
            adventures_list.append({
                "id": adv.id,
                "title": adv.title,
                "description": adv.description[:100] + "..." if adv.description and len(adv.description) > 100 else adv.description,
                "is_active": adv.is_active,
                "price": float(adv.price) if adv.price else 0,
                "max_capacity": adv.max_capacity,
                "created_at": adv.created_at.isoformat() if adv.created_at else None
            })
        
        return jsonify({
            "count": len(adventures_list),
            "adventures": adventures_list
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting all adventure IDs: {str(e)}")
        return jsonify({
            "error": "Failed to fetch adventures",
            "details": str(e)
        }), 500


# -----------------------------
# Debug: Create test adventure 101
# -----------------------------
@adventures_bp.route('/debug/create-test-101', methods=['POST'])
def create_test_adventure_101():
    """Create adventure with ID 101 for testing."""
    try:
        logger.debug("Creating test adventure 101")
        
        # Check if already exists
        existing = Adventure.query.filter_by(id=101).first()
        if existing:
            return jsonify({
                "message": "Adventure 101 already exists",
                "adventure": existing.to_dict()
            }), 200
        
        # Get the first user to be the creator
        first_user = User.query.first()
        if not first_user:
            # Create a test user if none exists
            from werkzeug.security import generate_password_hash
            test_user = User(
                username="testuser101",
                email="test101@example.com",
                password_hash=generate_password_hash("password123"),
                phone_number="0712345678"
            )
            db.session.add(test_user)
            db.session.commit()
            first_user = test_user
            logger.debug(f"Created test user with ID: {first_user.id}")
        
        # Create the adventure
        adventure = Adventure(
            id=101,
            title="Premium Safari Experience",
            description="Experience the wild like never before with our premium safari package. Enjoy luxury accommodations, expert guides, and exclusive wildlife viewing.",
            location="Maasai Mara National Reserve",
            price=15000.00,
            duration="3 days",
            difficulty="Medium",
            image_url="/images/safari-premium.jpg",
            max_capacity=10,
            is_active=True,
            user_id=first_user.id
        )
        
        db.session.add(adventure)
        db.session.commit()
        
        logger.info(f"Created adventure 101: {adventure.title}")
        
        return jsonify({
            "message": "Adventure 101 created successfully",
            "adventure": adventure.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        logger.error("Integrity error creating adventure 101")
        return jsonify({
            "message": "Adventure ID 101 might already exist",
            "error": "Integrity error"
        }), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create adventure 101: {str(e)}")
        return jsonify({
            "message": f"Failed to create adventure: {str(e)}",
            "error_type": type(e).__name__
        }), 500


# -----------------------------
# Debug: Create test adventure 102
# -----------------------------
@adventures_bp.route('/debug/create-test-102', methods=['POST'])
def create_test_adventure_102():
    """Create adventure with ID 102 for testing."""
    try:
        logger.debug("Creating test adventure 102")
        
        # Check if already exists
        existing = Adventure.query.filter_by(id=102).first()
        if existing:
            return jsonify({
                "message": "Adventure 102 already exists",
                "adventure": existing.to_dict()
            }), 200
        
        # Get the first user to be the creator
        first_user = User.query.first()
        if not first_user:
            # Create a test user if none exists
            from werkzeug.security import generate_password_hash
            test_user = User(
                username="testuser102",
                email="test102@example.com",
                password_hash=generate_password_hash("password123"),
                phone_number="0712345679"
            )
            db.session.add(test_user)
            db.session.commit()
            first_user = test_user
            logger.debug(f"Created test user with ID: {first_user.id}")
        
        # Create the adventure
        adventure = Adventure(
            id=102,
            title="Mountain Hiking Adventure",
            description="Challenge yourself with our expert-guided mountain trek. Perfect for adventure seekers looking for a physical challenge.",
            location="Mount Kenya",
            price=8000.00,
            duration="2 days",
            difficulty="Hard",
            image_url="/images/mountain-hike.jpg",
            max_capacity=8,
            is_active=True,
            user_id=first_user.id
        )
        
        db.session.add(adventure)
        db.session.commit()
        
        logger.info(f"Created adventure 102: {adventure.title}")
        
        return jsonify({
            "message": "Adventure 102 created successfully",
            "adventure": adventure.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        logger.error("Integrity error creating adventure 102")
        return jsonify({
            "message": "Adventure ID 102 might already exist",
            "error": "Integrity error"
        }), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create adventure 102: {str(e)}")
        return jsonify({
            "message": f"Failed to create adventure: {str(e)}",
            "error_type": type(e).__name__
        }), 500


# -----------------------------
# Debug: Create multiple test adventures
# -----------------------------
@adventures_bp.route('/debug/create-test-batch', methods=['POST'])
def create_test_adventures_batch():
    """Create multiple test adventures."""
    try:
        data = request.get_json() or {}
        count = data.get('count', 5)
        
        first_user = User.query.first()
        if not first_user:
            from werkzeug.security import generate_password_hash
            first_user = User(
                username="batch_user",
                email="batch@example.com",
                password_hash=generate_password_hash("password123"),
                phone_number="0700000000"
            )
            db.session.add(first_user)
            db.session.commit()
        
        test_adventures = [
            {
                "title": "Beach Getaway",
                "description": "Relax on pristine beaches with crystal clear waters.",
                "location": "Diani Beach",
                "price": 12000.00,
                "difficulty": "Easy"
            },
            {
                "title": "Cultural Tour",
                "description": "Experience local culture and traditions.",
                "location": "Lamu Island",
                "price": 9000.00,
                "difficulty": "Easy"
            },
            {
                "title": "Wildlife Safari",
                "description": "See the Big Five in their natural habitat.",
                "location": "Amboseli National Park",
                "price": 18000.00,
                "difficulty": "Medium"
            },
            {
                "title": "Desert Adventure",
                "description": "Explore the vast desert landscapes.",
                "location": "Samburu",
                "price": 14000.00,
                "difficulty": "Hard"
            },
            {
                "title": "Lake Exploration",
                "description": "Boat rides and bird watching at the lake.",
                "location": "Lake Nakuru",
                "price": 7500.00,
                "difficulty": "Easy"
            }
        ]
        
        created = []
        for i, adv_data in enumerate(test_adventures[:count]):
            # Find next available ID
            last_adventure = Adventure.query.order_by(Adventure.id.desc()).first()
            next_id = (last_adventure.id + 1) if last_adventure else 200 + i
            
            adventure = Adventure(
                id=next_id,
                title=adv_data["title"],
                description=adv_data["description"],
                location=adv_data["location"],
                price=adv_data["price"],
                duration="2 days",
                difficulty=adv_data["difficulty"],
                image_url=f"/images/{adv_data['title'].lower().replace(' ', '-')}.jpg",
                max_capacity=12,
                is_active=True,
                user_id=first_user.id
            )
            
            db.session.add(adventure)
            created.append({
                "id": adventure.id,
                "title": adventure.title,
                "price": float(adventure.price)
            })
        
        db.session.commit()
        
        return jsonify({
            "message": f"Created {len(created)} test adventures",
            "adventures": created
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create batch adventures: {str(e)}")
        return jsonify({
            "message": f"Failed to create adventures: {str(e)}"
        }), 500


# -----------------------------
# Debug: Activate adventure if exists
# -----------------------------
@adventures_bp.route('/debug/activate/<int:adventure_id>', methods=['POST'])
def activate_adventure(adventure_id):
    """Activate an adventure if it exists."""
    try:
        adventure = Adventure.query.filter_by(id=adventure_id).first()
        
        if not adventure:
            return jsonify({
                "success": False,
                "message": f"Adventure with ID {adventure_id} not found"
            }), 404
        
        adventure.is_active = True
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Adventure {adventure_id} activated",
            "adventure": adventure.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to activate adventure {adventure_id}: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to activate adventure: {str(e)}"
        }), 500


# -----------------------------
# Debug: Reset all adventures to active
# -----------------------------
@adventures_bp.route('/debug/activate-all', methods=['POST'])
def activate_all_adventures():
    """Activate all adventures."""
    try:
        updated = Adventure.query.filter_by(is_active=False).update({'is_active': True})
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Activated {updated} adventures",
            "activated_count": updated
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to activate all adventures: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to activate adventures: {str(e)}"
        }), 500


# -----------------------------
# Fetch all active adventures
# -----------------------------
@adventures_bp.route('/', methods=['GET'])
def get_adventures():
    """Get all active adventures."""
    try:
        adventures = Adventure.query.filter_by(is_active=True).all()
        logger.debug(f"Found {len(adventures)} active adventures")
        
        # Ensure all prices are float
        adventures_data = []
        for adv in adventures:
            adv_dict = adv.to_dict()
            adv_dict['price'] = float(adv.price) if adv.price else 0
            adventures_data.append(adv_dict)
        
        return jsonify(adventures_data), 200
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching adventures: {str(e)}")
        return jsonify({
            'message': 'Database error fetching adventures',
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Failed to fetch adventures: {str(e)}")
        return jsonify({
            'message': 'Failed to fetch adventures',
            'error': str(e)
        }), 500


# -----------------------------
# Fetch all adventures for admin
# -----------------------------
@adventures_bp.route('/admin/all', methods=['GET'])
@admin_required
def get_all_adventures_admin():
    try:
        adventures = Adventure.query.order_by(Adventure.created_at.desc()).all()
        result = []
        for adv in adventures:
            adv_data = adv.to_dict()
            adv_data['price'] = float(adv.price) if adv.price else 0
            
            creator = User.query.get(adv.user_id)
            adv_data['creator'] = {
                'id': creator.id,
                'username': creator.username,
                'email': creator.email,
                'phone_number': creator.phone_number,
                'is_admin': creator.is_admin
            } if creator else None
            result.append(adv_data)
            
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Failed to fetch adventures for admin: {str(e)}")
        return jsonify({
            'message': 'Failed to fetch adventures for admin',
            'error': str(e)
        }), 500


# -----------------------------
# Fetch single adventure
# -----------------------------
@adventures_bp.route('/<int:adventure_id>', methods=['GET'])
def get_adventure(adventure_id):
    """Get a single adventure by ID."""
    try:
        adventure = Adventure.query.get(adventure_id)
        if not adventure:
            logger.warning(f"Adventure {adventure_id} not found")
            return jsonify({
                'message': 'Adventure not found',
                'adventure_id': adventure_id,
                'available_ids': get_all_adventure_ids()
            }), 404
        
        if not adventure.is_active:
            logger.warning(f"Adventure {adventure_id} is inactive")
            return jsonify({
                'message': 'Adventure is not active',
                'adventure_id': adventure_id,
                'adventure': adventure.to_dict()
            }), 404
            
        adv_dict = adventure.to_dict()
        adv_dict['price'] = float(adventure.price) if adventure.price else 0
        
        return jsonify(adv_dict), 200
    except Exception as e:
        logger.error(f"Failed to fetch adventure {adventure_id}: {str(e)}")
        return jsonify({
            'message': 'Failed to fetch adventure',
            'error': str(e)
        }), 500


# -----------------------------
# Create new adventure
# -----------------------------
@adventures_bp.route('/', methods=['POST'])
@login_required
def create_adventure():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        logger.debug(f"Creating adventure for user {user_id}: {data}")

        required_fields = ['title', 'description', 'location', 'price']
        is_valid, error_message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({'message': error_message}), 400

        # Validate price is a number
        try:
            price = float(data['price'])
            if price < 0:
                return jsonify({'message': 'Price must be non-negative'}), 400
        except (ValueError, TypeError):
            return jsonify({'message': 'Price must be a valid number'}), 400

        adventure = Adventure(
            title=data['title'],
            description=data['description'],
            location=data['location'],
            price=price,
            duration=data.get('duration'),
            difficulty=data.get('difficulty'),
            image_url=data.get('image_url'),
            max_capacity=data.get('max_capacity', 10),
            user_id=user_id,
            is_active=data.get('is_active', True)
        )

        db.session.add(adventure)
        db.session.commit()
        
        logger.info(f"Created adventure {adventure.id}: {adventure.title}")

        adv_dict = adventure.to_dict()
        adv_dict['price'] = float(adventure.price)
        
        return jsonify({
            'message': 'Adventure created successfully',
            'adventure': adv_dict
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Integrity error creating adventure: {str(e)}")
        return jsonify({
            'message': 'Adventure creation failed due to database constraint',
            'error': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create adventure: {str(e)}")
        return jsonify({
            'message': 'Failed to create adventure',
            'error': str(e)
        }), 500


# -----------------------------
# Update existing adventure
# -----------------------------
@adventures_bp.route('/<int:adventure_id>', methods=['PUT'])
@login_required
def update_adventure(adventure_id):
    try:
        user_id = session.get('user_id')
        adventure = Adventure.query.get(adventure_id)
        
        if not adventure:
            return jsonify({'message': 'Adventure not found'}), 404

        # Check if user is creator or admin
        user = User.query.get(user_id)
        if adventure.user_id != user_id and not (user and user.is_admin):
            return jsonify({'message': 'Unauthorized'}), 403

        data = request.get_json() or {}
        logger.debug(f"Updating adventure {adventure_id}: {data}")
        
        # Update fields
        for field in ['title', 'description', 'location', 'duration', 
                     'difficulty', 'image_url', 'max_capacity', 'is_active']:
            if field in data:
                setattr(adventure, field, data[field])
        
        # Special handling for price
        if 'price' in data:
            try:
                price = float(data['price'])
                if price < 0:
                    return jsonify({'message': 'Price must be non-negative'}), 400
                adventure.price = price
            except (ValueError, TypeError):
                return jsonify({'message': 'Price must be a valid number'}), 400

        db.session.commit()
        
        logger.info(f"Updated adventure {adventure_id}")

        adv_dict = adventure.to_dict()
        adv_dict['price'] = float(adventure.price)
        
        return jsonify({
            'message': 'Adventure updated successfully',
            'adventure': adv_dict
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update adventure {adventure_id}: {str(e)}")
        return jsonify({
            'message': 'Failed to update adventure',
            'error': str(e)
        }), 500


# -----------------------------
# Soft delete adventure
# -----------------------------
@adventures_bp.route('/<int:adventure_id>', methods=['DELETE'])
@login_required
def delete_adventure(adventure_id):
    try:
        user_id = session.get('user_id')
        adventure = Adventure.query.get(adventure_id)
        
        if not adventure:
            return jsonify({'message': 'Adventure not found'}), 404

        # Check if user is creator or admin
        user = User.query.get(user_id)
        if adventure.user_id != user_id and not (user and user.is_admin):
            return jsonify({'message': 'Unauthorized'}), 403

        adventure.is_active = False
        db.session.commit()
        
        logger.info(f"Soft deleted adventure {adventure_id}")

        return jsonify({
            'message': 'Adventure deleted successfully',
            'adventure_id': adventure_id
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete adventure {adventure_id}: {str(e)}")
        return jsonify({
            'message': 'Failed to delete adventure',
            'error': str(e)
        }), 500


# -----------------------------
# Fetch logged-in user's adventures
# -----------------------------
@adventures_bp.route('/my-adventures', methods=['GET'])
@login_required
def get_my_adventures():
    try:
        user_id = session.get('user_id')
        adventures = Adventure.query.filter_by(user_id=user_id).all()
        logger.debug(f"Found {len(adventures)} adventures for user {user_id}")
        
        adventures_data = []
        for adv in adventures:
            adv_dict = adv.to_dict()
            adv_dict['price'] = float(adv.price) if adv.price else 0
            adventures_data.append(adv_dict)
            
        return jsonify(adventures_data), 200
    except Exception as e:
        logger.error(f"Failed to fetch adventures for user {user_id}: {str(e)}")
        return jsonify({
            'message': 'Failed to fetch your adventures',
            'error': str(e)
        }), 500


# -----------------------------
# Search adventures
# -----------------------------
@adventures_bp.route('/search', methods=['GET'])
def search_adventures():
    try:
        query = request.args.get('q', '').strip()
        location = request.args.get('location', '').strip()
        difficulty = request.args.get('difficulty', '').strip()
        max_price = request.args.get('max_price')
        
        base_query = Adventure.query.filter_by(is_active=True)
        
        if query:
            base_query = base_query.filter(
                (Adventure.title.ilike(f'%{query}%')) | 
                (Adventure.description.ilike(f'%{query}%'))
            )
        
        if location:
            base_query = base_query.filter(Adventure.location.ilike(f'%{location}%'))
        
        if difficulty:
            base_query = base_query.filter(Adventure.difficulty == difficulty)
        
        if max_price:
            try:
                max_price_float = float(max_price)
                base_query = base_query.filter(Adventure.price <= max_price_float)
            except ValueError:
                pass
        
        adventures = base_query.all()
        
        adventures_data = []
        for adv in adventures:
            adv_dict = adv.to_dict()
            adv_dict['price'] = float(adv.price) if adv.price else 0
            adventures_data.append(adv_dict)
        
        return jsonify({
            'count': len(adventures_data),
            'adventures': adventures_data
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to search adventures: {str(e)}")
        return jsonify({
            'message': 'Failed to search adventures',
            'error': str(e)
        }), 500


# -----------------------------
# Health check
# -----------------------------
@adventures_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        count = Adventure.query.count()
        active_count = Adventure.query.filter_by(is_active=True).count()
        
        return jsonify({
            "status": "healthy",
            "service": "adventures-service",
            "total_adventures": count,
            "active_adventures": active_count,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "adventures-service",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


# -----------------------------
# Get featured adventures
# -----------------------------
@adventures_bp.route('/featured', methods=['GET'])
def get_featured_adventures():
    """Get featured adventures."""
    try:
        # Get 3 most recent active adventures
        adventures = Adventure.query.filter_by(is_active=True)\
            .order_by(Adventure.created_at.desc())\
            .limit(3)\
            .all()
        
        adventures_data = []
        for adv in adventures:
            adv_dict = adv.to_dict()
            adv_dict['price'] = float(adv.price) if adv.price else 0
            adventures_data.append(adv_dict)
        
        return jsonify(adventures_data), 200
    except Exception as e:
        logger.error(f"Failed to fetch featured adventures: {str(e)}")
        return jsonify({
            'message': 'Failed to fetch featured adventures',
            'error': str(e)
        }), 500


# -----------------------------
# Debug: Get database statistics
# -----------------------------
@adventures_bp.route('/debug/stats', methods=['GET'])
def get_adventure_stats():
    """Get adventure statistics."""
    try:
        total = Adventure.query.count()
        active = Adventure.query.filter_by(is_active=True).count()
        inactive = total - active
        
        # Get price statistics
        price_stats = db.session.query(
            db.func.min(Adventure.price).label('min_price'),
            db.func.max(Adventure.price).label('max_price'),
            db.func.avg(Adventure.price).label('avg_price')
        ).filter_by(is_active=True).first()
        
        # Get difficulty distribution
        difficulties = db.session.query(
            Adventure.difficulty,
            db.func.count(Adventure.id).label('count')
        ).filter_by(is_active=True).group_by(Adventure.difficulty).all()
        
        return jsonify({
            "statistics": {
                "total_adventures": total,
                "active_adventures": active,
                "inactive_adventures": inactive,
                "price_stats": {
                    "min": float(price_stats.min_price) if price_stats.min_price else 0,
                    "max": float(price_stats.max_price) if price_stats.max_price else 0,
                    "average": float(price_stats.avg_price) if price_stats.avg_price else 0
                },
                "difficulty_distribution": [
                    {"difficulty": diff, "count": cnt}
                    for diff, cnt in difficulties
                ]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get adventure stats: {str(e)}")
        return jsonify({
            "error": "Failed to get statistics",
            "details": str(e)
        }), 500