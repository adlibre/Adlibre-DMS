#!/bin/bash
#
# Manages the startup and shutdown of this projects processes
# as well as running various tasks.
#
# Uses UNIX sockets for FCGI
#
# Version 2.5

# Project Specific
PROJNAME='adlibre_dms'

# Auto config based on standard project layout
CWD=$(cd ${0%/*} && pwd -P)
PROJDIR=$(cd $CWD/../ && pwd -P) # Root of our project
SRCDIR=$(cd $CWD/../${PROJNAME}/ && pwd -P) # Path to manage.py
BINDIR=$(cd $CWD/../bin/ && pwd -P) # Path to activate / virtualenv

# Source Config Overrides
if [ -f $SRCDIR/manage-fcgi.conf ]; then
    source $SRCDIR/manage-fcgi.conf
fi

# Config Defaults
WEB_USER=${WEB_USER-wwwpub}
METHOD=${METHOD-prefork} #threaded
MAXSPARE=${MAXSPARE-10}
MINSPARE=${MINSPARE-6}
MAXCHILDREN=${MAXCHILDREN-24}
MAXREQUESTS=${MAXREQUESTS-256}
UMASK=${UMASK-007} # Shouldn't need to change this

############################################

ACTION=$1
SETTINGS=${2-${SETTINGS-settings}} # If $2 not set, then use from config file, otherwise default to literal 'settings'
SOCKET="${PROJDIR}/${3-${SOCKET-$PROJNAME}}.sock"
PIDBASE="${PROJDIR}/${3-${PIDBASE-$PROJNAME}}"

WPIDFILE="${PIDBASE}.wsgi.pid"
CPIDFILE="${PIDBASE}.celeryd.pid"
CMD="python ${SRCDIR}/manage.py runfcgi method=${METHOD} minspare=${MINSPARE} maxspare=${MAXSPARE} maxchildren=${MAXCHILDREN} maxrequests=${MAXREQUESTS} socket=$SOCKET pidfile=${WPIDFILE} umask=${UMASK} --settings=${SETTINGS}"

# Functions
function startit {
    echo -n "Starting ${PROJNAME} with ${SETTINGS}: "

    if [ -f "${WPIDFILE}" ]; then
        echo "Error: PIDFILE ${WPIDFILE} exists. Already running?"
        RC=128
    else
        . ${BINDIR}/activate
	exec ${CMD}
        RC=$?
        echo "Started."
    fi
}

function stopit {
    echo -n "Stopping ${PROJNAME}: "

    if [ -f "${WPIDFILE}" ]; then
        kill `cat -- ${WPIDFILE}`
        RC=$?
        echo "Process(s) Terminated."
        rm -f -- ${WPIDFILE}
        rm -f -- ${SOCKET}
    else
        echo "PIDFILE not found. Killing likely processes."
        kill `pgrep -f "${CMD}"`
        RC=$?
        echo "Process(s) Terminated."
        rm -f -- ${SOCKET}
    fi
}

function status {
    echo "I don't know how to do that yet"
}

function startCelery {
    echo -n "Starting CeleryD ${PROJNAME} with ${SETTINGS}: "

    if [ -f "${CPIDFILE}" ]; then
        echo "Error: PIDFILE ${CPIDFILE} exists. Already running?"
        RC=128
    else
        . ${BINDIR}/activate
        python ${SRCDIR}/manage.py celeryd_detach --pidfile=${CPIDFILE} --settings=${SETTINGS}
        RC=$?
        echo "Started."
    fi
}

function stopCelery {
    echo -n "Stopping CeleryD ${PROJNAME}: "

    if [ -f "${CPIDFILE}" ]; then
        kill `cat -- ${CPIDFILE}`
        RC=$?
        echo "Process(s) Terminated."
        rm -f -- ${CPIDFILE}
    else
        echo "PIDFILE not found. Killing likely processes."
        kill `pgrep -f "python ${SRCDIR}/manage.py celeryd_detach pidfile=${CPIDFILE} --settings=${SETTINGS}"`
        RC=$?
        echo "Process(s) Terminated."
    fi
}

function rebuildIndex {
    echo -n "Rebuilding ${PROJNAME} search index with ${SETTINGS}: "
    . ${BINDIR}/activate
    python ${SRCDIR}/manage.py update_index --remove --settings=${SETTINGS}
    RC=$?
    echo "Done."
}

function showUsage {
    echo "Usage: manage-fcgi.sh {start|stop|restart|status|rebuildindex|startCelery|stopCelery|restartCelery} <settings_file> <sitename>"
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
    startCelery)
        startCelery
	;;
    stopCelery)
        stopCelery
	;;
	restartCelery)
	    stopCelery
	    startCelery
	;;
    status)
        status
        ;;
    rebuildindex)
        rebuildIndex
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
