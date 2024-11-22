import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore, storage
from backend.firebase.config import cred_dict

# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize Firebase Admin SDK
cred = credentials.Certificate(cred_dict)

# Add storage bucket name from environment
bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")

# Initialize Firebase app with storage bucket
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {'storageBucket': bucket_name})

# Initialize Firestore client
db = firestore.client()

# Initialize Firebase Storage bucket
bucket = storage.bucket()