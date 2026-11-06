#!/bin/bash
# Usage: select-articles.sh STATE_DIR AFTER_DATE OUTPUT_FILE
#
# Writes to OUTPUT_FILE the DOIs of the articles a run should send: those
# published after AFTER_DATE, plus those in STATE_DIR/last-failures, less
# those in STATE_DIR/sent.  With RESEND=true, articles already sent are not
# left out.  Prints counts as NAME=value lines for $GITHUB_ENV.
#
# If the article list can't be read, this exits with an error rather than
# selecting nothing, because the run would otherwise advance its date past
# articles it never saw.

set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "Usage: $0 STATE_DIR AFTER_DATE OUTPUT_FILE" >&2
    exit 1
fi
state_dir="$1"
after_date="$2"
output="$3"
work=$(mktemp -d)

mkdir -p "$state_dir"
touch "$state_dir/sent" "$state_dir/last-failures"

if ! pubarchiver -j micropublication -C -q -l -a "$after_date" > "$work/list"; then
    echo "Could not get the article list from microPublication" >&2
    exit 1
fi
{ grep '^10\.' "$work/list" || true; } | sort -u > "$work/published"
{ grep '^10\.' "$state_dir/last-failures" || true; } | sort -u > "$work/retry"
sort -u "$state_dir/sent" > "$work/sent"

sort -u "$work/published" "$work/retry" > "$work/all"
if [[ ${RESEND:-false} == 'true' ]]; then
    cp "$work/all" "$output"
else
    comm -23 "$work/all" "$work/sent" > "$output"
fi

echo "PUBLISHED_COUNT=$(wc -l < "$work/published" | tr -d ' ')"
echo "RETRY_COUNT=$(comm -12 "$output" "$work/retry" | wc -l | tr -d ' ')"
echo "ALREADY_SENT_COUNT=$(comm -12 "$work/all" "$work/sent" | wc -l | tr -d ' ')"
echo "SELECTED_COUNT=$(wc -l < "$output" | tr -d ' ')"
rm -rf "$work"
