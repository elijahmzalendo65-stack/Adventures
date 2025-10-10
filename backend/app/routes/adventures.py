from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models.adventure import Adventure
from app.utils.helpers import login_required, validate_required_fields

adventures_bp = Blueprint('adventures', __name__)

@adventures_bp.route('/', methods=['GET'])
def get_adventures():
    try:
        adventures = Adventure.query.filter_by(is_active=True).all()
        return jsonify([adventure.to_dict() for adventure in adventures]), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch adventures', 'error': str(e)}), 500

@adventures_bp.route('/<int:adventure_id>', methods=['GET'])
def get_adventure(adventure_id):
    try:
        adventure = Adventure.query.get_or_404(adventure_id)
        return jsonify(adventure.to_dict()), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch adventure', 'error': str(e)}), 500

@adventures_bp.route('/', methods=['POST'])
@login_required
def create_adventure():
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        required_fields = ['title', 'description', 'location', 'price']
        is_valid, error_message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({'message': error_message}), 400
        
        adventure = Adventure(
            title=data.get('title'),
            description=data.get('description'),
            location=data.get('location'),
            price=float(data.get('price')),
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

@adventures_bp.route('/<int:adventure_id>', methods=['PUT'])
@login_required
def update_adventure(adventure_id):
    try:
        user_id = session.get('user_id')
        adventure = Adventure.query.get_or_404(adventure_id)
        
        if adventure.user_id != user_id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        
        # Update allowed fields
        updatable_fields = ['title', 'description', 'location', 'price', 'duration', 
                           'difficulty', 'image_url', 'max_capacity', 'is_active']
        
        for field in updatable_fields:
            if field in data:
                if field == 'price':
                    setattr(adventure, field, float(data[field]))
                else:
                    setattr(adventure, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Adventure updated successfully', 
            'adventure': adventure.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update adventure', 'error': str(e)}), 500

@adventures_bp.route('/<int:adventure_id>', methods=['DELETE'])
@login_required
def delete_adventure(adventure_id):
    try:
        user_id = session.get('user_id')
        adventure = Adventure.query.get_or_404(adventure_id)
        
        if adventure.user_id != user_id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        # Soft delete by setting is_active to False
        adventure.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Adventure deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete adventure', 'error': str(e)}), 500

@adventures_bp.route('/my-adventures', methods=['GET'])
@login_required
def get_my_adventures():
    try:
        user_id = session.get('user_id')
        adventures = Adventure.query.filter_by(user_id=user_id).all()
        return jsonify([adventure.to_dict() for adventure in adventures]), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch your adventures', 'error': str(e)}), 500