#!/bin/sh
# Looks like python3 has a bug in smtpd (SMTPSenderRefused: (503, 'Error: send HELO first'...)
# So we try to start python2

if which python2.7; then
    PYTHON=python2.7
elif which python2.6; then
    PYTHON=python2.6
else
    PYTHON=python
fi

echo "use python $PYTHON"
$PYTHON run-smtpd.py $@
