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

if (msg) {
    log.log("> " + time + ":" + id + ":" + msg + "\n");
}

while (true) {
    YIELD();

    log.log("> " + time + ":" + id + ":" + msg + "\n");
}
