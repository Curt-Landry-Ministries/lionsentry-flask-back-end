import firebase_admin
from firebase_admin import credentials

# Set up our firebase admin SDK which lets us access the Firebase Auth service

cred = credentials.Certificate(
    "./lionsentry-firebase-adminsdk.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
    