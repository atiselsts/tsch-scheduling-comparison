/* A simple log file generator script */

TIMEOUT(1860000); /* 1860 seconds or 30+ minutes */
//TIMEOUT(1000000); /* 1000 seconds or 15+ minutes */
//TIMEOUT(10000);

//plugin = mote.getSimulation().getCooja().getStartedPlugin("PowerTracker");
//if (plugin === null) {
//    log.log("No PowerTracker plugin\n");
//    log.testFailed();
//}

timeout_function = function () {
    log.log("Script timed out.\n");
    log.testOK();
}

/* after 600 seconds or 10 minutes (increase in the future?) */
GENERATE_MSG(600000, "initial phase complete");

while (true) {
    if (msg) {
        if(msg.equals("initial phase complete")) {
            /* all nodes should be joined by now; reset initial stats */
            //plugin.reset();
            GENERATE_MSG(300000, "next phase complete");
        } else if(msg.equals("next phase complete")) {
            /* print current stats and reset the plugin to prepare for the next period */
            //stats = plugin.radioStatistics();
            //plugin.reset();
            //log.log("RADIO STATS @ " + time + "\n" + stats + "\n");
            GENERATE_MSG(300000, "next phase complete");
        }
        log.log(time + " " + id + " " + msg + "\n");
    }

    YIELD();
}
