# pytango-moenchDetector

## Description

This device connects to MOENCH detector and allows to control the state of the detector.

## Getting Started

### Dependencies

* `pytango 9`
* `slsdet`
* `slsDetectorGroup binary executables`

## Start
Please note:
* a server starts with a virtual detector, when the `IS_VIRTUAL_DETECTOR` boolean property of `MoenchDetectorControl` tango device has been assigned to `True`. Otherwise a real detector must be turned on.

### using tango-starter (the most preferable way)
1. Choose a `moench` starter from `astor` dropdown menu.
2. Start the `MoenchDetectorControl` server and the `MoenchAcquireControl` in a common way.
### using the shell script
1. Start the both servers (control and acquire) via shell script:  
```text
sh start_tango_servers.sh [OPTIONS...]

Options and arguments (and corresponding environment variables):
  --virtual : use virtual detector
  --local   : run tango servers locally without connecting to real DB
  --verbose : use info_stream for tango servers
```  
### manually
#### locally
Start servers via command:
* `python3 moench_tango_server.py moench -ORBendPoint giop:tcp:localhost:1234 -nodb -dlist id1/tests/dev1 [-v4]`
* `python3 moench_acquire_server.py moench -ORBendPoint giop:tcp:localhost:1235 -nodb -dlist id1/tests/dev2 [-v4]`

and then connect from Jive/iTango:
* `localhost:1234/id1/tests/dev1#dbase=no`
* `localhost:1235/id1/tests/dev2#dbase=no`

#### production
Start servers via command:
* `python3 moench_tango_server.py moench [-v4]`
* `python3 moench_acquire_server.py moench [-v4]`

and then connect from Jive/iTango:
* `rsxs/moenchControl/bchip286`
* `rsxs/moenchAcquire/bchip286`


## Help

Any additional information according to slsDetector, its python API or pytango references can be found under the links:

* [slsDetectorGroup wiki](https://slsdetectorgroup.github.io/devdoc/pydetector.html)
* [pytango reference](https://pytango.readthedocs.io/en/stable/)

## Authors

Contributors names and contact info

[@lrlunin](https://github.com/lrlunin)

[@dschick](https://github.com/dschick)
## Version History


## License

This project is licensed under the MIT License - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* Martin Borchert
* Daniel Schick
* Bastian Pfau
* rest of MBI crew 
