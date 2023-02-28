# pytango-moenchDetectorControl
![conda version](https://anaconda.org/mbi-div-b/tangods_moenchcontrol/badges/version.svg)
![last updated](https://anaconda.org/mbi-div-b/tangods_moenchcontrol/badges/latest_release_date.svg
)
![platforms](https://anaconda.org/mbi-div-b/tangods_moenchcontrol/badges/platforms.svg
)

## Description

This device connects to MOENCH detector and allows to control the state of the detector.

## Installation
This package is distributed via conda. There are necessary steps before installation:
1. `conda create -n tangods_env python=3.10`
2. `conda activate tangods_env`
3. `conda config --add channels conda-forge`
4. `conda config --add channels slsdetectorgroup`
5. `conda config --set channel_priority strict`

The package is in the mbi-div-b repository. Use the following command for installation:

`conda install -c mbi-div-b tangods_moenchcontrol`

## Start
Please note:
* The server starts with a virtual detector, when the `IS_VIRTUAL_DETECTOR` boolean property of `MoenchDetectorControl` tango device has been assigned to `True`. Otherwise a real detector must be turned on. **Please note that the virtual detector server is not distributed in conda and needs to be compiled manually.**
* As the `slsReceiver` executable must be run with sudo rights, the active user must have sudo rights. It is also necessary to provide the password for this user in the device tango property `ROOT_PASSWORD`. 

### manually
Start servers via commands sequence:
1. Activate the environment with installed package with: `conda activate tangods_env`.
2. Run the server with: `MoenchDetectorControl INSTANCE_NAME [-v4]`

You can also give a full path to the executable:

`./home/username/miniconda3/envs/tangods_env/bin/MoenchDetectorControl INSTANCE_NAME [-v4]`
### with Astor
There two necessary steps:
1. Add the following line into `StartDsPath` property of `Starter` tango DS: `/home/username/miniconda3/envs/tangods_env/bin`
2. Start the server from `Astor` window

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
