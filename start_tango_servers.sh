#!/bin/bash
if [[ ($* == *--help*) || ($* == *-h*)]]
then
  echo "usage: start_tango_servers.sh [flags]
  Options and arguments (and corresponding environment variables):
  --virtual : use local tango servers started on localhost
  --verbose : use info_stream for tango servers"
else
  if [[ $* == *--verbose* ]]
  then
  VERBOSE_ARG="-v4 "
  else
  VERBOSE_ARG=""
  fi
  if [[ $* == *--virtual* ]]
  then
    echo ">>>> Starting virtual"
    gnome-terminal -- /bin/sh -c "python3 moench_tango_control_server.py moench -ORBendPoint giop:tcp:localhost:1234 -nodb -dlist moench/virtual/control ${VERBOSE_ARG}--virtual"
    sleep 10
    gnome-terminal -- /bin/sh -c "python3 moench_tango_acquire_server.py moench -ORBendPoint giop:tcp:localhost:1235 -nodb -dlist moench/virtual/acquire ${VERBOSE_ARG}"
    echo ">>>> Virtual MOENCH tango server enviroment started"
    echo "connect via:"
    echo "c = Device(\"localhost:1234/moench/virtual/control#dbase=no\")"
    echo "a = Device(\"localhost:1235/moench/virtual/acquire#dbase=no\")"
  else
  echo ">>>> Starting real"
  #TODO: need to be configured with proper ip adresses and device names from the tango-DB
  #python3 moench_tango_control_server.py moench -ORBendPoint giop:tcp:localhost:1234 -nodb -dlist moench/virtual/control && python3 moench_tango_acquire_server.py moench -ORBendPoint giop:tcp:localhost:1235 -nodb -dlist moench/virtual/acquire
  echo ">>>> Real MOENCH tango server enviroment started"
  fi
fi
