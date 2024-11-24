import requests
import dotenv
import logging
import os

# Load environment variables from .env file
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Firebase API key for authentication
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

# Endpoints
auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"

def sign_in():
    print("Signing in to your account...")
    email = "gclark0812@gmail.coma"  # Your account email
    password = "f(VpRN1<Ji+QYX2e4i0J"  # Your account password

    # Payload for Firebase authentication
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    # Send the POST request to Firebase Auth for login
    response = requests.post(auth_url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        id_token = data['idToken']
        logging.info(f"Signed in successfully. ID Token: {id_token}")
        return id_token  # Return only the Firebase ID token
    else:
        logging.error(f"Login failed: {response.text}")
        return None

if __name__ == "__main__":
    # Authenticate and retrieve Firebase ID token
    id_token = sign_in()
    if id_token:
        # Log the Firebase ID token
        logging.info(f"Decoded Firebase ID token: {id_token}")
    else:
        logging.error("Unable to authenticate and obtain ID token.")
