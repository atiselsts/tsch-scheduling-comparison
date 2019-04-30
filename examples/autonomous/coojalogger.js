/* A simple log file generator script */

TIMEOUT(600000); /* 600 seconds or 10 minutes */

plugin = mote.getSimulation().getCooja().getStartedPlugin("PowerTracker");
if (plugin === null) {
  log.log("No PowerTracker plugin\n");
  log.testFailed();
}

timeout_function = function () {
    log.log("Script timed out.\n");

    stats = plugin.radioStatistics();
    log.log("RADIO STATS @ " + time + "\n" + stats + "\n");

    log.testOK();
}

/* after 300 seconds or 5 minutes */
GENERATE_MSG(300000, "initial phase complete");

while (true) {
    if (msg) {
        if(msg.equals("initial phase complete")) {
            /* all nodes should be joined by now */
            stats.reset();
        }
        log.log("> " + time + ":" + id + ":" + msg + "\n");
    }

    YIELD();
}
