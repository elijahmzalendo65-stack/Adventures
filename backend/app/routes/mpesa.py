from flask import Blueprint, request, jsonify, session
from datetime import datetime
from ..extensions import db
from ..models.payment import Payment
from ..models.booking import Booking
from ..utils.mpesa_utils import initiate_stk_push
from ..utils.helpers import login_required, validate_required_fields

mpesa_bp = Blueprint('mpesa', __name__, url_prefix='/api/mpesa')



@mpesa_bp.route('/stk-push', methods=['POST'])
@login_required
def stk_push():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}

        required_fields = ['phone_number', 'amount', 'adventure_id']
        is_valid, error_message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({'message': error_message}), 400

        phone_number = data['phone_number']
        amount = float(data['amount'])
        adventure_id = int(data['adventure_id'])

        
        response = initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=f"ADVENTURE_{adventure_id}",
            transaction_desc="Adventure booking payment"
        )

        payment = Payment(
            user_id=user_id,
            adventure_id=adventure_id,
            phone_number=phone_number,
            amount=amount,
            checkout_request_id=response.get('CheckoutRequestID'),
            merchant_request_id=response.get('MerchantRequestID'),
            status='pending'
        )
        db.session.add(payment)
        db.session.commit()

        return jsonify({
            'message': 'STK push initiated successfully',
            'payment_id': payment.id,
            'response': response
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to initiate STK push', 'error': str(e)}), 500


@mpesa_bp.route('/callback', methods=['POST'])
def mpesa_callback():
    try:
        data = request.get_json() or {}
        stk_callback = data.get('Body', {}).get('stkCallback', {})

        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        checkout_request_id = stk_callback.get('CheckoutRequestID')

        payment = Payment.query.filter_by(checkout_request_id=checkout_request_id).first()
        if not payment:
            return jsonify({'ResultCode': 1, 'ResultDesc': 'Payment not found'}), 404

        if result_code == 0:
           
            items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            for item in items:
                name = item.get('Name')
                value = item.get('Value')
                if name == 'MpesaReceiptNumber':
                    payment.mpesa_receipt_number = value
                elif name == 'Amount':
                    payment.amount = value
                elif name == 'TransactionDate':
                    payment.transaction_date = datetime.strptime(str(value), '%Y%m%d%H%M%S')

            payment.status = 'completed'
        else:
            
            payment.status = 'failed'

        payment.result_code = result_code
        payment.result_desc = result_desc

        
        booking = Booking.query.filter_by(payment_id=payment.id).first()
        if booking:
            if payment.status == 'completed':
                booking.status = 'confirmed'
            else:
                booking.status = 'pending'

        db.session.commit()
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'ResultCode': 1, 'ResultDesc': str(e)}), 500



@mpesa_bp.route('/payments', methods=['GET'])
@login_required
def get_payments():
    try:
        user_id = session.get('user_id')
        payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all()
        return jsonify([p.to_dict() for p in payments]), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch payments', 'error': str(e)}), 500



@mpesa_bp.route('/payment/<int:payment_id>', methods=['GET'])
@login_required
def get_payment(payment_id):
    try:
        user_id = session.get('user_id')
        payment = Payment.query.filter_by(id=payment_id, user_id=user_id).first()
        if not payment:
            return jsonify({'message': 'Payment not found'}), 404
        return jsonify(payment.to_dict()), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch payment', 'error': str(e)}), 500
