#!/bin/bash
# Usage: run-summary.sh SERVICE ARTIFACT_DIR
#
# Prints EMAIL_TO, EMAIL_SUBJECT, and EMAIL_BODY_B64 lines for $GITHUB_ENV,
# describing a run of the PMC or Portico workflow: how many articles were
# selected and sent, and each article that was not sent, with the reason.
# Reads the counts the workflow put in the environment and these files in
# ARTIFACT_DIR: report.csv, not-sent.txt, and upload-failed.txt.

set -uo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 SERVICE ARTIFACT_DIR" >&2
    exit 1
fi
service="$1"
dir="$2"
report="$dir/report.csv"
today="${TODAY:-$(date +%Y-%m-%d)}"

reason() {
    local doi="$1" status
    if [[ -f "$dir/upload-failed.txt" ]] && grep -qxF "$doi" "$dir/upload-failed.txt"; then
        echo "upload failed"
        return
    fi
    status=$(grep -F ",$doi," "$report" 2>/dev/null | head -1 | cut -d, -f1)
    if [[ -n $status ]]; then
        echo "$status"
    else
        echo "not in the article list"
    fi
}

if [[ ${PUBARCHIVER_STATUS:-} != '0' ]]; then
    to="${EMAIL_FAILURE:-}"
    subject="$service upload failed on $today"
    body="Nothing was sent. pubarchiver exited with status ${PUBARCHIVER_STATUS:-unknown}"
    body+=" or could not get microPublication's article list; the run log has the details."
    body+=$'\n'"The articles will be selected again on the next run."
else
    sent="${SENT_COUNT:-0}"
    not_sent="${NOT_SENT_COUNT:-0}"
    body="Selected ${SELECTED_COUNT:-0} articles: those published after ${AFTER_DATE:-?}"
    body+=" (${PUBLISHED_COUNT:-0}, of which ${ALREADY_SENT_COUNT:-0} were already sent)"
    body+=" and ${RETRY_COUNT:-0} from earlier runs."
    body+=$'\n'"Sent: $sent."
    if [[ $not_sent != '0' ]]; then
        to="${EMAIL_FAILURE:-}"
        subject="$service upload: $sent sent, $not_sent not sent on $today"
        body+=$'\n\n'"Not sent: $not_sent. These will be tried again on the next run:"
        while read -r doi; do
            [[ -n $doi ]] && body+=$'\n'"  $doi  $(reason "$doi")"
        done < "$dir/not-sent.txt"
    else
        to="${EMAIL_SUCCESS:-}"
        subject="$service upload: $sent articles on $today"
    fi
    if [[ -s $report ]]; then
        body+=$'\n\n'"$(cat "$report")"
    fi
fi

echo "EMAIL_TO=$to"
echo "EMAIL_SUBJECT=$subject"
echo "EMAIL_BODY_B64=$(printf '%s\n' "$body" | base64 -w 0)"
