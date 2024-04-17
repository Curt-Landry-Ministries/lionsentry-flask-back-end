# lionsentry-flask-back-end
Repository for LionSentry flask back-end

## Overview 🌟

LionSentry Flask Back-end

## Technical Overview 🏗️

- **Backend**: Flask, divided into:
  - Application server for general logic.
  - Authentication server for user data handling.
  - Notification server for message delivery.
- **Firebase Integration**: For robust authentication and Firestore for real-time data synchronization.
- **Docker Setup**: Simplifies development and deployment with a one-step build process.

## Build Script 🛠️

The build script (`build.sh`) ensures a smooth setup. Use the `-f` flag for a full setup, including Docker image management and service initialization.

## Development Environment 🖥️

Developed on Mac with Python venv. End-to-end testing is conducted using pytest.

- **Python Version**: 3.8
- **pip Version**: 23.3.1

### Virtual Environment Setup 🐍

- **PYTHONHOME**: Unset if set. This avoids conflicts with the virtual environment.
- **PYTHONPATH**: Set to the project root directory (`/xxx/Documents/GitHub/LionSentry/`) for proper module resolution.

## Installation and Setup 📦

**Clone the project and start virtual env**: 
   ```
   git clone git@github.com:Curt-Landry-Ministries/LionSentry.git
   cd LionSentry
   python3 -m venv venv
   source venv/bin/activate
   python3 -m pip install --upgrade pip
   ```
**Install requirments and run build script inside environment**: 
   ```
   pip install -r requirements.txt
   sudo ./build.sh -f
   ```

## Accessing the App 🌐

- **Application Server**: Runs on port 5001.
- **Authentication Server**: Runs on port 5002.
- **Email Server**: Runs on port 5003.

## Contact 👋
For any setup-related questions, please message Griffin Clark via Slack
