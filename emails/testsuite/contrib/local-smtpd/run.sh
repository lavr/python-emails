#!/bin/sh
# Looks like python3 has a bug in smtpd (SMTPSenderRefused: (503, 'Error: send HELO first'...)
# So we try to start python2

PYTHON=python2.7
# next line doesn't works actually. TODO: fix it
(which python2.7 && export PYTHON=python2.7) || (which python2.6 && export PYTHON=python2.6) ||  export PYTHON=python
echo "$PYTHON run.py $@"
$PYTHON run.py $@
