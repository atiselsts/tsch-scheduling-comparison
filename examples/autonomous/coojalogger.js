/* A simple log file generator script */

TIMEOUT(600000); /* 600 seconds or 10 minutes */

timeout_function = function () {
    log.log("Script timed out.\n");
    log.testOK();
}

if (msg) {
    log.log("> " + time + ":" + id + ":" + msg + "\n");
}

while (true) {
    YIELD();

    log.log("> " + time + ":" + id + ":" + msg + "\n");
}
