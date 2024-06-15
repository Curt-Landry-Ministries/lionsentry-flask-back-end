from backend.email_server.llm.generate_devotional import generate_devotional_content
import html
import json
import os
from flask import Flask, request, jsonify, abort
from firebase_admin import credentials, firestore, auth
import firebase_admin
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime
import pytz
from functools import wraps
import logging
from dotenv import load_dotenv
from flask.logging import default_handler
import sys

# Add the backend path to sys.path for absolute imports
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_path)


app = Flask(__name__)
app.logger.removeHandler(default_handler)
# Set log level to DEBUG
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
firebase_creds = credentials.Certificate(os.path.join(
    current_dir, '../firebase/lionsentry-firebase-adminsdk.json'))
if not firebase_admin._apps:
    firebase_admin.initialize_app(firebase_creds)
db = firestore.client()


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


def get_why_statement(user_id):
    # Get their Why Statement and include it here too
    why_statement_docs = db.collection(
        'whyStatements').where('forUser', '==', user_id).get()

    if len(why_statement_docs) == 0:
        return jsonify({"error": "Why Statement not found for the user"}), 404

    why_statement = why_statement_docs[0].to_dict().get('whyStatement', '')
    # Add the why statement to user data
    return why_statement

def get_onboarding_answers(user_id):
    answers_query = db.collection('onboardingAnswers').where('userID', '==', user_id)
    answers_docs = answers_query.stream()

    # Collect the most recent answer for each question
    recent_answers = {}
    for answer_doc in answers_docs:
        answer_data = answer_doc.to_dict()
        question = answer_data['question']
        # Assuming the answers are sorted in the array with the most recent last
        most_recent_answer = answer_data['answers'][-1]
        recent_answers[question] = most_recent_answer

    # Get the answer texts and create a list of question-answer pairs
    questions_answers = [{"question": q, "answer": a['answer']} for q, a in recent_answers.items()]
    return questions_answers


def schedule_email_with_sendgrid(recipient, dynamic_data, send_at, template_id=None):
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    message = Mail(
        from_email='griffin@lionsentry.com',
        to_emails=recipient,
    )
    if template_id:
        message.dynamic_template_data = dynamic_data
        message.template_id = template_id
    else:
        message.subject = dynamic_data.get('subject')
        message.html_content = dynamic_data.get('content')
    message.send_at = send_at
    response = sg.send(message)
    return response


@app.route('/generate-daily-devotionals-for-all-users', methods=['POST'])
@require_api_key
def create_new_emails_for_all_users():
    for_testing = request.json.get('for_testing', False)
    if for_testing:
        users = db.collection('users').where(
            'email', '==', 'dev@lionsentry.com').stream()
    else:
        users = db.collection('users').stream()

    for user in users:
        user_id = user.id
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_data['whyStatement'] = get_why_statement(user_id)
            user_data['onboardingAnswers'] = get_onboarding_answers(user_id)
            user_email = user_data.get('email')
            if user_email and not (user_email.startswith('test') or user_email.startswith('Test')):
                app.logger.info(
                    f"Attempting to generate email for user {user_id}")
                try:
                    devotional_content = generate_devotional_content(user_data)

                    title = devotional_content.get('Title')
                    title = html.unescape(devotional_content.get('Title'))

                    dynamic_template_data = {
                        "subject": title,
                        "bible_passage": devotional_content.get("BiblePassage"),
                        "personalization": devotional_content.get("Personalization"),
                        "journaling_prompt": devotional_content.get("JournalingPrompt")
                    }

                    db.collection('emailQueue').add({
                        'recipient': user_id,
                        'subject': title,
                        'content': dynamic_template_data,
                        'sendAt': datetime.now().isoformat(),
                        'status': 'written',
                        'template_id': 'd-82f430f90f964795925f4431b8b8daca'
                    })[1]
                    app.logger.info(
                        f"Email successfully generated for user {user_id}")
                except Exception as e:
                    app.logger.error(
                        f"Failed to generate email for user {user_id}: {e}")
                    return jsonify({"error": f"Failed to generate email for user {user_id}: {str(e)}"}), 500
            else:
                if user_email:
                    app.logger.info(
                        f"Skipping test user {user_id} with email {user_email}")
                else:
                    app.logger.error(
                        f"User {user_id} does not have an email address")
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
    emails = db.collection('emailQueue').where(
        'status', '==', 'written').stream()
    for email in emails:
        email_data = email.to_dict()
        user_id = email_data['recipient']
        app.logger.debug(f"Scheduling email for user {user_id}")

        # Fetch the user's email address
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            # Schedule the email with SendGrid
            user_email = user_doc.to_dict().get('email')
            send_at_utc = convert_to_utc(
                email_data['sendAt'], 'America/Los_Angeles')
            response = schedule_email_with_sendgrid(
                user_email, email_data['content'], send_at_utc, template_id=email_data.get(
                    'template_id')
            )
            app.logger.debug(
                f"SendGrid response: {response.status_code} {response.body}")
            email.reference.update(
                {'status': 'sentToSendGrid', 'sendGridID': response.headers['X-Message-Id']})
        else:
            app.logger.error(f'User {user_id} does not exist in the database')
    print('Finished scheduling emails')
    return jsonify({"message": "Emails scheduled successfully"}), 200


@ app.route('/create-email-doc', methods=['POST'])
@ require_api_key
# Create a new email document in the email queue.
def create_email_doc():
    data = request.get_json()
    app.logger.debug(f"Received request to create email doc with data: {data}")

    recipient = data.get('recipient')
    subject = data.get('subject')
    content = data.get('content')
    send_at = data.get('sendAt')
    template_id = data.get('template_id')  # Optional template ID

    if not recipient or not subject or not content or not send_at:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        email_doc_ref = db.collection('emailQueue').add({
            'recipient': recipient,
            'subject': subject,
            'content': content,
            'sendAt': send_at,
            'status': 'written',
            'template_id': template_id  # Include the template ID in the document

        })[1]

        return jsonify({"message": "Email added to queue successfully", "id": email_doc_ref.id}), 200
    except Exception as e:
        app.logger.error(f"Error adding email to queue: {e}")
        return jsonify({"error": "Failed to add email to queue"}), 500


@ app.route('/sendgrid-webhook', methods=['POST'])
# Handle webhook events from SendGrid.
def sendgrid_webhook():
    data = request.get_json()
    app.logger.debug(f"Received SendGrid webhook data: {data}")

    for event in data:
        sendGridID = event.get('email_id')
        status = event.get('event')
        if status == 'delivered':
            db.collection('emailQueue').document(
                sendGridID).update({'status': 'sentSuccessfully'})
        elif status == 'deferred':
            db.collection('emailQueue').document(
                sendGridID).update({'status': 'queuedSuccessfully'})
        elif status == 'bounce' or status == 'dropped':
            db.collection('emailQueue').document(
                sendGridID).update({'status': status})
    return jsonify({"message": "Webhook received"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
