#!/bin/bash
# Usage: record-state.sh STATE_DIR SELECTED_FILE SENT_FILE TODAY
#
# Records the outcome of a run in STATE_DIR: the DOIs in SENT_FILE are added
# to STATE_DIR/sent, every selected DOI that is not now in STATE_DIR/sent
# becomes STATE_DIR/last-failures for the next run to try again, and TODAY
# becomes STATE_DIR/last-run-date.

set -euo pipefail

if [[ $# -ne 4 ]]; then
    echo "Usage: $0 STATE_DIR SELECTED_FILE SENT_FILE TODAY" >&2
    exit 1
fi
state_dir="$1"
selected="$2"
sent_now="$3"
today="$4"
work=$(mktemp -d)

mkdir -p "$state_dir"
touch "$state_dir/sent" "$selected" "$sent_now"

sort -u "$state_dir/sent" "$sent_now" > "$work/sent"
sort -u "$selected" > "$work/selected"
comm -23 "$work/selected" "$work/sent" > "$state_dir/last-failures"
mv "$work/sent" "$state_dir/sent"
echo "$today" > "$state_dir/last-run-date"
echo "Sent so far: $(wc -l < "$state_dir/sent" | tr -d ' '). To retry next run: $(wc -l < "$state_dir/last-failures" | tr -d ' ')."
rm -rf "$work"
