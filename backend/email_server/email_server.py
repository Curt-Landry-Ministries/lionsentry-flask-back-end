import os
from flask import Flask, request, jsonify, abort
from firebase_admin import credentials, firestore
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime
import pytz
from functools import wraps
import logging
from dotenv import load_dotenv
from flask.logging import default_handler
import sys
from backend.firebase.firebase_admin_sdk import db

app = Flask(__name__)
app.logger.removeHandler(default_handler)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
load_dotenv()
 
current_dir = os.path.dirname(os.path.abspath(__file__))

def convert_to_utc(time_str, timezone_str):
    local = pytz.timezone(timezone_str)
    naive = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    utc_dt = naive.astimezone(pytz.utc)
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
    message = Mail(
        from_email='griffin@lionsentry.com',
        to_emails=recipient,
        subject=subject,
        html_content=content
    )
    message.send_at = send_at
    response = sg.send(message)
    return response

@app.route('/schedule-emails', methods=['POST'])
@require_api_key
def schedule_emails():
    print('Starting to schedule emails')
    emails = db.collection('emailQueue').where('status', '==', 'written').stream()
    for email in emails:
        email_data = email.to_dict()
        user_id = email_data['recipient']
        
        # Fetch the user's email address
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            user_email = user_doc.to_dict().get('email')
            print(f'Scheduling email for user: {user_id}')
            send_at_utc = convert_to_utc(email_data['sendAt'], 'America/Los_Angeles')
            response = schedule_email_with_sendgrid(user_email, email_data['subject'], email_data['content'], send_at_utc)
            email.reference.update({'status': 'sentToSendGrid', 'sendGridID': response.headers['X-Message-Id']})
        else:
            app.logger.error(f'User not found for ID: {user_id}')
    print('Finished scheduling emails')
    return jsonify({"message": "Emails scheduled successfully"}), 200

@app.route('/sendgrid-webhook', methods=['POST'])
def sendgrid_webhook():
    data = request.get_json()
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
