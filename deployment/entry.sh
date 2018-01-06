#!/usr/bin/env bash
#
# Entrypoint script for django image.

function wait_couch {
    # LICENSE: MIT License, Copyright (c) 2017 Volt Grid Pty Ltd
    # Wait for Redis to be available
    local host=${1:-'localhost'}
    local port=${2:-'5984'}
    local timeout=${3:-30}
    echo -n "Connecting to CouchDB at ${host}:${port}..."
    for (( i=0;; i++ )); do
        if [ ${i} -eq ${timeout} ]; then
            echo " timeout!"
            exit 99
        fi
        sleep 1
        (exec 3<>/dev/tcp/${host}/${port}) &>/dev/null && break
        echo -n "."
    done
    echo " connected."
    exec 3>&-
    exec 3<&-
}

exec_procfile() {
    # LICENSE: MIT License, Copyright (c) 2017 Volt Grid Pty Ltd
    # Exec Procfile command
    local procfile=${1:-'Procfile'}
    if [ ! -e "$procfile" ]; then return 0; fi
    while read line || [[ -n "$line" ]]; do
        if [[ -z "$line" ]] || [[ "$line" == \#* ]]; then continue; fi
        if [[ "${2}" == "${line%%:*}" ]]; then
            echo "Executing ${2} from ${1}..."
            eval exec "${line#*:[[:space:]]}"
        fi
    done < "$procfile"
}

run_deployfile() {
    # LICENSE: MIT License, Copyright (c) 2017 Volt Grid Pty Ltd
    # Run all Deployfile commands
    local deployfile=${1:-'Deployfile'}
    if [ ! -e "$deployfile" ]; then return 0; fi
    while read line || [[ -n "$line" ]]; do
        if [[ -z "$line" ]] || [[ "$line" == \#* ]]; then continue; fi
        (>&2 echo "Running task ${line%%:*}: ${line#*:[[:space:]]}")
        eval "${line#*:[[:space:]]}"
        rc=$?
        [ "$rc" != 0 ] && exit $rc
    done < "$deployfile"
}

if [ -z "$CI" ]; then
    echo "Waiting for attached services..."
    wait_couch $COUCHDB_HOST $COUCHDB_PORT
fi

# Exec Procfile or run Deploy commands, or if not found then exec command passed
run_deployfile deployment/Deployfile
exec_procfile deployment/Procfile $1
exec "$@"
