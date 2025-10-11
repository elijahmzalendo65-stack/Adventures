from flask import Blueprint, request, jsonify
from datetime import datetime
from ..extensions import db
from ..models.payment import Payment
from ..models.booking import Booking
from ..utils.mpesa_utils import initiate_stk_push
from ..utils.helpers import login_required, validate_required_fields

mpesa_bp = Blueprint('mpesa', __name__)

@mpesa_bp.route('/stk-push', methods=['POST'])
@login_required
def stk_push():
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        required_fields = ['phone_number', 'amount', 'adventure_id']
        is_valid, error_message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({'message': error_message}), 400
        
        phone_number = data.get('phone_number')
        amount = data.get('amount')
        adventure_id = data.get('adventure_id')
        
        # Initiate STK push
        response = initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=f"ADVENTURE_{adventure_id}",
            transaction_desc="Adventure booking payment"
        )
        
        # Save payment record
        payment = Payment(
            phone_number=phone_number,
            amount=amount,
            checkout_request_id=response.get('CheckoutRequestID'),
            merchant_request_id=response.get('MerchantRequestID'),
            user_id=user_id,
            adventure_id=adventure_id
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'message': 'STK push initiated successfully',
            'response': response,
            'payment_id': payment.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@mpesa_bp.route('/callback', methods=['POST'])
def mpesa_callback():
    try:
        data = request.get_json()
        
        # Process M-Pesa callback
        result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
        result_desc = data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')
        checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
        
        # Find payment record
        payment = Payment.query.filter_by(checkout_request_id=checkout_request_id).first()
        
        if payment:
            if result_code == 0:
                # Successful payment
                callback_metadata = data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])
                
                for item in callback_metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        payment.mpesa_receipt_number = item.get('Value')
                    elif item.get('Name') == 'Amount':
                        payment.amount = item.get('Value')
                    elif item.get('Name') == 'TransactionDate':
                        transaction_date_str = str(item.get('Value'))
                        transaction_date = datetime.strptime(transaction_date_str, '%Y%m%d%H%M%S')
                        payment.transaction_date = transaction_date
                
                payment.status = 'completed'
                payment.result_code = result_code
                payment.result_desc = result_desc
                
                # Update associated booking status if exists
                booking = Booking.query.filter_by(payment_id=payment.id).first()
                if booking:
                    booking.status = 'confirmed'
                
            else:
                # Failed payment
                payment.status = 'failed'
                payment.result_code = result_code
                payment.result_desc = result_desc
            
            db.session.commit()
        
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'}), 200
        
    except Exception as e:
        return jsonify({'ResultCode': 1, 'ResultDesc': str(e)}), 500

@mpesa_bp.route('/payments', methods=['GET'])
@login_required
def get_payments():
    try:
        user_id = session.get('user_id')
        payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all()
        return jsonify([payment.to_dict() for payment in payments]), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch payments', 'error': str(e)}), 500

@mpesa_bp.route('/payment/<int:payment_id>', methods=['GET'])
@login_required
def get_payment(payment_id):
    try:
        user_id = session.get('user_id')
        payment = Payment.query.filter_by(id=payment_id, user_id=user_id).first_or_404()
        return jsonify(payment.to_dict()), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch payment', 'error': str(e)}), 500