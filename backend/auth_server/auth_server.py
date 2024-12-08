
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





    """
    Searches for a user by email in the Keap API and creates the contact if not found.
    If the contact already exists and is not tagged, adds the specified tag.

    Args:
        base_url (str): Keap API base URL.
        access_token (str): Keap API access token.
        email (str): Email to search and create or update.
        family_name (str): Family name of the contact.
        given_name (str): Given name of the contact.
        middle_name (str, optional): Middle name of the contact. Defaults to None.
        duplicate_option (str, optional): Duplicate resolution option. Defaults to "Email".
        tag_name (str, optional): Tag to add to the contact. Defaults to "lionsentry".

    Returns:
        dict: API response as a dictionary.
    """

def search_create_update_keap_contact(
    base_url: str,
    access_token: str,
    email: str,
    family_name: str,
    given_name: str,
    middle_name: str = None,
    duplicate_option: str = "Email",
    tag_name: str = "LS User"
):

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Search for the contact by email
    search_url = f"{base_url}/contacts?email={email}"
    search_response = requests.get(search_url, headers=headers)

    if search_response.status_code == 200:
        results = search_response.json().get("contacts", [])
        if results:
            # Contact exists, check if the tag is already applied
            contact = results[0]
            contact_id = contact.get("id")
            if contact_id:
                tag_id = get_tag_id(base_url, access_token, tag_name)
                if tag_id:
                    add_tag_response = add_tag_to_contact(base_url, access_token, contact_id, tag_id)
                    if add_tag_response.get("error"):
                        print("Error tagging contact:", add_tag_response["error"])
                    else:
                        print(f"Tag '{tag_name}' added successfully to contact {contact_id}.")
                        # Re-fetch contact to verify tag
                        contact = get_contact(base_url, access_token, contact_id)
                        return {"message": "Contact already exists and updated", "contact": contact}
            return {"message": "Contact already exists and updated", "contact": contact}
    else:
        print("Error searching for contact:", search_response.status_code, search_response.text)
        return {"error": "Failed to search for contact"}

    # Contact does not exist, create a new one
    create_url = f"{base_url}/contacts"
    payload = {
        "email_addresses": [{"email": email, "field": "EMAIL1"}],
        "family_name": family_name,
        "given_name": given_name,
        "middle_name": middle_name,
        "duplicate_option": duplicate_option
    }

    create_response = requests.put(create_url, headers=headers, json=payload)

    if create_response.status_code in [200, 201]:
        new_contact = create_response.json()

        # Add the specified tag to the new contact
        contact_id = new_contact.get("id")
        if contact_id:
            tag_id = get_tag_id(base_url, access_token, tag_name)
            if tag_id:
                add_tag_response = add_tag_to_contact(base_url, access_token, contact_id, tag_id)
                if add_tag_response.get("error"):
                    print("Error tagging contact:", add_tag_response["error"])
                else:
                    print(f"Tag '{tag_name}' added successfully to new contact {contact_id}.")
        
        return new_contact
    else:
        print("Error creating contact:", create_response.status_code, create_response.text)
        return {"error": "Failed to create contact"}

def get_contact(base_url: str, access_token: str, contact_id: int):
    """
    Retrieves the contact details from Keap.

    Args:
        base_url (str): Keap API base URL.
        access_token (str): Keap API access token.
        contact_id (int): ID of the contact.

    Returns:
        dict: Contact details.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    contact_url = f"{base_url}/contacts/{contact_id}"
    response = requests.get(contact_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching contact details:", response.status_code, response.text)
        return {}

def get_tag_id(base_url: str, access_token: str, tag_name: str):
    """
    Retrieves the ID of a tag by its name.

    Args:
        base_url (str): Keap API base URL.
        access_token (str): Keap API access token.
        tag_name (str): Name of the tag.

    Returns:
        int or None: ID of the tag if found, otherwise None.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    tags_url = f"{base_url}/tags"
    response = requests.get(tags_url, headers=headers)

    if response.status_code == 200:
        tags = response.json().get("tags", [])
        for tag in tags:
            if tag["name"] == tag_name:
                return tag["id"]
    else:
        print("Error retrieving tag ID:", response.status_code, response.text)
    return None

def add_tag_to_contact(base_url: str, access_token: str, contact_id: int, tag_id: int):
    """
    Adds a tag to a Keap contact.

    Args:
        base_url (str): Keap API base URL.
        access_token (str): Keap API access token.
        contact_id (int): ID of the contact.
        tag_id (int): ID of the tag.

    Returns:
        dict: API response as a dictionary.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    tags_url = f"{base_url}/contacts/{contact_id}/tags"
    payload = {"tagIds": [tag_id]}

    response = requests.post(tags_url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        return response.json()
    else:
        print("Error adding tag:", response.status_code, response.text)
        return {"error": response.text}

@auth_app.route('/create-keap-user', methods=['POST'])
def create_keap_user():
    data = request.get_json()

    BASE_URL = "https://api.infusionsoft.com/crm/rest/v1"
    ACCESS_TOKEN = os.environ.get('KEAP_API_KEY')
    email = data.get("email") 
    first_name = data.get("firstName")
    last_name = data.get("lastName")

    response = search_create_update_keap_contact(
        base_url=BASE_URL,
        access_token=ACCESS_TOKEN,
        email=email,
        family_name=last_name,
        given_name=first_name
    )
    return response

if __name__ == '__main__':
    auth_app.run(host='0.0.0.0', port=5002, debug=True)
