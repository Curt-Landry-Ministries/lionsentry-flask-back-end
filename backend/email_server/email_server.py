import os
import sys
import json
import pytz
import logging
from functools import wraps
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
import requests
from sendgrid.helpers.mail import Mail
from flask.logging import default_handler
from flask import Flask, request, jsonify, abort
from firebase_admin import credentials, firestore
from backend.firebase.firebase_admin_sdk import db

app = Flask(__name__)
CORS(app)
app.logger.removeHandler(default_handler)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)  # Set log level to DEBUG
load_dotenv()

# Log environment variables
app.logger.debug(f"APP_SERVER_URL: {'http://localhost:5001' if os.getenv('DEV_MODE') else 'https://api.lionsentry.com/app_server/'}")
app.logger.debug(f"EMAIL_SERVER_API_KEY: {os.getenv('EMAIL_SERVER_API_KEY')}")
app.logger.debug(f"APP_SERVER_API_KEY: {os.getenv('APP_SERVER_API_KEY')}")
app.logger.debug(f"SENDGRID_API_KEY: {os.getenv('SENDGRID_API_KEY')}")

APP_SERVER_URL = 'http://localhost:5001' if os.getenv('DEV_MODE') else 'https://lionsentry.com'

current_dir = os.path.dirname(os.path.abspath(__file__))

def convert_to_utc(time_str, timezone_str):
    local = pytz.timezone(timezone_str)
    naive = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%f")
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp())


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('EMAIL-SERVER-API-KEY')
        if api_key != os.getenv('EMAIL_SERVER_API_KEY'):
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

def schedule_email_with_sendgrid(recipient, subject, content, send_at):
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    if isinstance(content, dict):
        content = json.dumps(content)  # Convert dict to JSON string if necessary
    message = Mail(
        from_email='griffin@lionsentry.com',
        to_emails=recipient,
        subject=subject,
        html_content=content
    )
    message.send_at = send_at
    response = sg.send(message)
    return response


@app.route('/generate-daily-devotionals-for-all-users', methods=['POST'])
@require_api_key
def create_new_emails_for_all_users():
    users = db.collection('users').stream()
    for user in users:
        user_id = user.id
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_email = user_data.get('email')
            # If the user has an email and isn't a test user (only want this to fire for the dev@lionsentry email in our test environment)
            if user_email and not(user_email.startswith('test') or user_email.startswith('Test')): 
                app.logger.info(f"Attempting to generate email for user {user_id}")
                try:
                    response = requests.post(
                        f'{APP_SERVER_URL}/generate-email',
                        headers={'API-KEY': os.getenv('APP_SERVER_API_KEY')},
                        json={'user_id': user_id}
                    )
                    app.logger.info(f"Sent API-KEY: {os.getenv('APP_SERVER_API_KEY')}")
                    app.logger.info(f"Request URL: {APP_SERVER_URL}/generate-email")
                    app.logger.info(f"Request Headers: {response.request.headers}")
                    app.logger.info(f"Request Body: {response.request.body}")
                    app.logger.info(f"Response Status: {response.status_code}, Response Text: {response.text}")
                    response.raise_for_status()  # Raise an exception for HTTP errors

                    content = response.json()  # Assuming the response content is in JSON format
                    email_doc_ref = db.collection('emailQueue').add({
                        'recipient': user_id,
                        'subject': 'Daily Devotional',
                        'content': content,
                        'sendAt': datetime.now().isoformat(),
                        'status': 'written'
                    })[1]
                    app.logger.info(f"Email successfully generated for user {user_id}")
                except requests.exceptions.RequestException as e:
                    app.logger.error(f"Failed to generate email for user {user_id}: {e}")
                    return jsonify({"error": f"Failed to communicate with the app server for user {user_id}: {str(e)}"}), 500
            else:
                if user_email:
                    app.logger.info(f"Skipping test user {user_id} with email {user_email}")
                else:
                    app.logger.error(f"User {user_id} does not have an email address")
        else:
            app.logger.error(f"User {user_id} does not exist in the database")
    return jsonify({"message": "Emails created successfully"}), 200

@app.route('/schedule-emails', methods=['POST'])
@require_api_key
# Schedule emails that are in the queue and marked as 'written'.
def schedule_emails():
    app.logger.debug("Received request to schedule emails")
    app.logger.debug(f"Request headers: {request.headers}")
    
    print('Starting to schedule emails')
    emails = db.collection('emailQueue').where('status', '==', 'written').stream()
    for email in emails:
        email_data = email.to_dict()
        user_id = email_data['recipient']
        app.logger.debug(f"Scheduling email for user {user_id}")
        
        # Fetch the user's email address
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            # Schedule the email with SendGrid
            user_email = user_doc.to_dict().get('email')
            send_at_utc = convert_to_utc(email_data['sendAt'], 'America/Los_Angeles')
            response = schedule_email_with_sendgrid(user_email, email_data['subject'], email_data['content'], send_at_utc)
            app.logger.debug(f"SendGrid response: {response.status_code} {response.body}")
            email.reference.update({'status': 'sentToSendGrid', 'sendGridID': response.headers['X-Message-Id']})
        else:
            app.logger.error(f'User {user_id} does not exist in the database')
    print('Finished scheduling emails')
    return jsonify({"message": "Emails scheduled successfully"}), 200


@app.route('/create-email-doc', methods=['POST'])
@require_api_key
# Create a new email document in the email queue.
def create_email_doc():
    data = request.get_json()
    app.logger.debug(f"Received request to create email doc with data: {data}")
    
    recipient = data.get('recipient')
    subject = data.get('subject')
    content = data.get('content')
    send_at = data.get('sendAt')

    if not recipient or not subject or not content or not send_at:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        email_doc_ref = db.collection('emailQueue').add({
            'recipient': recipient,
            'subject': subject,
            'content': content,
            'sendAt': send_at,
            'status': 'written'
        })[1]

        return jsonify({"message": "Email added to queue successfully", "id": email_doc_ref.id}), 200
    except Exception as e:
        app.logger.error(f"Error adding email to queue: {e}")
        return jsonify({"error": "Failed to add email to queue"}), 500

@app.route('/sendgrid-webhook', methods=['POST'])
# Handle webhook events from SendGrid.
def sendgrid_webhook():
    data = request.get_json()
    app.logger.debug(f"Received SendGrid webhook data: {data}")
    
    for event in data:
        sendGridID = event.get('email_id')
        status = event.get('event')
        if status == 'delivered':
            db.collection('emailQueue').document(sendGridID).update({'status': 'sentSuccessfully'})
        elif status == 'deferred':
            db.collection('emailQueue').document(sendGridID).update({'status': 'queuedSuccessfully'})
        elif status == 'bounce' or status == 'dropped':
            db.collection('emailQueue').document(sendGridID).update({'status': status})
    return jsonify({"message": "Webhook received"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
