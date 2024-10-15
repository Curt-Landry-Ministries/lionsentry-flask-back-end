# App Server Readme

## Data Models

**Users:**
userID: Unique identifier for the user.
email: User's email address.
photoURL: URL of the user's profile photo.
name, firstName, lastName: Basic user information.
accountCreated: Timestamp of when the user created their account.
isDeleted: Boolean flag to indicate if the user account is deleted.

**Goals:**
goal: Description of the user's goal.
category: Category under which the goal falls.
deadline: Deadline for achieving the goal.
isComplete: Boolean flag to mark if the goal is completed.
isDeleted: Boolean flag to mark if the goal is deleted.
forUser: Reference to the user who created the goal.

**Devotionals:**
title: Title of the devotional.
biblePassage: A relevant Bible passage.
personalization: Custom text based on user input.
journalingPrompt: Prompts for the user to reflect on the devotional.
forUser: Reference to the user who created the devotional.

**Why Statements:**
whyStatement: User's personalized "why" statement.
dateTimeCreated: Timestamp of when the why statement was created.
forUser: Reference to the user.

**OnboardingAnswers:**
question: Question text.
answers: List of user responses to the question, each with timestamps.
forUser: Reference to the user who answered the question.

## Endpoints
POST /generate-email:
Generates a devotional email for a user based on their Why Statement.
POST /generate-devotional:
Creates a devotional for the user based on their Why Statement.
GET /get-devotionals:
Fetches a list of devotionals for a logged-in user.
POST /save-goals:
Saves a goal for the authenticated user.
GET /get-goals:
Retrieves all non-deleted goals for the logged-in user.
POST /upload-profile-photo:
Uploads a profile photo for a user to Firebase Storage and saves the URL in Firestore.
GET /get-user-info:
Retrieves information about the logged-in user.
POST /generate-why-statement:
Generates a Why Statement for a user based on their answers to onboarding questions.
GET /get-latest-why-statement:
Fetches the latest Why Statement for the user.
POST /submit-onboarding-answer:
Submits an answer for a user's onboarding question.
POST /get-latest-answer:
Retrieves the latest answer for a specific onboarding question.
GET /get-all-answers:
Fetches all answers provided by the user during the onboarding process.
POST /save-user-data-point:
Allows users to update a specific data point in their user profile.

## How to Get a Profile Photo URL for a User

Upload the profile photo via the /upload-profile-photo endpoint:

This endpoint takes a photo file and a user_id in the request and uploads the image to Firebase Storage.
After successfully uploading the image, the photo URL is stored in the user's Firestore document.
Fetch the user's profile photo URL using /get-user-info:

This endpoint retrieves the user's data from Firestore, including the photoURL if it has been set.
