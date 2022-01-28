#!/bin/bash
if [[ ($* == *--help*) || ($* == *-h*)]]
then
  echo "Usage: sh start_tango_servers.sh [OPTIONS...]
  Options and arguments (and corresponding environment variables):
  --virtual : use virtual detector
  --local   : run tango servers locally without connecting to real DB
  --verbose : use info_stream for tango servers"
else
  if [[ $* == *--verbose* ]]
  then
  VERBOSE_ARG="-v4"
  else
  VERBOSE_ARG=""
  fi

  if [[ $* == *--local* ]]
  then
  MESSAGE_1=">>>> Starting locally"
  NETWORK_ARG_CONTROL="-ORBendPoint giop:tcp:localhost:1234 -nodb -dlist moench/virtual/control"
  NETWORK_ARG_ACQUIRE="-ORBendPoint giop:tcp:localhost:1235 -nodb -dlist moench/virtual/acquire"
  MESSAGE_3=">>>> Started locally\nconnect via:\nc = Device(\"localhost:1234/moench/virtual/control#dbase=no\")\na = Device(\"localhost:1235/moench/virtual/acquire#dbase=no\")"
  else
  MESSAGE_1=">>>> Starting on network"
  NETWORK_ARG_CONTROL=""
  NETWORK_ARG_ACQUIRE=""
  MESSAGE_3=">>>> Started on network\n connect via jive"
  fi

  if [[ $* == *--virtual* ]]
  then
  MESSAGE_2=">>>> with a virtual detector..."
  VIRTUAL_ARG="--virtual"
  else
  MESSAGE_2=">>>> with a real detector..."
  VIRTUAL_ARG=""
  fi

  echo ${MESSAGE_1}
  echo ${MESSAGE_2}
  gnome-terminal -- /bin/sh -c "python3 moench_tango_control_server.py moench ${NETWORK_ARG_CONTROL} ${VERBOSE_ARG} ${VIRTUAL_ARG}; exec bash"
  sleep 10
  gnome-terminal -- /bin/sh -c "python3 moench_tango_acquire_server.py moench ${NETWORK_ARG_ACQUIRE} ${VERBOSE_ARG}; exec bash"
  echo -e ${MESSAGE_3}
fi
