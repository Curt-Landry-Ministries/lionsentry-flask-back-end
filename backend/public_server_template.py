import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask_cors import CORS

# Adhering to DRY, we can extract functionality that is common to both the Auth and App servers into this file like CORS, logging, and session setup.

# Get the absolute path of the directory where this script is located
template_dir = os.path.dirname(os.path.abspath(__file__))


def setup_logging(app, log_directory='logs'):
    # Modify the log directory path to be relative to the template directory
    log_directory = os.path.join(template_dir, log_directory)

    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f'{log_directory}/{current_time}.log'

    # Ensure the directory exists
    os.makedirs(log_directory, exist_ok=True)

    # Setup logger
    file_handler = RotatingFileHandler(
        log_filename, maxBytes=1000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    class NoAccessFilter(logging.Filter):
        def filter(self, record):
            if '"GET' in record.getMessage() or '"POST' in record.getMessage() or '"OPTIONS' in record.getMessage():
                return False
            return True

    # Apply the filter to the file handler
    file_handler.addFilter(NoAccessFilter())

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)


def get_base_directory():
    return os.path.dirname(os.path.abspath(__file__))


def setup_cors(app, origins=["http://localhost:5003", "https://lionsentry.com"]):
    CORS(app, origins=origins, supports_credentials=True)


def setup_session(app, secret_key='your_secret_key_here'):
    app.secret_key = secret_key
    # Additional session configuration can go here if needed


def setup_after_request(app):
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization')
        response.headers.add(
            'Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response
