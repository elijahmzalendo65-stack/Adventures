import requests
import base64
from datetime import datetime
from flask import current_app


def get_mpesa_access_token():
    """
    Generates an M-Pesa OAuth access token for STK push.
    """
    try:
        consumer_key = current_app.config.get('MPESA_CONSUMER_KEY')
        consumer_secret = current_app.config.get('MPESA_CONSUMER_SECRET')

        if not consumer_key or not consumer_secret:
            raise ValueError("M-Pesa Consumer Key/Secret not configured")

        url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        response = requests.get(url, auth=(consumer_key, consumer_secret), timeout=10)

        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            raise Exception(f"Failed to get M-Pesa access token: {response.text}")
    except Exception as e:
        print("Error getting M-Pesa access token:", str(e))
        raise



def generate_mpesa_password():
    """
    Generates password for STK Push request using shortcode, passkey, and timestamp.
    Returns tuple: (password, timestamp)
    """
    try:
        shortcode = current_app.config.get('MPESA_SHORTCODE')
        passkey = current_app.config.get('MPESA_PASSKEY')

        if not shortcode or not passkey:
            raise ValueError("M-Pesa Shortcode/Passkey not configured")

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data = shortcode + passkey + timestamp
        password = base64.b64encode(data.encode()).decode('utf-8')
        return password, timestamp
    except Exception as e:
        print("Error generating M-Pesa password:", str(e))
        raise



def initiate_stk_push(phone_number, amount, account_reference, transaction_desc):
    """
    Initiates a Safaricom M-Pesa STK push for payment.
    Returns JSON response from M-Pesa.
    """
    try:
        if not phone_number or not amount:
            raise ValueError("Phone number and amount are required for STK push")

        
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        elif phone_number.startswith("+"):
            phone_number = phone_number[1:]

        access_token = get_mpesa_access_token()
        if not access_token:
            raise Exception("Failed to obtain M-Pesa access token")

        password, timestamp = generate_mpesa_password()
        if not password or not timestamp:
            raise Exception("Failed to generate M-Pesa STK password")

        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'BusinessShortCode': current_app.config.get('MPESA_SHORTCODE'),
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone_number,
            'PartyB': current_app.config.get('MPESA_SHORTCODE'),
            'PhoneNumber': phone_number,
            'CallBackURL': current_app.config.get('MPESA_CALLBACK_URL'),
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc
        }

        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code == 200:
            result = response.json()
            if 'ResponseCode' in result and result['ResponseCode'] == '0':
                return result
            else:
                raise Exception(f"STK push failed: {result}")
        else:
            raise Exception(f"STK push request failed: {response.status_code} - {response.text}")

    except Exception as e:
        print("Error initiating STK push:", str(e))
        raise
