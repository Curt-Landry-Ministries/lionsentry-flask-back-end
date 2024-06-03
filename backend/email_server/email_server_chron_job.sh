#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Variables
CRON_SCHEDULE="0 3 * * *"
SCRIPT_PATH="/usr/local/bin/schedule_emails.sh"
ENDPOINT_URL="https://emailserver.lionsentry.com.com/schedule-emails"
API_KEY=$EMAIL_SERVER_API_KEY

# Create the script that will be called by cron
echo "#!/bin/bash" > $SCRIPT_PATH
echo "curl -X POST $ENDPOINT_URL -H 'EMAIL-SERVER-API-KEY: $API_KEY'" >> $SCRIPT_PATH

# Make the script executable
chmod +x $SCRIPT_PATH

# Add the cron job
(crontab -l ; echo "$CRON_SCHEDULE $SCRIPT_PATH") | crontab -

echo "Cron job set to hit $ENDPOINT_URL every day at 3am PST."
