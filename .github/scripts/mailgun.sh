#!/bin/bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <ARTIFACT_DIR>" >&2
    exit 1
fi

ARTIFACT_DIR="$1"
REPORT_CSV="${ARTIFACT_DIR}/report.csv"
REPORT_HTML="${ARTIFACT_DIR}/report.html"
RERUN_REPORT_HTML="${ARTIFACT_DIR}/rerun-report.html"
LOG_FILE="${ARTIFACT_DIR}/run.log"
RUN_NAME="${RUN_NAME:-}"
RUN_DATE="$(date +%Y-%m-%d)"
PUBARCHIVER_STATUS="${PUBARCHIVER_STATUS:-0}"
VALIDATION_ERRORS="${VALIDATION_ERRORS:-0}"
CURL_STATUS="${CURL_STATUS:-0}"

# Determine subject and recipient based on failures
if [[ $PUBARCHIVER_STATUS != '0' ]] || [[ $VALIDATION_ERRORS != '0' ]] || [[ $CURL_STATUS != '0' ]]; then
    EMAIL_TO="${EMAIL_FAILURE:-}"
    if [[ $PUBARCHIVER_STATUS != '0' ]]; then
        SUBJECT="${RUN_NAME} failed: pubarchiver error"
    elif [[ $VALIDATION_ERRORS != '0' ]]; then
        SUBJECT="${RUN_NAME} failed: ${VALIDATION_ERRORS} articles with validation errors"
    else
        SUBJECT="${RUN_NAME} failed: FTP upload error"
    fi
else
    EMAIL_TO="${EMAIL_SUCCESS:-}"
    SUBJECT="${RUN_NAME} results for ${RUN_DATE}"
fi

# Ensure we have an email address
if [[ -z "$EMAIL_TO" ]]; then
    echo "No email recipient configured; skipping email" >&2
    exit 0
fi

# Build curl command with attachments
CURL_CMD="curl -s --user \"api:${MAILGUN_API_KEY}\" \
  https://api.mailgun.net/v3/${MAILGUN_DOMAIN}/messages \
  -F from='GitHub Actions <mailgun@${MAILGUN_DOMAIN}>' \
  -F to=\"$EMAIL_TO\" \
  -F subject=\"$SUBJECT\""

# Add text body
CURL_CMD="$CURL_CMD -F text='${RUN_NAME} completed. See attached reports and logs.'"

# Add attachments if they exist
[[ -f "$LOG_FILE" ]] && CURL_CMD="$CURL_CMD -F attachment=@$LOG_FILE"
[[ -f "$REPORT_CSV" ]] && CURL_CMD="$CURL_CMD -F attachment=@$REPORT_CSV"
[[ -f "$REPORT_HTML" ]] && CURL_CMD="$CURL_CMD -F attachment=@$REPORT_HTML"
[[ -f "$RERUN_REPORT_HTML" ]] && CURL_CMD="$CURL_CMD -F attachment=@$RERUN_REPORT_HTML"

eval "$CURL_CMD" || {
    echo "Failed to send email via Mailgun" >&2
    exit 1
}

echo "Email sent to $EMAIL_TO"
exit 0
