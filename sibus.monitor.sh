#!/bin/sh

### BEGIN INIT INFO
# Provides:          myservice
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Put a short description of the service here
# Description:       Put a long description of the service here
### END INIT INFO

if [ -z "$ALPIBUS_DIR" ]; then
    echo "ERROR: set env var ALPIBUS_DIR first ! (add export ALPIBUS_DIR='' in your .bashrc file)"
    exit 1
fi

if [ ! -d "$ALPIBUS_DIR" ]; then
    echo "ERROR: ALPIBUS_DIR var is not a valid folder: $ALPIBUS_DIR"
    exit 1
fi


# Change the next 3 lines to suit where you install your script and what you want to call it
DIR=$ALPIBUS_DIR/bus.plugins/bus.monitor
DAEMON_NAME=bus.monitor.py
DAEMON=$DIR/$DAEMON_NAME

# Add any command line options for your daemon here
DAEMON_OPTS=""

# This next line determines what user the script runs as.
# Root generally not recommended but necessary if you are using the Raspberry Pi GPIO from Python.
DAEMON_USER=$USER

# The process ID of the script when it runs is stored here:
PIDFILE=$DIR/$DAEMON_NAME.pid

. /lib/lsb/init-functions

do_start () {
    log_daemon_msg "Starting system $DAEMON_NAME daemon"
    start-stop-daemon --start --background --pidfile $PIDFILE --make-pidfile --chdir $DIR --user $DAEMON_USER --chuid $DAEMON_USER --startas $DAEMON -- $DAEMON_OPTS
    log_end_msg $?
}
do_stop () {
    log_daemon_msg "Stopping system $DAEMON_NAME daemon"
    start-stop-daemon --stop --pidfile $PIDFILE --retry 10
    log_end_msg $?
}

case "$1" in

    start|stop)
        do_${1}
        ;;

    restart|reload|force-reload)
        do_stop
        do_start
        ;;

    status)
        status_of_proc -p $PIDFILE "$DAEMON" "$DAEMON_NAME" "system-wide $DAEMON_NAME" && exit 0 || exit $?
        ;;

    *)
        echo "Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart|status}"
        exit 1
        ;;

esac
exit 0
