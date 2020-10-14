#!/bin/bash

export PORTICO_OUTPUT=/raid/micropublication/portico
export PORTICO_USER=foo
export PORTICO_PASS=foo
export EMAIL_SUCCESS="mhucka@library.caltech.edu"
export EMAIL_FAILURE="mhucka@library.caltech.edu"

export SLACK_CHANNEL=mikestestingchannel
export SLACK_CLI_TOKEN=foo

bash -x ./archive-in-portico
