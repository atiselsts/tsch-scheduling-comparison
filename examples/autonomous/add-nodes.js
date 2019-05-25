TIMEOUT(3600000); /* 1 hour */
timeout_function = function () {
    log.log("Script timed out.\n");
    log.testOK();
}

nextNodeID = 3;

/* after 10 seconds */
GENERATE_MSG(10000, "time to add new node");

while (true) {
    if (msg) {
        if(msg.equals("time to add new node")) {
            // after 5 seconds
            GENERATE_MSG(5000, "time to add new node");

            m = sim.getMoteTypes()[0].generateMote(sim);
            m.getInterfaces().getMoteID().setMoteID(nextNodeID);
            m.getInterfaces().getPosition().setCoordinates(50, 50, 0);
            sim.addMote(m);
            log.log("added a new node with ID " + nextNodeID + "\n");
            nextNodeID++;

        } else {
            log.log(time + " " + id + " " + msg + "\n");
        }
    }

    YIELD();
}
