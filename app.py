from flask import Flask, render_template, request, session, redirect, url_for,flash,jsonify
import requests
import base64
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()





app = Flask(__name__)

app.secret_key = 'a_very_secret_key_123'

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        phone_number = request.form.get('phone')
        print(phone_number)
        print("Button was clicked")
        response = sendStkPush(phone_number)

        flash(json.dumps(response))
        
        return redirect(url_for('confirm_payment'))
        
    return render_template('index.html')

@app.route('/confirm_payment')
def confirm_payment():
    return render_template('confirm_payment.html')

@app.route('/callbackurl', methods=['POST'])
def handle_callback():
    print("Callback hit!!")
    callback_data = request.get_json()
    print(f"This is the callback data {callback_data}")

    response_data = {'Status':'Success'}
    return jsonify(response_data)




def generate_access_token():
    consumer_key = os.getenv("CONSUMER_KEY")
    consumer_secret = os.getenv("CONSUMER_SECRET")

    #choose one depending on you development environment
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
        print(f"Your access token is {response['access_token']}")

        # Check for errors and return the access token
        if "access_token" in response:
            return response["access_token"]
        else:
            raise Exception("Failed to get access token: " + response["error_description"])
    except Exception as e:
        raise Exception("Failed to get access token: " + str(e)) 
    



 
def sendStkPush(phone_number):
    token = generate_access_token()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    shortCode = os.getenv("SHORT_CODE")  #sandbox -174379
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
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
        "Amount": "1",
        "PartyA": phone_number,
        "PartyB": shortCode,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://lipia.onrender.com/callbackurl",
        "AccountReference": "Payment",
        "TransactionDesc": "Pay internet"
    }
    
    try:
        response = requests.post(url, json=requestBody, headers=headers)
        print(response.json())
        return response.json()
    except Exception as e:
        print('Error:', str(e))


import os


 # Get the port from the environment variable or default to 5000
port = int(os.environ.get("PORT", 10000))
app.run(debug=True, host='0.0.0.0', port=port)