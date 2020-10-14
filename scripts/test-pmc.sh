#!/bin/bash

export PMC_OUTPUT=/raid/micropublication/pmc
export PMC_USER=foo
export PMC_PASS=foo
export EMAIL_SUCCESS="mhucka@library.caltech.edu"
export EMAIL_FAILURE="mhucka@library.caltech.edu"

export SLACK_CHANNEL=mikestestingchannel
export SLACK_CLI_TOKEN=foo

bash -x ./archive-in-pmc
