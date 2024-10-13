
import os
import json
import logging
import datetime
from functools import wraps
from flask_cors import CORS
from firebase_admin import auth, firestore
from backend import public_server_template as pst
from flask import Flask, request, jsonify, session
from backend.firebase.firebase_admin_sdk import db
from backend.app_server.algorithms.LLM.generate_devotional import generate_devotional_content
from backend.app_server.algorithms.LLM.generate_why_statement import generate_why_statement as generate_why_statement_content

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

        # Generate a devotional using the user's Why Statement
        devotional_content = generate_devotional_content(why_statement)

        # Store the devotional in Firestore
        dateTimeCreated = datetime.datetime.now().isoformat()
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
    
@app.route('/generate-devotional', methods=['POST'])
@verify_firebase_token
def generate_devotional_route(decoded_token):
    try:
        user_id = decoded_token['uid']

        why_statement_docs = db.collection('whyStatements').where('forUser', '==', user_id).get()

        if len(why_statement_docs) == 0:
            return jsonify({"error": "Why Statement not found for the user"}), 404

        why_statement = why_statement_docs[0].to_dict().get('whyStatement', '')

        # Check if why_statement is a string, if not, convert it to a dictionary
        if isinstance(why_statement, str):
            why_statement = {"whyStatement": why_statement}

        devotional_content = generate_devotional_content(why_statement)

        dateTimeCreated = datetime.datetime.now().isoformat()
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
            devotionals.append(devotional_data)

        return jsonify(devotionals)
    except Exception as e:
        app.logger.error(f'Failed to get devotionals: {e}', exc_info=True)
        return jsonify({"error": "Failed to retrieve devotionals"}), 500
    
@app.route('/save-goals', methods=['POST'])
@verify_firebase_token
# goals have a goal, category, string, deadline, created, isComplete, isDeleted=false, forUser
def save_goals(decoded_token):
    try:
        user_id = decoded_token['uid']
        data = request.json
        goal = data.get('goal')
        category = data.get('category')
        deadline = data.get('deadline')
        created = datetime.datetime.now().isoformat()
        is_complete = False
        is_deleted = False

        goal_record = {
            "goal": goal,
            "category": category,
            "deadline": deadline,
            "created": created,
            "isComplete": is_complete,
            "isDeleted": is_deleted,
            "forUser": user_id
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
            goals.append(goal_data)

        return jsonify(goals)
    except Exception as e:
        app.logger.error(f'Failed to get goals: {e}', exc_info=True)
        return jsonify({"error": "Failed to retrieve goals"}), 500

@app.route('/generate-why-statement', methods=['POST'])
@verify_firebase_token
def generate_why_statement_route(decoded_token):
    try:
        user_id = decoded_token['uid']

        # Query Firestore for all answer documents for the user
        answers_query = db.collection('onboardingAnswers').where('userID', '==', user_id)
        answers_docs = answers_query.stream()

        # Collect the most recent answer for each question
        recent_answers = {}
        for answer_doc in answers_docs:
            answer_data = answer_doc.to_dict()
            question = answer_data['question']
            # Assuming the answers are sorted in the array with the most recent last
            most_recent_answer = answer_data['answers'][-1]
            recent_answers[question] = most_recent_answer

        # Get the answer texts and create a list of question-answer pairs
        questions_answers = [{"question": q, "answer": a['answer']} for q, a in recent_answers.items()]

        # Generate the Why Statement content
        why_statement_content = generate_why_statement_content(questions_answers)

        # Check if the user wants to save the WhyStatement record to Firestore
        save_to_firestore = request.json.get("saveToFirestore", True)
        response_data = {"whyStatement": why_statement_content.get("whyStatement")}
        if save_to_firestore:
            dateTimeCreated = datetime.datetime.now().isoformat()
            why_statement_record = {
                "whyStatement": response_data['whyStatement'],
                "dateTimeCreated": dateTimeCreated,
                "forUser": user_id
            }
            doc_ref = db.collection('whyStatements').add(why_statement_record)[1]
            response_data['doc_id'] = doc_ref.id

        return jsonify(response_data)
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


@app.route('/submit-onboarding-answer', methods=['POST'])
@verify_firebase_token  
def submit_answer(decoded_token):
    try:
        user_id = decoded_token['uid']  # Extracting user ID from the decoded token
        question = request.json.get("question")
        answer_text = request.json.get("answer")
        question_index = request.json.get("questionIndex")
        dateTimeAnswered = datetime.datetime.now().isoformat()  # Current timestamp

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
