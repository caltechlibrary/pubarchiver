#!/bin/bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <ARTIFACT_DIR>" >&2
    exit 1
fi

ARTIFACT_DIR="$1"
REPORT_HTML="${ARTIFACT_DIR}/report.html"
RERUN_REPORT_HTML="${ARTIFACT_DIR}/rerun-report.html"
LOG_FILE="${ARTIFACT_DIR}/run.log"
EMAIL_TO="${EMAIL_TO:-}"
EMAIL_SUBJECT="${EMAIL_SUBJECT:-}"
EMAIL_BODY_B64="${EMAIL_BODY_B64:-}"

# Ensure we have an email address
if [[ -z "$EMAIL_TO" ]]; then
    echo "No email recipient configured; skipping email" >&2
    exit 0
fi

# Decode email body from base64
EMAIL_BODY=$(echo "$EMAIL_BODY_B64" | base64 -d)

# Build curl command with attachments
CURL_CMD="curl -s --user \"api:${MAILGUN_API_KEY}\" \\
  https://api.mailgun.net/v3/${MAILGUN_DOMAIN}/messages \\
  -F from='PubArchiver <no-reply@${MAILGUN_DOMAIN}>' \\
  -F to=\"$EMAIL_TO\" \\
  -F subject=\"$EMAIL_SUBJECT\""

# Add text body (using printf to handle special characters safely)
CURL_CMD="$CURL_CMD -F text=@-"

# Add attachments if they exist
[[ -f "$LOG_FILE" ]] && CURL_CMD="$CURL_CMD -F attachment=@$LOG_FILE"
[[ -f "$REPORT_HTML" ]] && CURL_CMD="$CURL_CMD -F attachment=@$REPORT_HTML"
[[ -f "$RERUN_REPORT_HTML" ]] && CURL_CMD="$CURL_CMD -F attachment=@$RERUN_REPORT_HTML"

printf '%s' "$EMAIL_BODY" | eval "$CURL_CMD" || {
    echo "Failed to send email via Mailgun" >&2
    exit 1
}

echo "Email sent to $EMAIL_TO"
exit 0
