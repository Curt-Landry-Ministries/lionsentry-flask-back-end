
import os
import json
import logging
import datetime
from datetime import datetime, timedelta
from functools import wraps
from flask_cors import CORS
from firebase_admin import auth, firestore
from backend import public_server_template as pst
from flask import Flask, request, jsonify, session
from backend.firebase.firebase_admin_sdk import db
from backend.app_server.algorithms.LLM.generate_devotional import generate_devotional_content
from backend.app_server.algorithms.LLM.generate_why_statement import generate_why_statement as generate_why_statement_content
from firebase_admin import storage
from werkzeug.utils import secure_filename
import uuid


app = Flask(__name__)
CORS(app)

base_dir = pst.get_base_directory()
app.secret_key = 'your_secret_key_here'
logging.basicConfig(level=logging.DEBUG)
pst.setup_session(app)
pst.setup_logging(app)
pst.setup_cors(app)

base_dir = pst.get_base_directory()
user_answers = {}

# Auth Token
   
def verify_firebase_token(f):
    # Decoder to verify the Firebase ID token
    @wraps(f)
    def decorator(*args, **kwargs):
        token_header = request.headers.get('Authorization')
        if token_header and token_header.startswith('Bearer '):
            token = token_header.split(' ')[1]
        else:
            logging.error("Authentication token is missing or invalid")
            return jsonify({"error": "Authentication token is missing or invalid"}), 401

        try:
            decoded_token = auth.verify_id_token(token)
            logging.debug("Token successfully verified")
            kwargs['decoded_token'] = decoded_token
        except Exception as e:
            logging.error(f"Invalid authentication token: {e}")
            return jsonify({"error": "Invalid authentication token"}), 401
        return f(*args, **kwargs)
    return decorator


# generate email route - probably going away

@app.route('/generate-email', methods=['POST'])
@verify_firebase_token
def generate_email_route():
    logging.debug("Accessing /generate-email endpoint")
    try:
        data = request.json
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Query Firestore for the user's Why Statement
        why_statement_docs = db.collection('whyStatements').where('forUser', '==', user_id).get()
        if len(why_statement_docs) == 0:
            return jsonify({"error": "Why Statement not found for the user"}), 404

        why_statement = why_statement_docs[0].to_dict().get('whyStatement', '')
        user_fname = why_statement_docs[0].to_dict().get('firstName', '')
        # Generate a devotional using the user's Why Statement
        devotional_content = generate_devotional_content(user_fname, why_statement)

        # Store the devotional in Firestore
        dateTimeCreated = datetime.now().isoformat()
        devotional_record = {
            "title": devotional_content["Title"],
            "biblePassage": devotional_content["BiblePassage"],
            "personalization": devotional_content["Personalization"],
            "journalingPrompt": devotional_content["JournalingPrompt"],
            "dateTimeCreated": dateTimeCreated,
            "forUser": user_id
        }
        db.collection('devotionals').add(devotional_record)

        return jsonify(devotional_content)
    except Exception as e:
        app.logger.error(f'Failed to generate devotional content: {e}', exc_info=True)
        return jsonify({"error": "Failed to generate devotional content"}), 500

# starrt devotionals routes

@app.route('/generate-devotional', methods=['POST'])
@verify_firebase_token
def generate_devotional_route(decoded_token):
    try:
        user_id = decoded_token['uid']
        
        # Determine the most recent 05:59 UTC (i.e., the start of the daily limit period)
        # now = datetime.utcnow()
        # if now.hour < 6:
        #     reset_time = now.replace(hour=6, minute=0, second=0, microsecond=0) - timedelta(days=1)
        # else:
        #     reset_time = now.replace(hour=6, minute=0, second=0, microsecond=0)

        # # Query devotionals created by this user since the most recent reset time
        # devotional_query = db.collection('devotionals').where('forUser', '==', user_id).where(
        #     'dateTimeCreated', '>=', reset_time.isoformat())
        # devotionals_today = devotional_query.stream()
        
        # # Check if user has reached the limit of 3 devotionals
        # if len(list(devotionals_today)) >= 3:
        #     app.logger.error(f'Daily limit reached for user {user_id}')
        #     return jsonify({"error": "Daily limit reached", "code": "LIMIT_REACHED"}), 429
        
        # Fetch the user's Why Statement
        why_statement_docs = db.collection('whyStatements').where('forUser', '==', user_id).get()
        if len(why_statement_docs) == 0:
            return jsonify({"error": "Why Statement not found for the user"}), 404

        why_statement = why_statement_docs[0].to_dict().get('whyStatement', '')

        # Query to fetch user's firstName
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({"error": "User not found"}), 404

        user_data = user_doc.to_dict()
        first_name = user_data.get('firstName', 'Member')

        print(first_name)

        # Ensure why_statement is in dictionary format
        if isinstance(why_statement, str):
            why_statement = {"whyStatement": why_statement}

        # Generate the devotional content based on why_statement
        devotional_content = generate_devotional_content(first_name, why_statement)

        # Check if devotional_content is a string and parse it to a dictionary
        if isinstance(devotional_content, str):
            try:
                devotional_content = json.loads(devotional_content)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                return jsonify({"error": "Failed to parse devotional content"}), 500

        # Debugging to confirm it's a dictionary
        print(type(devotional_content))
        print(devotional_content)

        dateTimeCreated = datetime.now().isoformat()
        doc_uid = uuid.uuid4().hex
        devotional_record = {
            "introduction": devotional_content["introduction"],
            "verse": devotional_content["verse"],
            "insight": devotional_content["insight"],
            "life_application": devotional_content["life_application"],
            "declaration": devotional_content["declaration"],
            "prayer": devotional_content["prayer"],
            "dateTimeCreated": dateTimeCreated,
            "forUser": user_id,
            "doc_id": doc_uid,
            "isFavorite": False
        }
        
        # Save the devotional in Firestore
        db.collection('devotionals').add(devotional_record)

        # Log and return the devotional content
        app.logger.info(jsonify(devotional_record))
        return jsonify(devotional_record)
        
    except Exception as e:
        app.logger.error(f'Failed to generate devotional content: {e}', exc_info=True)
        return jsonify({"error": "Failed to generate devotional content"}), 500

@app.route('/get-devotionals', methods=['GET'])
@verify_firebase_token
def get_devotionals(decoded_token):
    try:
        user_id = decoded_token['uid']
        devotionals_query = db.collection('devotionals').where('forUser', '==', user_id).order_by('dateTimeCreated', direction=firestore.Query.DESCENDING)
        devotionals_docs = devotionals_query.stream()

        devotionals = []
        for doc in devotionals_docs:
            devotional_data = doc.to_dict()
            # if there's no doc_id (for legacy devotionals), add one using the doc id
            if 'doc_id' not in devotional_data:
                devotional_data['doc_id'] = uuid.uuid4().hex
            devotionals.append(devotional_data)
        return jsonify(devotionals)
    except Exception as e:
        app.logger.error(f'Failed to get devotionals: {e}', exc_info=True)
        return jsonify({"error": "Failed to retrieve devotionals"}), 500
    
@app.route('/update-devotional', methods=['PUT'])
@verify_firebase_token
def update_devotional(decoded_token):
    try:
        user_id = decoded_token['uid']
        data = request.get_json()

        # Validate request data
        if not data or 'doc_id' not in data or not isinstance(data['doc_id'], str):
            return jsonify({"error": "Invalid request data"}), 400

        doc_id = data['doc_id']
        is_favorite = data.get('isFavorite')

        if is_favorite is None or not isinstance(is_favorite, bool):
            return jsonify({"error": "Invalid or missing isFavorite value"}), 400

        # Fetch the devotional document by doc_id
        devotionals_query = db.collection('devotionals').where('doc_id', '==', doc_id).limit(1)
        devotional_docs = list(devotionals_query.stream())

        if not devotional_docs:
            return jsonify({"error": "Devotional not found"}), 404

        devotional_doc = devotional_docs[0]
        devotional_data = devotional_doc.to_dict()

        # Verify the devotional belongs to the authenticated user
        if devotional_data.get('forUser') != user_id:
            return jsonify({"error": "Unauthorized access to devotional"}), 403

        # Update only the isFavorite field
        devotional_doc.reference.update({'isFavorite': is_favorite})

        return jsonify({
            "message": "Devotional updated successfully",
            "doc_id": doc_id,
            "updatedFields": {"isFavorite": is_favorite}
        }), 200

    except Exception as e:
        app.logger.error(f'Failed to update devotional: {e}', exc_info=True)
        return jsonify({"error": "Failed to update devotional"}), 500

# end devotionals routes
# start goals routes

@app.route('/save-goals', methods=['POST'])
@verify_firebase_token
# goals have a goal, category, string, deadline, created, isComplete, isDeleted=false, forUser
def save_goals(decoded_token):
    try:
        app.logger.debug("Hit save goal endpoint")
        user_id = decoded_token['uid']
        data = request.json
        goal = data.get('goal')
        description = data.get('description')
        category = data.get('category')
        deadline = data.get('deadline')
        created = datetime.now().isoformat()
        is_complete = False
        is_deleted = False
        doc_id=uuid.uuid4().hex

        goal_record = {
            "goal": goal,
            "description": description,
            "category": category,
            "deadline": deadline,
            "created": created,
            "isComplete": is_complete,
            "isDeleted": is_deleted,
            "forUser": user_id,
            "doc_id": doc_id
        }

        db.collection('goals').add(goal_record)
        
        return jsonify({"message": "Goal saved successfully"}), 200
    except Exception as e:
        app.logger.error(f'Failed to save goal: {e}', exc_info=True)
        return jsonify({"error": "Failed to save goal"}), 500
    
@app.route('/get-goals', methods=['GET'])
@verify_firebase_token
def get_goals(decoded_token):
    try:
        user_id = decoded_token['uid']
        goals_query = db.collection('goals').where('forUser', '==', user_id).where('isDeleted', '==', False)
        goals_docs = goals_query.stream()

        goals = []
        for doc in goals_docs:
            goal_data = doc.to_dict()

            # handle legacy goals not having doc_id's
            if 'doc_id' not in goal_data:
                goal_data['doc_id'] = uuid.uuid4().hex
                doc.reference.update({"doc_id": goal_data['doc_id']})
            goals.append(goal_data)

        return jsonify(goals)
    except Exception as e:
        app.logger.error(f'Failed to get goals: {e}', exc_info=True)
        return jsonify({"error": "Failed to retrieve goals"}), 500

@app.route('/update-goal', methods=['PUT'])
@verify_firebase_token
def update_goal(decoded_token):
    try:
        user_id = decoded_token['uid']
        data = request.get_json()

        # Validate request data
        if not data or 'doc_id' not in data or not isinstance(data['doc_id'], str):
            return jsonify({"error": "Invalid request data. 'doc_id' is required."}), 400

        if 'updateFields' not in data or not isinstance(data['updateFields'], dict):
            return jsonify({"error": "Invalid request data. 'updateFields' is required."}), 400

        doc_id = data['doc_id']
        update_fields = data['updateFields']

        # Allowed fields for updating
        allowed_fields = {'goal', 'category', 'deadline', 'description', 'isComplete'}
        update_data = {key: value for key, value in update_fields.items() if key in allowed_fields}

        if not update_data:
            return jsonify({"error": "No valid fields to update."}), 400

        # Fetch the goal document by doc_id
        goals_query = db.collection('goals').where('doc_id', '==', doc_id).limit(1)
        goal_docs = list(goals_query.stream())

        if not goal_docs:
            return jsonify({"error": "Goal not found."}), 404

        goal_doc = goal_docs[0]
        goal_data = goal_doc.to_dict()

        # Verify the goal belongs to the authenticated user
        if goal_data.get('forUser') != user_id:
            return jsonify({"error": "Unauthorized access to this goal."}), 403

        # Update the document with valid fields
        goal_doc.reference.update(update_data)

        return jsonify({
            "message": "Goal updated successfully",
            "doc_id": doc_id,
            "updatedFields": update_data
        }), 200

    except Exception as e:
        app.logger.error(f"Failed to update goal: {e}", exc_info=True)
        return jsonify({"error": "Failed to update goal."}), 500

# end goals routes
# start user routes

@app.route('/upload-profile-photo', methods=['POST'])
def upload_profile_photo():
    try:
        # Verify if the request has a file part
        if 'photo' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['photo']

        # Check if the user selected a file
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Ensure the file has a valid filename
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Generate a unique filename to avoid collisions
            unique_filename = f"{uuid.uuid4().hex}_{filename}"

            # Firebase storage bucket
            bucket = storage.bucket()

            # Upload the file to Firebase Storage
            blob = bucket.blob(f"profile_photos/{unique_filename}")

            # Optionally, set the blob to be publicly accessible (if you want public access to the image)
            blob.upload_from_file(file, content_type=file.content_type)
            blob.make_public()  # Make the image publicly accessible

            # Get the public URL
            photo_url = blob.public_url

            # Add the photo URL to the user's Firestore document
            user_id = request.form.get('user_id')
            user_ref = db.collection('users').document(user_id)
            user_ref.update({"photoURL": photo_url})

            # Return the URL of the uploaded file
            return jsonify({"photo_url": photo_url}), 200

        else:
            return jsonify({"error": "Invalid file type"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/get-user-info', methods=['GET'])
@verify_firebase_token
def get_user_info(decoded_token):
    try:
        user_id = decoded_token['uid']
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()

        if user_doc.exists:
            user_data = user_doc.to_dict()
            return jsonify(user_data)
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        app.logger.error(f'Failed to get user info: {e}', exc_info=True)
        return jsonify({"error": "Failed to retrieve user info"}), 500


def allowed_file(filename):
    """Check if the uploaded file is a valid image type."""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# end user routes
# start why statement routes

@app.route('/generate-why-statement', methods=['POST'])
@verify_firebase_token
def generate_why_statement_route(decoded_token):
    try:
        # Log incoming request payload
        app.logger.info("Incoming JSON payload: %s", request.json)

        # Validate input
        if isinstance(request.json, list):
            # If payload is a list, process it directly
            answers = request.json
            save_to_firestore = True  # Default if not specified in this case
        elif isinstance(request.json, dict):
            # If payload is a dict, extract answers and saveToFirestore
            answers = request.json.get("answers", [])
            save_to_firestore = request.json.get("saveToFirestore", True)
        else:
            return jsonify({"error": "Malformed data: Expected JSON object or array"}), 400

        if not answers:
            return jsonify({"error": "No answers provided"}), 400

        # Generate the Why Statement content
        questions_answers = [{"question": ans["questions"], "answer": ans["answer"]} for ans in answers]

        # Parse the string to a dictionary
        why_statement_content = generate_why_statement_content(questions_answers)
        print(why_statement_content)

        try:
            # Convert JSON string to Python dictionary
            why_statement_content = json.loads(why_statement_content)

            # Prepare response data
            response_data = {
                "whyStatement": why_statement_content.get("why_statement"),
                "purposeStatement": why_statement_content.get("purpose_statement")
            }

            if save_to_firestore:
                user_id = decoded_token['uid']
                dateTimeCreated = datetime.now().isoformat()
                why_statement_record = {
                    "whyStatement": response_data['whyStatement'],
                    "purposeStatement": response_data['purposeStatement'],
                    "dateTimeCreated": dateTimeCreated,
                    "forUser": user_id
                }
                doc_ref = db.collection('whyStatements').add(why_statement_record)[1]
                response_data['doc_id'] = doc_ref.id

            return jsonify(response_data)

        except json.JSONDecodeError as e:
            print("Failed to parse JSON:", e)
            return jsonify({"error": "Invalid response format"}), 500

    except KeyError as e:
        app.logger.error("KeyError: %s. Data received: %s", e, request.json)
        return jsonify({"error": "Malformed data"}), 400
    except Exception as e:
        app.logger.error("Unhandled exception: %s", e, exc_info=True)
        return jsonify({"error": "Failed to generate why statement"}), 500
 
@app.route('/get-latest-why-statement', methods=['GET', 'OPTIONS'])
@verify_firebase_token
def get_latest_why_statement(decoded_token):
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({"message": "CORS preflight check successful"})
        response.status_code = 200
        return response
    try:
        user_id = decoded_token['uid']

        # Query Firestore for the most recent Why Statement for the user
        why_statement_query = db.collection('whyStatements')\
                                .where('forUser', '==', user_id)\
                                .order_by('dateTimeCreated', direction=firestore.Query.DESCENDING)\
                                .limit(1)
        why_statement_docs = why_statement_query.stream()

        # Extract the most recent Why Statement
        for doc in why_statement_docs:
            why_statement_data = doc.to_dict()
            return jsonify(why_statement_data), 200

        return jsonify({"error": "No Why Statement found for the user"}), 404
    except Exception as e:
        app.logger.error(f'Failed to retrieve latest why statement: {e}', exc_info=True)
        return jsonify({"error": "Failed to retrieve latest why statement"}), 500


# end why statement routes
# start user routes

@app.route('/submit-onboarding-answer', methods=['POST'])
@verify_firebase_token  
def submit_answer(decoded_token):
    try:
        user_id = decoded_token['uid']  # Extracting user ID from the decoded token
        question = request.json.get("question")
        answer_text = request.json.get("answer")
        question_index = request.json.get("questionIndex")
        dateTimeAnswered = datetime.now().isoformat()  # Current timestamp

        # Construct the answer object
        answer_object = {
            "answer": answer_text,
            "dateTimeAnswered": dateTimeAnswered
        }

        # Check if there's an existing document for this question and user
        answers_query = db.collection('onboardingAnswers').where('userID', '==', user_id).where('question', '==', question)
        documents = list(answers_query.stream())

        if documents:
            # If the record exists, add the new answer to the 'answers' array
            answer_doc = documents[0]
            answer_doc.reference.update({
                "answers": firestore.ArrayUnion([answer_object])
            })
        else:
            # If the record does not exist, create a new one
            new_answer_record = {
                "question": question,
                "userID": user_id,
                "answers": [answer_object],
                "questionIndex": question_index
            }
            db.collection('onboardingAnswers').add(new_answer_record)

        return jsonify({"status": "success", "message": "Answer submitted successfully"})
    except Exception as e:
        app.logger.error(f'Failed to submit answer: {e}', exc_info=True)
        return jsonify({"error": "Failed to submit answer"}), 500

@app.route('/save-user-data-point', methods=['OPTIONS', 'POST'])
@verify_firebase_token
def save_user_data_point(decoded_token):
    if request.method == 'OPTIONS':
        # Handle preflight CORS request
        response = jsonify({"message": "CORS preflight check successful"})
        response.status_code = 200
        return response

    try:
        data = request.get_json()
        target_user_id = data.get('targetUserId')
        data_point = data.get('dataPoint')
        action = data.get('action')
        value = data.get('value')

        if not target_user_id:
            return jsonify({"error": "targetUserId is required"}), 400

        user_id = decoded_token['uid']
        app.logger.debug(f"Authenticated user ID: {user_id}, Target user ID: {target_user_id}")

        if user_id != target_user_id:
            return jsonify({"error": "Unauthorized to modify this user's data"}), 403

        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        if not user_doc.exists:
            return jsonify({"error": "User does not exist"}), 404

        if action == 'replace':
            user_ref.update({data_point: value})
        elif action == 'append' and isinstance(value, list):
            user_ref.update({data_point: firestore.ArrayUnion(value)})
        else:
            return jsonify({"error": "Invalid action or value type"}), 400

        return jsonify({"message": "User data updated successfully"}), 200
    except Exception as e:
        app.logger.error(f'Error in save_user_data_point: {str(e)}', exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/get-questions', methods=['GET'])
# Grab the static questions and feed them to the frontend
def get_questions():
    try:
        # Construct the absolute path for the questions.json
        questions_path = os.path.join(base_dir, "data/questions.json")

        with open(questions_path, 'r') as file:
            questions = json.load(file)
        return jsonify(questions)
    except Exception as e:
        app.logger.error(f'Failed to get questions: {e}', exc_info=True)
        return jsonify({"error": "Failed to retrieve questions"}), 500

@app.route('/get-latest-answer', methods=['POST'])
# Get an answer for a specific question
@verify_firebase_token
def get_latest_answer(decoded_token):
    user_id = decoded_token['uid']
    question = request.json.get('question')

    # Query Firestore for the latest answer for the question and user
    answers_query = db.collection('onboardingAnswers').where('userID', '==', user_id).where('question', '==', question)
    documents = list(answers_query.stream())

    if documents:
        # If the record exists, get the latest answer
        answer_doc = documents[0].to_dict()
        latest_answer = answer_doc['answers'][-1]  # Assuming the answers are appended and the last one is the latest
        return jsonify(latest_answer)
    else:
        # If no answer is found, return an appropriate response
        return jsonify({"error": "No answer found for the given question"}), 404
    
@app.route('/get-all-answers', methods=['GET'])
@verify_firebase_token
def get_all_answers(decoded_token):
    try:
        user_id = decoded_token['uid']
        
        # Query Firestore for all answer documents for the user
        answers_query = db.collection('onboardingAnswers').where('userID', '==', user_id)
        answer_documents = answers_query.stream()

        # Collect all answers in a list
        all_answers = []
        for answer_doc in answer_documents:
            answer_data = answer_doc.to_dict()
            all_answers.append(answer_data)

        return jsonify(all_answers)
    except Exception as e:
        app.logger.error(f'Failed to get all answers: {e}', exc_info=True)
        return jsonify({"error": "Failed to retrieve all answers"}), 500


if __name__ == '__main__':
    app.logger.info('Server startup')
    app.run(host='0.0.0.0', debug=True, port=5001)
