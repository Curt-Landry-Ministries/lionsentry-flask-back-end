
import os
import json
import requests
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from firebase_admin import auth, firestore
from backend import public_server_template as pst
from backend.firebase.firebase_admin_sdk import db

auth_app = Flask(__name__)
CORS(auth_app)

base_dir = pst.get_base_directory()
load_dotenv()

BASE_URL = "https://api.infusionsoft.com/crm/rest/v1"
ACCESS_TOKEN = os.environ.get('KEAP_API_KEY') 

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
    # db.collection('onboardingFlows').document(user_id).set({
    #     "version": 1,
    #     "userID": user_id,
    #     "steps": steps_data
    # })


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
# Get a Firebase ID token and refresh token for a user
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
            return jsonify({
                "idToken": response_data.get("idToken"),
                "refreshToken": response_data.get("refreshToken"),
                "expiresIn": response_data.get("expiresIn")  # Optional: Token validity in seconds
            }), 200
        else:
            return jsonify({"error": "Authentication failed"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_app.route('/refresh-id-token', methods=['POST'])
def refresh_id_token():
    try:
        # Parse the incoming request
        data = request.get_json()
        refresh_token = data.get('refreshToken')

        if not refresh_token:
            return jsonify({"error": "Refresh token is required"}), 400

        # Get Firebase API key from environment
        firebase_api_key = os.environ.get('FIREBASE_API_KEY')
        url = f"https://securetoken.googleapis.com/v1/token?key={firebase_api_key}"

        # Prepare payload
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }

        # Make the request to refresh the token
        response = requests.post(url, data=payload)

        if response.status_code == 200:
            response_data = response.json()
            return jsonify({
                "idToken": response_data.get("id_token"),
                "refreshToken": response_data.get("refresh_token"),
                "expiresIn": response_data.get("expires_in")
            }), 200
        else:
            return jsonify({"error": "Failed to refresh token"}), response.status_code
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

        collections = ['users', 'onboardingAnswers', 'whyStatements', 'dailyDevotionals']
        
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


def search_create_update_keap_contact(email, family_name, given_name, tag_name="LS User"):
    """
    Searches for a user by email in the Keap API and creates the contact if not found.
    If the contact exists, it adds the specified tag if not already applied.

    Args:
        email (str): Email to search or create the contact.
        family_name (str): Last name of the contact.
        given_name (str): First name of the contact.
        tag_name (str): Tag to add to the contact. Defaults to "LS User".

    Returns:
        dict: Contact data or error response.
    """
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

    # Step 1: Search for contact by email
    search_url = f"{BASE_URL}/contacts?email={email}"
    search_response = requests.get(search_url, headers=headers)
    if search_response.status_code != 200:
        return {"error": "Failed to search for contact", "details": search_response.text}

    contacts = search_response.json().get("contacts", [])
    contact_id = contacts[0]["id"] if contacts else None

    # Step 2: If contact exists, check and add the tag
    if contact_id:
        tag_id = get_tag_id(tag_name)
        if tag_id:
            add_tag_to_contact(contact_id, tag_id)
        return {"message": "Contact exists and updated", "contact_id": contact_id}

    # Step 3: Create new contact
    create_url = f"{BASE_URL}/contacts"
    payload = {
        "email_addresses": [{"email": email, "field": "EMAIL1"}],
        "family_name": family_name,
        "given_name": given_name,
    }
    create_response = requests.put(create_url, headers=headers, json=payload)
    if create_response.status_code not in [200, 201]:
        return {"error": "Failed to create contact", "details": create_response.text}

    new_contact_id = create_response.json().get("id")
    tag_id = get_tag_id(tag_name)
    if tag_id:
        add_tag_to_contact(new_contact_id, tag_id)

    return {"message": "Contact created and tagged", "contact_id": new_contact_id}


def get_tag_id(tag_name):
    """Retrieve tag ID by tag name."""
    tags_url = f"{BASE_URL}/tags"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    response = requests.get(tags_url, headers=headers)

    if response.status_code == 200:
        for tag in response.json().get("tags", []):
            if tag["name"] == tag_name:
                return tag["id"]
    print(f"Error retrieving tag ID for '{tag_name}':", response.text)
    return None


def add_tag_to_contact(contact_id, tag_id):
    """Add a tag to a Keap contact."""
    tags_url = f"{BASE_URL}/contacts/{contact_id}/tags"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"tagIds": [tag_id]}

    response = requests.post(tags_url, headers=headers, json=payload)
    if response.status_code not in [200, 201]:
        print("Error adding tag:", response.text)


@auth_app.route('/create-keap-user', methods=['POST'])
def create_keap_user():
    """Flask route to create or update a Keap user."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input provided"}), 400

    email = data.get("email")
    first_name = data.get("firstName")
    last_name = data.get("lastName")

    if not email or not first_name or not last_name:
        return jsonify({"error": "Missing required fields: email, firstName, or lastName"}), 400

    response = search_create_update_keap_contact(email, last_name, first_name)
    return jsonify(response)


if __name__ == '__main__':
    auth_app.run(host='0.0.0.0', port=5002, debug=True)
