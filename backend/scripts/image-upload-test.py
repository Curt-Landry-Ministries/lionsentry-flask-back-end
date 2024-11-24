import os
import json
import requests
from getpass import getpass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Firebase API key from environment
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

# Base URL for your main app server
APP_BASE_URL = "http://localhost:5001"  # The main app server for your API

# Function to sign in via Firebase and return the ID token
def sign_in():
    print("Sign in to your account:")
    email = "gclark0812@gmail.coma"
    password = "f(VpRN1<Ji+QYX2e4i0J" # this is a test acc with no valuable info in it

    # Firebase authentication URL
    login_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    
    # Payload for Firebase authentication
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    # Send the POST request to Firebase
    response = requests.post(login_url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Signed in successfully. User ID: {data['localId']}")
        return data['idToken'], data  # Return the Firebase ID token and user info
    else:
        print(f"Login failed: {response.text}")
        return None, None

def test_upload_and_set_photo(user_id, id_token):
    if not id_token:
        print("Failed to sign in; cannot proceed with the test.")
        return
    
    # Step 1: Upload the photo
    with open('./llama.jpg', 'rb') as img:
        files = {'photo': img}
        data = {'user_id': user_id}
        response = requests.post(
            f"{APP_BASE_URL}/upload-profile-photo",
            headers={'Authorization': f'Bearer {id_token}'},
            files=files,
            data=data
        )

    # Check if the upload was successful
    if response.status_code == 200:
        response_data = response.json()
        photo_url = response_data.get("photo_url")
        print(f"Photo uploaded successfully. URL: {photo_url}")
    else:
        print(f"Photo upload failed: {response.text}")
        return

    # Step 2: Use the uploaded photo URL to update the user's profile
    update_payload = {
        "targetUserId": user_id,
        "dataPoint": "photoURL",
        "action": "replace",
        "value": photo_url
    }

    update_response = requests.post(
        f"{APP_BASE_URL}/save-user-data-point",
        headers={'Authorization': f'Bearer {id_token}', 'Content-Type': 'application/json'},
        json=update_payload
    )

    if update_response.status_code == 200:
        print("User profile photo updated successfully.")
    else:
        print(f"Failed to update user profile photo: {update_response.text}")

def main():
    id_token, user = sign_in()
    if user:
        test_upload_and_set_photo(user['localId'], id_token)
    else:
        print("Sign-in failed; terminating script.")

if __name__ == "__main__":
    main()
