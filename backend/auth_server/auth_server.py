
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

# ENVIRONMENT VARIABLES
TAG_ID = str(os.environ.get('LS_TAG_ID'))  # Tag ID as a string
ACCESS_TOKEN = os.environ.get('KEAP_API_KEY')  # Keap API key
BASE_URL = "https://api.infusionsoft.com/crm/rest/v1"

# HEADERS for requests
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

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
    with open(os.path.join(base_dir, "auth_server/onboarding_steps.json"), "r") as file:
        steps = json.load(file)

    # Initialize steps data
    steps_data = [{"stepName": step, "dateCompleted": None, "dateCreated": datetime.utcnow()} for step in steps]

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

@auth_app.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        # Get the email from the request payload
        data = request.get_json()
        email = data.get('email')
        FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY')

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        # Firebase Authentication endpoint for sending reset password emails
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }

        # Make a POST request to Firebase API
        response = requests.post(url, json=payload)
        response_data = response.json()

        if response.status_code == 200:
            return jsonify({'message': 'Password reset email sent successfully.'}), 200
        else:
            error_message = response_data.get('error', {}).get('message', 'Failed to send email')
            return jsonify({'error': error_message}), response.status_code

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def search_and_create_or_update_contact(email: str, family_name: str, given_name: str, time_zone: str, middle_name: str = None):
    # 1) search
    search_url = f"{BASE_URL}/contacts?email={email}"
    search_response = requests.get(search_url, headers=HEADERS)

    if search_response.status_code == 200:
        contacts = search_response.json().get("contacts", [])
        if contacts:
            contact_id = contacts[0].get("id")
            print(f"Contact found: ID={contact_id}, Email={email}")

            # ensure time zone is set for existing contacts
            ok, err = update_contact_timezone(contact_id, time_zone)
            if not ok:
                print(f"Failed to update time_zone for contact {contact_id}: {err}")

            # tag logic (unchanged except payload fix below)
            if tag_already_applied(contact_id, TAG_ID):
                return {"message": "Tag already exists for contact", "contact_id": contact_id}
            add_tag_result = add_tag_to_contact(contact_id, TAG_ID)
            return ({"error": "Failed to apply tag", "contact_id": contact_id}
                    if add_tag_result.get("error")
                    else {"message": "Tag applied to existing contact", "contact_id": contact_id})

    elif search_response.status_code != 404:
        return {"error": "Error searching contact", "details": search_response.text}

    # 2) create
    print("Contact not found. Creating a new contact...")
    create_url = f"{BASE_URL}/contacts"
    payload = {
        "email_addresses": [{"email": email, "field": "EMAIL1"}],
        "family_name": family_name,
        "given_name": given_name,
        "middle_name": middle_name,
        "time_zone": time_zone,
        "opt_in_reason": "LionSentry Acknowledgement"
    }
    create_response = requests.post(create_url, headers=HEADERS, json=payload)

    if create_response.status_code in (200, 201):
        contact_id = create_response.json().get("id")
        add_tag_result = add_tag_to_contact(contact_id, TAG_ID)
        return ({"error": "Failed to apply tag to new contact", "contact_id": contact_id}
                if add_tag_result.get("error")
                else {"message": "New contact created and tagged", "contact_id": contact_id})

    return {"error": "Error creating contact", "details": create_response.text}


def add_tag_to_contact(contact_id: int, tag_id: str):
    url = f"{BASE_URL}/contacts/{contact_id}/tags"
    payload = {"tagIds": [tag_id]}  # <-- use the arg
    resp = requests.post(url, headers=HEADERS, json=payload)
    if resp.status_code in (200, 201):
        return {"success": True, "contact_id": contact_id, "tag_id": tag_id}
    return {"error": f"Error adding tag: {resp.status_code} - {resp.text}"}

def tag_already_applied(contact_id: int, tag_id: str):
    """
    Checks if a specific tag is already applied to a contact.
    """
    tags_url = f"{BASE_URL}/contacts/{contact_id}/tags"
    response = requests.get(tags_url, headers=HEADERS)

    if response.status_code == 200:
        existing_tags = response.json().get("tags", [])
        print(f"Raw existing tags response: {existing_tags}")  # Debugging line

        # Extract tag IDs from the nested structure
        tag_ids = [str(tag.get("tag", {}).get("id")) for tag in existing_tags if "tag" in tag and "id" in tag["tag"]]
        print(f"Existing tag IDs for contact {contact_id}: {tag_ids}")

        # Check if the tag_id exists
        return tag_id in tag_ids
    else:
        print(f"Error fetching tags for contact {contact_id}: {response.text}")
    return False

def add_tag_to_contact(contact_id: int, tag_id: str):
    """
    Adds a tag to a contact.
    """
    tags_url = f"{BASE_URL}/contacts/{contact_id}/tags"

    payload = {"tagIds": [TAG_ID]}
    print(f"Sending payload to add tag: {payload}")  # Debugging line

    response = requests.post(tags_url, headers=HEADERS, json=payload)

    if response.status_code in [200, 201]:
        print(f"Tag successfully applied: {response.json()}")
        return {"success": True, "contact_id": contact_id, "tag_id": TAG_ID}
    else:
        print(f"Failed to apply tag: {response.status_code} - {response.text}")
        return {"error": f"Error adding tag: {response.text}"}

@auth_app.route('/create-keap-user', methods=['POST'])
def create_keap_user():
    """Flask route to create or update a Keap user."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input provided"}), 400

    email = data.get("email")
    first_name = data.get("firstName")
    last_name = data.get("lastName")
    time_zone = data.get("timeZone")

    if not email or not first_name or not last_name:
        return jsonify({"error": "Missing required fields: email, firstName, or lastName"}), 400

    response = search_and_create_or_update_contact(email, last_name, first_name, time_zone)
    if "error" in response:
        return jsonify({"status": "failure", "details": response}), 500
    else:
        return jsonify({"status": "success", "details": response}), 200

if __name__ == '__main__':
    auth_app.run(host='0.0.0.0', port=5002, debug=True)
