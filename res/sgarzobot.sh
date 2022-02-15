#!/bin/bash
### BEGIN INIT INFO
# Provides:          sgarzobot
# Required-Start:    $local_fs $network $named $time $syslog
# Required-Stop:     $local_fs $network $named $time $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Servizio SGARZOBOT
# Description:       Servizio SGARZOBOT
### END INIT INFO
command_start="cd /home/pi/sgarzoBot && python3 bot.py 1>/dev/null 2>/dev/null &"
command_kill="ps -aux | grep bot.py | grep python | awk \'{print \$2}\' | xargs sudo kill -9 1>/dev/null 2>/dev/null"
ret_check=`ps -aux | grep bot.py | grep python`
case "$1" in
	check)
		if [ "$ret_check" != "" ]
			then
				echo "Attivo"
			else
				echo "Spento"
		fi
	;;
	start)
		if [ "$ret_check" != "" ]
			then
				echo "Servizio SGARZOBOT attivo"
			else
				eval $command_start
				echo "Avviato servizio SGARZOBOT"
		fi
	;;
	stop)
		if [ "$ret_check" != "" ]
			then
				eval $command_kill
				echo "Stoppato servizio SGARZOBOT"
			else
				echo "Servizio SGARZOBOT non attivo"
		fi
	;;
	restart)
		if [ "$ret_check" != "" ]
			then
				eval $command_kill
				eval $command_start
				echo "Restart servizio SGARZOBOT"
			else
				eval $command_start
				echo "Avviato servizio SGARZOBOT"
		fi
	;;
	*)
		echo "Usage: $0 {check|start|stop|restart}"
        exit 2
	;;
esac
exit 0