# pytango-moenchDetector

## Description

This device connects to MOENCH detector and allows to control the state of the detector.

## Getting Started

### Dependencies

* `pytango 9`
* `slsdet`
* `slsDetectorGroup binary executables`

## Start
### using the shell script
1. Start the both servers (control and acquire) via shell script:  
`sh start_tango_servers.sh [ |--help| --virtual [--verbose]]`
### manually
#### locally
Start server via command:
* `python moench_tango_server.py moench -ORBendPoint giop:tcp:localhost:1234 -nodb -dlist id1/tests/dev1`
and then connect from itango:
* `localhost:1234/id1/tests/dev1#dbase=no`

#### production

to be done...

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
