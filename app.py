from flask import Flask, render_template, request, session, redirect, url_for,flash,jsonify
import requests
import base64
from datetime import datetime
import json
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

import os









# SQLite (for local testing)


consumer_key = os.getenv('CONSUMER_KEY')
consumer_secret = os.getenv('CONSUMER_SECRET')
passkey = os.getenv('PASSKEY')
shortCode = os.getenv('SHORT_CODE')


# PostgreSQL
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://user:password@localhost/wifi_billing"



db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///transactions.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()

    return app

app = create_app()





load_dotenv()




app.secret_key = 'a_very_secret_key_123'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process-payment', methods=['POST'])
def process_payment():
    data = request.get_json()
    package_name = data['packageName']
    package_amount = data['packageAmount']
    phone_number = data['phoneNumber']
    phone_number = phone_number.strip()

  

    

    if phone_number.startswith('07'):
        phone_number = '254' + phone_number[1:]
    
    response = sendStkPush(phone_number,package_amount)

    # ! Logging received data
    print(f"Payment: for {phone_number}")
   
    return jsonify({"status":"success", "message":"Payment processed successfully"})


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    mpesa_code = db.Column(db.String(255), unique=True, nullable=False)
    status = db.Column(db.String(255), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Transaction('{self.phone}', '{self.amount}', '{self.mpesa_code}', '{self.status}')"



    


def generate_access_token():
    consumer_key = os.getenv('CONSUMER_KEY')
    
    consumer_secret = os.getenv('CONSUMER_SECRET')

    if not consumer_key or not consumer_secret:
        raise ValueError("Missing CONSUMER_KEY or CONSUMER_SECRET in environment variables")


    #sandbox
    # url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    #live
    url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        
        encoded_credentials = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()

        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }

        # Send the request and parse the response
        response = requests.get(url, headers=headers).json()

        
        

        # Check for errors and return the access token
        if "access_token" in response:
            return response["access_token"]
        
        else:
            raise Exception("Failed to get access token: " + response["error_description"])
    except Exception as e:
        raise Exception("Failed to get access token: " + str(e)) 
    

def sendStkPush(phone_number,package_amount):
    token = generate_access_token()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    shortCode = os.getenv('SHORT_CODE')  #sandbox -174379
    passkey = os.getenv('PASSKEY')
    stk_password = base64.b64encode((shortCode + passkey + timestamp).encode('utf-8')).decode('utf-8')

    
    
    #choose one depending on you development environment
    #sandbox
    # url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    #live
    url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }
    
    requestBody = {
        "BusinessShortCode": shortCode,
        "Password": stk_password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline", #till "CustomerBuyGoodsOnline"
        "Amount": package_amount,
        "PartyA": phone_number,
        "PartyB": os.getenv('SHORT_CODE'),
        "PhoneNumber": phone_number,
        "CallBackURL": "https://samawa.co.ke/callback",
        "AccountReference": f"InternetAccess-{package_amount}",
        "TransactionDesc": f"WiFi Access Payment - Ksh {package_amount}"
    }
    
    try:
        response = requests.post(url, json=requestBody, headers=headers)
        print(response.json())
        return response.json()
    except Exception as e:
        print('Error:', str(e))



@app.route('/callback', methods=['POST'])
def handle_callback():
    # try:
        callback_data = request.json
        print(callback_data)
        result_code = callback_data['Body']['stkCallback']['ResultCode']

        
        

        if result_code == 0:
            callback_metadata = callback_data['Body']['stkCallback']['CallbackMetadata']
            amount = None
            phone_number = None
            for item in callback_metadata['Item']:
                if item['Name'] == 'Amount':
                    amount = item['Value']
                    print(f"Paid Amaount is : {amount}")
                elif item['Name'] == 'PhoneNumber':
                    phone_number = item['Value']
                    print(f"Phone number is : {phone_number}")
                elif item['Name'] == 'MpesaReceiptNumber':
                    mpesa_code = item['Value']
                    print(f"Mpesa code is : {mpesa_code}")

            #Saving the data in the database
            status = "success" if result_code == 0 else "failed"
            print(f"status is : {status}")

            # transaction = Transaction(phone=phone_number, amount=amount, mpesa_code=mpesa_code, status=status)

            # db.session.add(transaction)
            # db.session.commit()

            return jsonify({"status":"success", "message":"Transaction has been recorded"})
    # except Exception as e:
    #     db.session.rollback()
    #     return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/confirm_payment')
def confirm_payment():
    return render_template('confirm_payment.html')






 # Get the port from the environment variable or default to 5000
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=True, host='0.0.0.0', port=port)