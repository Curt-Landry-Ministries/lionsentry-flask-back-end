import firebase_admin
from firebase_admin import credentials, firestore, auth

# Initialize Firebase Admin SDK
cred = credentials.Certificate("../firebase/lionsentry-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Step 1: Build a list of all user IDs from the 'users' collection
def get_all_user_ids():
    users_ref = db.collection("users")
    user_ids = [doc.id for doc in users_ref.stream()]
    print(f"Total users found: {len(user_ids)}")
    return set(user_ids)

# Step 2: Automatically delete orphaned documents in specified collections if the userId is not in the users list
def clean_orphaned_documents(user_ids, collections_with_user_ids):
    for collection_name, user_id_field in collections_with_user_ids.items():
        collection_ref = db.collection(collection_name)
        docs = collection_ref.stream()
        for doc in docs:
            doc_data = doc.to_dict()
            if user_id_field in doc_data:
                user_id = doc_data[user_id_field]
                if user_id not in user_ids:
                    # Automatically delete without confirmation
                    collection_ref.document(doc.id).delete()
                    print(f"Deleted {collection_name} document with ID: {doc.id}")
            else:
                print(f"Warning: Document {doc.id} in {collection_name} does not have field '{user_id_field}'")

# Step 3: Prompt for confirmation before deleting Firebase Auth users without matching Firestore user records
def clean_orphaned_auth_users(user_ids):
    page = auth.list_users()
    while page:
        for user in page.users:
            if user.uid not in user_ids:
                email = user.email or "No email"
                response = input(f"Do you want to delete auth user with UID {user.uid}, Email: {email}? (yes/no): ")
                if response.lower() == "yes":
                    auth.delete_user(user.uid)
                    print(f"Deleted Firebase Auth user with UID: {user.uid}, Email: {email}")
        page = page.get_next_page()

# Main function to execute steps
def main():
    user_ids = get_all_user_ids()
    
    # Define which collections and fields to check
    collections_with_user_ids = {
        "devotionals": "forUser",
        "goals": "forUser",
        "onboardingAnswers": "userID",
        "whyStatements": "forUser"
    }
    
    print("Starting cleanup of Firestore documents.")
    clean_orphaned_documents(user_ids, collections_with_user_ids)
    
    print("Starting cleanup of Firebase Auth users.")
    clean_orphaned_auth_users(user_ids)

if __name__ == "__main__":
    main()
