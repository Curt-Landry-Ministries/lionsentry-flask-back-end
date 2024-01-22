# FOR TESTING ONLY - reset the database and re-initialize the test user
import firebase_admin
from firebase_admin import credentials, auth, firestore
from pathlib import Path
from server_utils import TestAuthServerBase
import concurrent.futures


# Initialize Firebase Admin
def initialize_firebase():
    project_root = Path(__file__).resolve().parents[2]
    firebase_credentials_path = project_root / "backend/firebase/lionsentry-firebase-adminsdk.json"
    cred = credentials.Certificate(str(firebase_credentials_path))
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

# Delete all authentication records
def delete_auth_records():
    page = auth.list_users()
    while page:
        for user in page.users:
            auth.delete_user(user.uid)
        page = page.get_next_page()

# Delete Firestore collections

def delete_firestore_collections():
    db = firestore.client()
    collections = ['users', 'onboardingFlows', 'onboardingAnswers', 'whyStatements', 'devotionals', 'emailQueue']

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(delete_collection, db.collection(collection)) for collection in collections]
        concurrent.futures.wait(futures)


# Helper to delete a Firestore collection
def delete_collection(collection):
    docs = collection.stream()
    for doc in docs:
        doc.reference.delete()

# Create test user using TestAuthServer
def create_test_user():
    test_server = TestAuthServerBase()
    test_server.setUp()  # Ensure the test server is set up correctly
    user_id, email = test_server.create_user_with_credentials("testAccount@lionsentry.com", "Password")
    if user_id:
        print(f"Test user created successfully: {email} (ID: {user_id})")
    else:
        print("Failed to create test user.")

# Main execution
def main():
    print("Databases in peril, a serious choice now calls")
    print("Erase all data, and watch as each record falls")
    print("Are you sure to nuke? \n(y/n):")

    choice = input().strip().lower()
    if choice == 'y':
        print("Anihilating all data...")
        initialize_firebase()
        delete_auth_records()
        delete_firestore_collections()
        create_test_user()
        print("Database nuked and test user recreated successfully.")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main()
