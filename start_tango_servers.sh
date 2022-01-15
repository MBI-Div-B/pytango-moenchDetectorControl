#!/bin/bash
if [[ ($* == *--help*) || ($* == *-h*)]]
then
  echo "usage: start_tango_servers.sh [flags]
  Options and arguments (and corresponding environment variables):
  --virtual : use local tango servers started on localhost"
else
  if [[ $* == *--virtual* ]]
  then
    python3 moench_tango_control_server.py moench -ORBendPoint giop:tcp:localhost:1234 -nodb -dlist moench/virtual/control --virtual && python3 moench_tango_acquire_server.py moench -ORBendPoint giop:tcp:localhost:1235 -nodb -dlist moench/virtual/acquire && echo ">>>> Virtual MOENCH tango server enviroment started"
  else
  #TODO: need to be configured with proper ip adresses and device names from the tango-DB
  #python3 moench_tango_control_server.py moench -ORBendPoint giop:tcp:localhost:1234 -nodb -dlist moench/virtual/control && python3 moench_tango_acquire_server.py moench -ORBendPoint giop:tcp:localhost:1235 -nodb -dlist moench/virtual/acquire
  echo ">>>> Real MOENCH tango server enviroment started"
  fi
fi