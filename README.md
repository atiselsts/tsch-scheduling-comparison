# ALICE on Contiki-NG

# Autonomous schedluing tests

The autonmous scheduling test application is available under `examples/autonomous/`.

There are three applications that simulate three traffic patters:

* `exp-collection` - data collection from nodes to root
* `exp-query` - data query, root to nodes and back to root
* `exp-local` - local traffic between parent and child nodes

The testing infrastructure, in form of both simulation generator and testbed executable generator,
is available under `examples/autonomous/testing`.

The experiments compare different options of the ALICE and Orchestra schedulers.
Change the `FIRMWARE_TYPE` variable in the makefile to select a different protocol option to test.

When using this source code, please cite the following paper:

*/To be done/*.
