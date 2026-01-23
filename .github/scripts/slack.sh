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
    TITLE="${RUN_NAME} failed: FTP upload to PMC failed with status ${CURL_STATUS}."
    TEXT="Archives were not uploaded. Will retry on next run."
else
    COLOR="#00ff00"
    TITLE="${RUN_NAME} completed successfully."
    TEXT="Run completed on ${RUN_DATE}. Archives uploaded to PMC."
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
exit 0
