/* A simple log file generator script */

TIMEOUT(660000); /* 660 seconds or 11 minutes */

plugin = mote.getSimulation().getCooja().getStartedPlugin("PowerTracker");
if (plugin === null) {
  log.log("No PowerTracker plugin\n");
  log.testFailed();
}

timeout_function = function () {
    log.log("Script timed out.\n");
    log.testOK();
}

/* after 300 seconds or 5 minutes (increase in the future?) */
GENERATE_MSG(300000, "initial phase complete");

while (true) {
    if (msg) {
        if(msg.equals("initial phase complete")) {
            /* all nodes should be joined by now; reset initial stats */
            plugin.reset();
            GENERATE_MSG(300000, "next phase complete");
        } else if(msg.equals("next phase complete")) {
            /* print current stats and reset the plugin to prepare for the next period */
            stats = plugin.radioStatistics();
            plugin.reset();
            log.log("RADIO STATS @ " + time + "\n" + stats + "\n");
            GENERATE_MSG(300000, "next phase complete");
        }
        log.log(time + " " + id + " " + msg + "\n");
    }

    YIELD();
}
