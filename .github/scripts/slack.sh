#!/bin/bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <ARTIFACT_DIR>" >&2
    exit 1
fi

ARTIFACT_DIR="$1"
REPORT_CSV="${ARTIFACT_DIR}/report.csv"
RUN_NAME="${RUN_NAME:-}"
RUN_DATE="$(date +%Y-%m-%d)"
PUBARCHIVER_STATUS="${PUBARCHIVER_STATUS:-0}"
VALIDATION_ERRORS="${VALIDATION_ERRORS:-0}"
CURL_STATUS="${CURL_STATUS:-0}"

# Check if slack CLI is available
if ! command -v slack &>/dev/null; then
    echo "Slack CLI not found; skipping Slack notification"
    exit 0
fi

# Ensure we have a channel
if [[ -z "${SLACK_CHANNEL:-}" ]]; then
    echo "No Slack channel configured; skipping Slack notification" >&2
    exit 0
fi

# Determine overall status
if [[ $PUBARCHIVER_STATUS != '0' ]]; then
    COLOR="#ff0000"
    TITLE="${RUN_NAME} failed: pubarchiver exited with status ${PUBARCHIVER_STATUS}."
    TEXT="Check logs for details."
elif [[ $VALIDATION_ERRORS != '0' ]]; then
    COLOR="#ff0000"
    TITLE="${RUN_NAME} failed: ${VALIDATION_ERRORS} articles had validation/processing errors."
    TEXT="Run completed on ${RUN_DATE}. Articles skipped: ${VALIDATION_ERRORS}"
elif [[ $CURL_STATUS != '0' ]]; then
    COLOR="#ff0000"
    TITLE="${RUN_NAME} failed: FTP upload failed with status ${CURL_STATUS}."
    TEXT="Articles were not uploaded. Will retry on next run."
else
    COLOR="#00ff00"
    TITLE="${RUN_NAME} completed successfully."
    TEXT="Run completed on ${RUN_DATE}. Articles were uploaded successfully."
fi

slack chat send \
    --channel "$SLACK_CHANNEL" \
    --color "$COLOR" \
    --title "$TITLE" \
    --text "$TEXT" || {
    echo "Failed to post Slack message" >&2
    exit 1
}

echo "Slack message posted to $SLACK_CHANNEL"

# Upload files based on success/failure
LOG_FILE="${ARTIFACT_DIR}/run.log"

if [[ $PUBARCHIVER_STATUS != '0' ]] || [[ $VALIDATION_ERRORS != '0' ]] || [[ $CURL_STATUS != '0' ]]; then
    # On failure, upload the log file
    if [[ -f "$LOG_FILE" ]]; then
        slack file upload --channels "$SLACK_CHANNEL" --file "$LOG_FILE" \
            --comment "Here is the run log:" || {
            echo "Failed to upload log file to Slack" >&2
        }
    fi
else
    # On success, upload the report
    if [[ -f "$REPORT_CSV" ]]; then
        slack file upload --channels "$SLACK_CHANNEL" --file "$REPORT_CSV" \
            --comment "Here is the record of what was uploaded:" || {
            echo "Failed to upload report to Slack" >&2
        }
    fi
fi

exit 0
