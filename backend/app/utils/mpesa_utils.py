import requests
import base64
from datetime import datetime
from flask import current_app

def get_mpesa_access_token():
    consumer_key = current_app.config['MPESA_CONSUMER_KEY']
    consumer_secret = current_app.config['MPESA_CONSUMER_SECRET']
    
    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    response = requests.get(url, auth=(consumer_key, consumer_secret))
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception('Failed to get M-Pesa access token')

def generate_mpesa_password():
    shortcode = current_app.config['MPESA_SHORTCODE']
    passkey = current_app.config['MPESA_PASSKEY']
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    data = shortcode + passkey + timestamp
    password = base64.b64encode(data.encode()).decode('utf-8')
    
    return password, timestamp

def initiate_stk_push(phone_number, amount, account_reference, transaction_desc):
    access_token = get_mpesa_access_token()
    password, timestamp = generate_mpesa_password()
    
    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'BusinessShortCode': current_app.config['MPESA_SHORTCODE'],
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone_number,
        'PartyB': current_app.config['MPESA_SHORTCODE'],
        'PhoneNumber': phone_number,
        'CallBackURL': current_app.config['MPESA_CALLBACK_URL'],
        'AccountReference': account_reference,
        'TransactionDesc': transaction_desc
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Failed to initiate STK push: {response.text}')