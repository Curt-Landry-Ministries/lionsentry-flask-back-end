from dotenv import load_dotenv
from flask import Flask, request, jsonify
from firebase_admin import auth, firestore
import os
import json
from flask_cors import CORS
from datetime import datetime

import requests

from backend import public_server_template as pst

from backend.firebase.firebase_admin_sdk import db

auth_app = Flask(__name__)
CORS(auth_app)

base_dir = pst.get_base_directory()
load_dotenv()

def on_create_user(user_id, email):
    """
    Users have two kinds of records - 1:1 records and 1:many records. We should intialize all of the 1:1 records here (e.g. user info, onboarding flow, etc.)
    """

    user_ref = db.collection('users').document(user_id)
    user_ref.set({
        'userID': user_id,
        'email': email,
        'firstName': '',
        'lastName': '',
        'birthday': None,
        'sex': '',
        'referredBy': '',
        'accountCreated': datetime.utcnow(),
        'login': [],
        'preferredBibleVersion': '',
        'isDeleted': False,
        'timeZone': '',
    })

    # initialize an onboarding flow for this user
    initialize_onboarding_flow(user_id)

def initialize_onboarding_flow(user_id):
    # Load onboarding steps from JSON file
    # TODO implement this in the FE. My thinking here is that we want to save the user's place in the onbaording flow, as it's pretty lengthy and restarting would suck
    with open(os.path.join(base_dir, "auth_server/onboarding_steps.json"), "r") as file:
        steps = json.load(file)

    # Initialize steps data
    steps_data = [{"stepName": step, "dateCompleted": None, "dateCreated": datetime.utcnow()} for step in steps]

    # Create onboarding flow document
    db.collection('onboardingFlows').document(user_id).set({
        "version": 1,
        "userID": user_id,
        "steps": steps_data
    })


@auth_app.route('/login-user', methods=['POST'])
def login_user():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Authenticate user with Firebase
        firebase_api_key = os.environ.get('FIREBASE_API_KEY')
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            response_data = response.json()
            user_id = response_data.get("localId")
            id_token = response_data.get("idToken")

            # Fetch user info from Firestore
            user_info = db.collection('users').document(user_id).get().to_dict()

            return jsonify({"idToken": id_token, "user": user_info}), 200
        else:
            return jsonify({"error": "Authentication failed"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_app.route('/create-user-manually', methods=['POST'])
# Create a user with username/password (as opposed to w/ Google, FB, etc.)
def create_user_manually():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        user_record = auth.create_user(email=email, password=password)

        # Create Firestore record for user
        on_create_user(user_record.uid, email)

        # Initialize onboarding flow for user
        initialize_onboarding_flow(user_record.uid)

        return jsonify({"message": "User created successfully", "uid": user_record.uid}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@auth_app.route('/get-id-token', methods=['POST'])
# Get a Firebase ID token for a user
def get_id_token():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Authenticate user with Firebase
        firebase_api_key = os.environ.get('FIREBASE_API_KEY')
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            response_data = response.json()
            return jsonify({"idToken": response_data.get("idToken")}), 200
        else:
            return jsonify({"error": "Authentication failed"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_app.route('/delete-user', methods=['POST'])
# Delete a user and all of the other data associated with them
def delete_user():
    try:
        data = request.get_json()
        user_id = data.get('userID')
        id_token = data.get('idToken')

        # Verify the ID token first
        decoded_token = auth.verify_id_token(id_token)
        if not decoded_token or decoded_token['uid'] != user_id:
            return jsonify({"error": "Unauthorized request"}), 403

        collections = ['users', 'onboardingFlows', 'onboardingAnswers', 'whyStatements', 'dailyDevotionals']
        
        # For each collection, if a document exists for the user, delete it
        for collection in collections:
            doc_ref = db.collection(collection).document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                doc_ref.delete()

        # Delete Firebase Authentication User
        auth.delete_user(user_id)

        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        # Detailed error logging
        return jsonify({"error": str(e), "detailed_error": repr(e)}), 500



if __name__ == '__main__':
    auth_app.run(host='0.0.0.0', port=5002, debug=True)
