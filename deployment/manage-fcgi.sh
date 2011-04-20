#!/bin/bash
#
# Manages the startup and shutdown of this projects FCGI processes.
# Uses UNIX sockets
#

# Project Specific Config
PROJNAME='dms'
WEB_USER='wwwpub'

CWD=$(cd ${0%/*} && pwd -P)
PROJDIR=$(cd $CWD/../src/${PROJNAME}/ && pwd -P) # Root of our project source
BINDIR=$(cd $CWD/../bin/ && pwd -P) # Path to activate / virtualenv
PIDFILE="$PROJDIR/${PROJNAME}.pid"
SOCKET="$PROJDIR/${PROJNAME}.sock"

############################################

ACTION=$1
SETTINGS=$2

# Functions
function startit {
    if [ "SETTINGS" == "" ]; then
        echo -n"Starting ${PROJNAME}: "
        . ${BINDIR}/activate
        python ${PROJDIR}/manage.py runfcgi protocol=scgi socket=$SOCKET pidfile=$PIDFILE
        RC=$?
        echo "Started"
    else
        echo -n "Starting ${PROJNAME} with ${SETTINGS}: "
        . ${BINDIR}/activate
        python ${PROJDIR}/manage.py runfcgi protocol=scgi socket=$SOCKET pidfile=$PIDFILE --settings=${SETTINGS}
        RC=$?
        echo "Started"
    fi
}

function stopit {
    echo -n "Stopping ${PROJNAME}: "

    if [ -f $PIDFILE ]; then
        kill `cat -- $PIDFILE` &&
        rm -f -- $PIDFILE &&
        RC=$?
        echo "Process(s) Terminated."
    else
        echo "PIDFILE not found. Killing likely processes."
        kill `pgrep -f "python ${PROJDIR}/manage.py"`
        exit 128
    fi
}

function status {
    echo "I don't know how to do that yet"
}

function showUsage {
    echo "Usage: manage-fcgi.sh {start|stop|status|restart} <settings_file>"
}

# check that we have required parameters
if [ "$ACTION" == "" ]; then
    showUsage
    exit 128
fi

# Sanity check username = $WEB_USER else die with error
if [ ! "`whoami`" == "$WEB_USER" ]; then
    echo "Error: Must run as ${WEB_USER}."
    exit 128
fi

# See how we were called.
case "$ACTION" in
    start)
        startit
	;;
    stop)
        stopit
	;;
    status)
        status
        ;;
    restart)
        stopit
        startit
	;;
    *)
	    showUsage
	;;
esac

exit $RC
