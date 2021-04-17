#!/bin/bash
# =============================================================================
# @file    helpers
# @brief   Common shell functions used across multiple workflows
# @author  Michael Hucka <mhucka@caltech.edu>
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/microarchiver
#
# The code below assumes the following variables are set by the calling code:
#
# * $log -- the file where a run-time log of actions is written
# * $today -- a string giving today's date
# * $mainscript -- the path to the main workflow script calling these helpers
# * $outputdir -- directory where files from the day's run are written
#
# The code below assumes the existence of the following environment variables:
#
# * EMAIL_FAILURE: email address(es) to send notifications of failures
# * SLACK_CHANNEL: Slack channel to send notifications of failure or success
# * SLACK_CLI_TOKEN: used by slack-cli for the Slack API token
#
# The code below also assumes that programs "microarchiver" and "slack" (the
# latter from https://github.com/rockymadden/slack-cli) are on the calling
# user's command search $path.
# =============================================================================

run_microarchiver() {
    # We have only two cases, Portico and PMC, so this grungy approach is good
    # enough for now.  Future revisions should generalize this, though.
    destination=Portico
    shopt -s nocasematch
    for i in "$@" ; do
        if [[ "$i" == "pmc" ]] ; then
            destination=PMC
            break
        fi
    done
    shopt -u nocasematch

    # Next, make sure we can find microarchiver. If not, send mail & quit.
    if ! command -v microarchiver &> /dev/null; then
        body=$(cat <<EOF
This is an error message generated by the process running microarchiver for
uploading publications to $destination. The process is unable to find the
program "microarchiver". This indicates either a configuration problem or
a change in the computer system where the process is executed. Manual
intervention is required. Additional information may be found here:

  computer: `hostname`
  directory: $outputdir

This message was produced by $mainscript on `hostname`.
EOF
)
        echo "$body" | mail -s"microarchiver failure $today" $EMAIL_FAILURE
        run_slack chat send --channel $SLACK_CHANNEL --color "#ff0000" \
              --title "Error: unable to upload micropublication.org to $destination" \
              --text "$mainscript on `hostname` cannot find program 'microarchiver'"
        exit 1
    fi

    # Run microarchiver with arguments and save output in $log
    count=$(microarchiver $@ 2>&1 | tee -a $log | grep "Total articles" | cut -d ' ' -f3)

    # If successful, return the num. of articles written, else send mail & quit
    status=$?
    if (($status == 0)); then
        echo $count
    else
        case "$status" in
            1) cause="No network detected" ;;
            2) cause="The user interrupted program execution" ;;
            3) cause="An exception or fatal error occurred during execution" ;;
            *) cause="An unexpected error occurred during execution" ;;
        esac
        body=$(cat <<EOF
This is an error message generated by the process running microarchiver for
uploading publications to $destination. While doing its work, microarchiver has
encountered the following error:

   $cause

The attached log file may indicate a reason for the failure. Look at the
bottom the log file to see what was the last action attempted.

Today's upload to $destination has been stopped.
EOF
)
        echo "$body" | mail -s"microarchiver failure $today" -a $log $EMAIL_FAILURE
        run_slack chat send --channel $SLACK_CHANNEL --color "#ff0000" \
              --title "Error: unable to complete $destination archiving for micropublication.org" \
              --text "microarchiver failed to create archive file for $destination. Cause: $cause."
        run_slack file upload --channels $SLACK_CHANNEL --file $log \
              --comment "Here is the microarchiver run log:"
        exit $status
    fi
}

run_slack() {
    # First make sure we can find slack. If not, log it and return silently.
    if ! command -v slack &> /dev/null; then
        echo "Unable to find slack" >> $log
        return
    fi

    # Run slack-cli with arguments. Send its output to /dev/null because it
    # always returns a JSON blob (no way to turn it off) and the resulting
    # output will cause cron to think it should be mailed to the user.
    slack "$@" > /dev/null 2>&1
}

run_curl() {
    # FIXME: this is a hack, made possible by the fact that we currently only
    # upload to PMC.  If ever we upload to more destinations, this needs to
    # be fixed to determine the destination from the arguments.
    destination=PMC

    # First, make sure we can find curl. If not, send mail & quit.
    if ! command -v curl &> /dev/null; then
        body=$(cat <<EOF
This is an error message generated by the process running microarchiver for
uploading publications to $destination. The process is unable to find the
program "curl". This indicates either a configuration problem or a
change in the computer system where the process is executed. Manual
intervention is required. Additional information may be found here:

  computer: `hostname`
  directory: $outputdir

This message was produced by $mainscript on `hostname`.
EOF
)
        echo "$body" | mail -s"PMC upload process failure $today" $EMAIL_FAILURE
        run_slack chat send --channel $SLACK_CHANNEL --color "#ff0000" \
              --title "Error: unable to upload micropublication.org to $destination" \
              --text "$mainscript on `hostname` cannot find program 'curl'"
        exit 1
    fi

    # Run curl.

    curl -w '%{response_code}' $@ >> $log 2>&1
    status=$?
    if (($status > 0)); then
        # The 2nd-to-last line will have a message from curl.
        problem=$(tail -n 2 $log | head -n 1)
        body=$(cat <<EOF
This is an error message generated by the process running microarchiver for
uploading publications to $destination. The "curl" command used to upload files to
$destination failed with the following return status:

  $problem

The attached log file may indicate a reason for the failure. Look at the
bottom the log file to see what was the last action attempted.

Today's upload to $destination has been stopped.
EOF
)
        echo "$body" | mail -s"PMC upload failure $today" -a $log $EMAIL_FAILURE
        run_slack chat send --channel $SLACK_CHANNEL --color "#ff0000" \
              --title "Error: unable to complete PMC upload for micropublication.org" \
              --text "$mainscript unable to ftp to $destination. Cause: $problem."
        run_slack file upload --channels $SLACK_CHANNEL --file $log \
              --comment "Here is the microarchiver run log:"
        exit $status
    fi
}
