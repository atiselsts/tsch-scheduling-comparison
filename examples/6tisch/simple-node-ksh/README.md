How to change the used TSCH scheduler ?
Here, three TSCH schedulers are provided.
1) Orchestra
2) MC-Orchestra (Using multiple channel offsets in the unicast slotframe is supported)
3) ALICE

To change the used TSCH scheduler, you should change the following two parameters:

Makefile/MAKE_WITH_TSCH_SCHEDULER
project-conf.h/CURRENT_TSCH_SCHEDULER

Default value is 3 (ALICE).
If you change the number to 1 or 2, the used TSCH scheduler changes to Orchestra or MC-Orchestra, respectively.

You don't have to change other variables.

* Remember! DO NOT insert any space after the number in the line including Makefile/MAKE_WITH_TSCH_SCHEDULER !


==========================================================================

A RPL+TSCH node. Will act as basic node by default, but can be configured at startup
using the user button and following instructions from the log output. Every press
of a button toggles the mode as 6ln, 6dr or 6dr-sec (detailled next). After 10s with
no button press, the node starts in the last setting. The modes are:
* 6ln (default): 6lowpan node, will join a RPL+TSCH network and act as router.
* 6dr: 6lowpan DAG Root, will start its own RPL+TSCH network. Note this is not a
border router, i.e. it does not have a serial interface with connection to
the Internet. For a border router, see ../border-router.
* 6dr-sec: 6lowpan DAG Root, starting a RPL+TSCH network with link-layer security
enabled. 6ln nodes are able to join both non-secured or secured networks.  
