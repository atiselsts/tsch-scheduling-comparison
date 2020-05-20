# What is this?

This is the source code behind the paper:

* *A. Elsts, S. Kim, H. Kim, C. Kim. An Empirical Survey of Autonomous Scheduling Methods for TSCH, IEEE Access, 2020.* https://doi.org/10.1109/ACCESS.2020.2980119

# Autonomous scheduling tests

The paper experimentally evaluate the ALICE and Orchestra schedulers.

Our experiments used the FIT IoT-LAB infrastructure.
Alternative simulation-only experiment setup is possible using Cooja motes
and either trace-based or randomly-generated simulation scripts.

## Quick start

The autonomous scheduling test applications are available under `examples/autonomous/`.

For a quick start, open one of the simulation files provided there in Cooja and run it.
The data packet generation starts after an 30 min warm-up period. Search for "seqnum=" in the logs to
see packets being received.

### Tweaking the setup

* Change the `FIRMWARE_TYPE` variable in the makefile to select a different protocol option to test.
* The file `common-conf.h` contains the configuration options common to all applications.

### Applications
There are three applications that simulate three traffic patters:

* `exp-collection` - data collection from nodes to root
* `exp-query` - data query, root to nodes and back to root
* `exp-local` - local traffic between parent and child nodes

## Automated testing infrastructure

The testing infrastructure, in form of both simulation generator and testbed executable generator,
is available under `examples/autonomous/testing`.

* `generate_firmwares.py` will generate source folders with different settings and a script called
`compile-all.sh` that can be used to build the firmwares for IoT-LAB
* `generate_sims.py` will generate simulation files and source folders with different settings and
a script called `run-all.sh` that can be used to run Cooja on all of the different settings.

You may need to change some paths before using the scripts!

## Implementation

The implementation of the different approaches can be found in:

* `os/services/orchestra`
* `os/services/alice`
* `os/net/mac/tsch` (some parts of it)

## Request for an acknowledgement

When using this source code, please cite the following paper:

* *A. Elsts, S. Kim, H. Kim, C. Kim. An Empirical Survey of Autonomous Scheduling Methods for TSCH, IEEE Access, 2020.* https://doi.org/10.1109/ACCESS.2020.2980119

This work is mostly based on the ALICE and Orchestra schedulers:

* *Seohyang Kim, Hyung-Sin Kim, and Chongkwon Kim, ALICE: Autonomous Link-based Cell Scheduling for TSCH, In the 18th ACM/IEEE International Conference on Information Processing in Sensor Networks (IPSN'19).*
* *Simon Duquennoy, Beshr Al Nahas, Olaf Landsiedel, and Thomas Watteyne, Orchestra: Robust Mesh Networks Through Autonomously Scheduled TSCH, ACM SenSys'15*
