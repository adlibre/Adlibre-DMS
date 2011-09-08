#!/bin/bash
#
# Manages the startup and shutdown of this projects FCGI processes
# as well as rebuilding the search index.
#
# Uses UNIX sockets for FCGI
#

# Project Specific Config
PROJNAME='dms'
WEB_USER='wwwpub'

CWD=$(cd ${0%/*} && pwd -P)
PROJDIR=$(cd $CWD/../ && pwd -P) # Root of our project
SRCDIR=$(cd $CWD/../src/${PROJNAME}/ && pwd -P) # Path to manage.py
BINDIR=$(cd $CWD/../bin/ && pwd -P) # Path to activate / virtualenv

############################################

ACTION=$1
SETTINGS=${2-settings}
SOCKET="$PROJDIR/"${3-$(echo "${PROJNAME}")}".sock"
PIDFILE="$PROJDIR/"${3-$(echo "${PROJNAME}")}".pid"

# Functions
function startit {
    echo -n "Starting ${PROJNAME} with ${SETTINGS}: "

    if [ -f "${PIDFILE}" ]; then
        echo "Error: PIDFILE ${PIDFILE} exists. Already running?"
        RC=128
    else
        . ${BINDIR}/activate
        python ${SRCDIR}/manage.py runfcgi socket=$SOCKET pidfile=$PIDFILE --settings=${SETTINGS}
        RC=$?
        echo "Started."
    fi
}

function stopit {
    echo -n "Stopping ${PROJNAME}: "

    if [ -f $PIDFILE ]; then
        kill `cat -- $PIDFILE`
        RC=$?
        echo "Process(s) Terminated."
        rm -f -- $PIDFILE
    else
        echo "PIDFILE not found. Killing likely processes."
        kill `pgrep -f "python ${SRCDIR}/manage.py runfcgi socket=$SOCKET pidfile=$PIDFILE --settings=${SETTINGS}"`
        RC=$?
        echo "Process(s) Terminated."
    fi
}

function status {
    echo "I don't know how to do that yet"
}

function rebuildindex {
    echo -n "Rebuilding ${PROJNAME} search index with ${SETTINGS}: "
    . ${BINDIR}/activate
    python ${SRCDIR}/manage.py update_index --remove --settings=${SETTINGS}
    RC=$?
    echo "Done."
}

function showUsage {
    echo "Usage: manage-fcgi.sh {start|stop|status|rebuildindex|restart} <settings_file>"
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
    rebuildindex)
        rebuildindex
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
