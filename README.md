# ALICE on Contiki-NG

ALICE supports both Contiki and Contiki-NG !
In this version (Contiki-NG), ALICE runs even in the Cooja simulator.

ALICE example code location: ./examples/6tisch/simple-node-ksh/

ALICE source code location: ./os/services/alice/


# ALICE

ALICE is an autonomous link-based TSCH cell scheduling solution. ALICE uses Contiki Orchestra code as its skeleton code. ALICE uses three slotframes (EB, broadcast/default and unicast) as Orchestra does. The main difference is unicast slotframe schedule which implements time-varying scheduling and link-based scheduling.

ALICE source code location: ./os/services/alice/ and ./core/net/mac/tsch/ 

ALICE example code location: ./examples/6tisch/simple-node-ksh

When using this source code, please cite the following paper:

Seohyang Kim, Hyung-Sin Kim, and Chongkwon Kim, ALICE: Autonomous Link-based Cell Scheduling for TSCH, In the 18th ACM/IEEE International Conference on Information Processing in Sensor Networks (IPSN'19), April 16-18, 2019, Montreal, Canada.









# Contiki-NG: The OS for Next Generation IoT Devices

<img src="https://github.com/contiki-ng/contiki-ng.github.io/blob/master/images/logo/Contiki_logo_2RGB.png" alt="Logo" width="256">

# Contiki-NG: The OS for Next Generation IoT Devices

[![Build Status](https://travis-ci.org/contiki-ng/contiki-ng.svg?branch=master)](https://travis-ci.org/contiki-ng/contiki-ng/branches)
[![license](https://img.shields.io/badge/license-3--clause%20bsd-brightgreen.svg)](https://github.com/contiki-ng/contiki-ng/blob/master/LICENSE.md)
[![Latest release](https://img.shields.io/github/release/contiki-ng/contiki-ng.svg)](https://github.com/contiki-ng/contiki-ng/releases/latest)
[![GitHub Release Date](https://img.shields.io/github/release-date/contiki-ng/contiki-ng.svg)](https://github.com/contiki-ng/contiki-ng/releases/latest)
[![Last commit](https://img.shields.io/github/last-commit/contiki-ng/contiki-ng.svg)](https://github.com/contiki-ng/contiki-ng/commit/HEAD)

Contiki-NG is an open-source, cross-platform operating system for Next-Generation IoT devices. It focuses on dependable (secure and reliable) low-power communication and standard protocols, such as IPv6/6LoWPAN, 6TiSCH, RPL, and CoAP. Contiki-NG comes with extensive documentation, tutorials, a roadmap, release cycle, and well-defined development flow for smooth integration of community contributions.

Unless explicitly stated otherwise, Contiki-NG sources are distributed under
the terms of the [3-clause BSD license](LICENSE.md). This license gives
everyone the right to use and distribute the code, either in binary or
source code format, as long as the copyright license is retained in
the source code.

Contiki-NG started as a fork of the Contiki OS and retains some of its original features.

Find out more:

* GitHub repository: https://github.com/contiki-ng/contiki-ng
* Documentation: https://github.com/contiki-ng/contiki-ng/wiki
* Web site: http://contiki-ng.org

Engage with the community:

* Gitter: https://gitter.im/contiki-ng
* Twitter: https://twitter.com/contiki_ng
