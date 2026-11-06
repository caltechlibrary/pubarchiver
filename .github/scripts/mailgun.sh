#!/bin/bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <ARTIFACT_DIR>" >&2
    exit 1
fi

ARTIFACT_DIR="$1"
REPORT_HTML="${ARTIFACT_DIR}/report.html"
RERUN_REPORT_HTML="${ARTIFACT_DIR}/rerun-report.html"
DOAJ_RESULTS="${ARTIFACT_DIR}/doaj-results.csv"
LOG_FILE="${ARTIFACT_DIR}/run.log"
# The body is read from a file: in an environment variable, a large run's
# report can exceed the 128 KB Linux allows for one, and then every later
# step fails to start with "Argument list too long".
BODY_FILE="${ARTIFACT_DIR}/email-body.txt"
EMAIL_TO="${EMAIL_TO:-}"
EMAIL_SUBJECT="${EMAIL_SUBJECT:-}"

# Ensure we have an email address
if [[ -z "$EMAIL_TO" ]]; then
    echo "No email recipient configured; skipping email" >&2
    exit 0
fi

if [[ ! -f "$BODY_FILE" ]]; then
    echo "Cannot send email: $BODY_FILE does not exist" >&2
    exit 1
fi

# Build curl command with attachments
CURL_CMD="curl -s --user \"api:${MAILGUN_API_KEY}\" \\
  https://api.mailgun.net/v3/${MAILGUN_DOMAIN}/messages \\
  -F from='PubArchiver <no-reply@${MAILGUN_DOMAIN}>' \\
  -F to=\"$EMAIL_TO\" \\
  -F subject=\"$EMAIL_SUBJECT\""

# The text body comes from standard input.
CURL_CMD="$CURL_CMD -F text=@-"

# Add attachments if they exist
[[ -f "$LOG_FILE" ]] && CURL_CMD="$CURL_CMD -F attachment=@$LOG_FILE"
[[ -f "$REPORT_HTML" ]] && CURL_CMD="$CURL_CMD -F attachment=@$REPORT_HTML"
[[ -f "$RERUN_REPORT_HTML" ]] && CURL_CMD="$CURL_CMD -F attachment=@$RERUN_REPORT_HTML"
[[ -f "$DOAJ_RESULTS" ]] && CURL_CMD="$CURL_CMD -F attachment=@$DOAJ_RESULTS"

eval "$CURL_CMD" < "$BODY_FILE" || {
    echo "Failed to send email via Mailgun" >&2
    exit 1
}

echo "Email sent to $EMAIL_TO"
exit 0
