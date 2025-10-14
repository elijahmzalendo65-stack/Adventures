from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models.adventure import Adventure
from ..models.user import User
from ..utils.helpers import login_required, admin_required, validate_required_fields

adventures_bp = Blueprint('adventures', __name__, url_prefix='/api/adventures')


# -----------------------------
# Fetch all active adventures
# -----------------------------
@adventures_bp.route('/', methods=['GET'])
def get_adventures():
    try:
        adventures = Adventure.query.filter_by(is_active=True).all()
        return jsonify([adv.to_dict() for adv in adventures]), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch adventures', 'error': str(e)}), 500


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
        return jsonify({'message': 'Failed to fetch adventures for admin', 'error': str(e)}), 500


# -----------------------------
# Fetch single adventure
# -----------------------------
@adventures_bp.route('/<int:adventure_id>', methods=['GET'])
def get_adventure(adventure_id):
    try:
        adventure = Adventure.query.get_or_404(adventure_id)
        return jsonify(adventure.to_dict()), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch adventure', 'error': str(e)}), 500


# -----------------------------
# Create new adventure
# -----------------------------
@adventures_bp.route('/', methods=['POST'])
@login_required
def create_adventure():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}

        required_fields = ['title', 'description', 'location', 'price']
        is_valid, error_message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({'message': error_message}), 400

        adventure = Adventure(
            title=data['title'],
            description=data['description'],
            location=data['location'],
            price=float(data['price']),
            duration=data.get('duration'),
            difficulty=data.get('difficulty'),
            image_url=data.get('image_url'),
            max_capacity=data.get('max_capacity', 10),
            user_id=user_id
        )

        db.session.add(adventure)
        db.session.commit()

        return jsonify({
            'message': 'Adventure created successfully',
            'adventure': adventure.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create adventure', 'error': str(e)}), 500


# -----------------------------
# Update existing adventure
# -----------------------------
@adventures_bp.route('/<int:adventure_id>', methods=['PUT'])
@login_required
def update_adventure(adventure_id):
    try:
        user_id = session.get('user_id')
        adventure = Adventure.query.get_or_404(adventure_id)

        if adventure.user_id != user_id:
            return jsonify({'message': 'Unauthorized'}), 403

        data = request.get_json() or {}
        for field in ['title', 'description', 'location', 'price', 'duration', 'difficulty', 'image_url', 'max_capacity', 'is_active']:
            if field in data:
                value = float(data[field]) if field == 'price' else data[field]
                setattr(adventure, field, value)

        db.session.commit()

        return jsonify({
            'message': 'Adventure updated successfully',
            'adventure': adventure.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update adventure', 'error': str(e)}), 500


# -----------------------------
# Soft delete adventure
# -----------------------------
@adventures_bp.route('/<int:adventure_id>', methods=['DELETE'])
@login_required
def delete_adventure(adventure_id):
    try:
        user_id = session.get('user_id')
        adventure = Adventure.query.get_or_404(adventure_id)

        if adventure.user_id != user_id:
            return jsonify({'message': 'Unauthorized'}), 403

        adventure.is_active = False
        db.session.commit()

        return jsonify({'message': 'Adventure deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete adventure', 'error': str(e)}), 500


# -----------------------------
# Fetch logged-in user's adventures
# -----------------------------
@adventures_bp.route('/my-adventures', methods=['GET'])
@login_required
def get_my_adventures():
    try:
        user_id = session.get('user_id')
        adventures = Adventure.query.filter_by(user_id=user_id).all()
        return jsonify([adv.to_dict() for adv in adventures]), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch your adventures', 'error': str(e)}), 500
