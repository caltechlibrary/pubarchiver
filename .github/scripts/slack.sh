#!/bin/bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <ARTIFACT_DIR>" >&2
    exit 1
fi

ARTIFACT_DIR="$1"
REPORT_CSV="${ARTIFACT_DIR}/report.csv"

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

# Count skipped/failed articles
SKIPPED_COUNT=0
if [[ -f "$REPORT_CSV" ]]; then
    SKIPPED_COUNT=$(grep -c "missing," "$REPORT_CSV" || true)
fi

# Determine color based on failures
if [[ $SKIPPED_COUNT -gt 0 ]]; then
    COLOR="#ff0000"
    TITLE="Portico archiving completed with failures"
else
    COLOR="#00ff00"
    TITLE="Portico archiving completed successfully"
fi

TEXT="Run completed on $(date +%Y-%m-%d). Articles skipped: $SKIPPED_COUNT"

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
