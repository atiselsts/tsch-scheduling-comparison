#!/usr/bin/python3

INFILE = "grenoble.txt"

# put the coordinator in the corner
coordinator_x = 0
coordinator_y = 0

MAX_NODES = 31

def get_by_dist(nodes, x, y):
    bydist = []
    for xi, yi, nodeid, m3id in nodes:
        d = ((xi - x) ** 2 + (yi - y) ** 2) ** 0.5
        bydist.append((d, xi, yi, nodeid, m3id))
    bydist.sort()
    return bydist

def printall(nodes, x, y, maxd):
    for d, xi, yi, nodeid, _ in get_by_dist(nodes, x, y):
        if d >= maxd:
            break
        print(xi, yi, nodeid)

def print_only_subset(nodes, x, y, maxd, min_dist, min_dist_from_coord = 0):
    bydist = get_by_dist(nodes, x, y)
    # find the closest first
    (_, real_coordinator_x, real_coordinator_y, real_coordinator_id, _) = bydist[0]
    print("using coordinator ", real_coordinator_x, real_coordinator_y, real_coordinator_id)

    coord = bydist[0]
    selected = [coord]
    for node in bydist[1:]:
        d_to_coord, x, y, _, _ = node
        if d_to_coord >= maxd:
            break
        ok = True
        if min_dist > 0:
            # filter by minimal dist from all selected
            for _, xi, yi, _, _ in selected:
                d = ((xi - x) ** 2 + (yi - y) ** 2) ** 0.5
                if d < min_dist:
                    ok = False
                    break
        if min_dist_from_coord > 0:
            _, xi, yi, _, _ = coord
            d = ((xi - x) ** 2 + (yi - y) ** 2) ** 0.5
            if d < min_dist_from_coord:
                ok = False
            
        if ok:
            # far enough from all, add this one
            selected.append(node)
            if len(selected) >= MAX_NODES:
                break

    print("nodes:")
    m3ids = []
    for d, xi, yi, nodeid, m3id in selected:
        print(m3id, xi, yi, nodeid)
        m3ids.append(m3id)
    # remove the "m3-" bit
    im3ids = [int(u[3:]) for u in m3ids]
    print("export nodes='" + "+".join([str(u) for u in sorted(im3ids)]) + "'")

    print("C code:")
    for d, xi, yi, nodeid, m3id in selected:
        print("  {:#x}, // x={} y={}".format(nodeid, xi, yi))

    print("mapping from ID to number")
    i = 1
    for d, xi, yi, nodeid, m3id in selected:
        print('order["{}"] = {}'.format(m3id, i))
        i += 1

def main():
    nodes = []
    with open(INFILE) as f:
        for line in f:
            fields = line.strip().split()
            state = fields[1].lower()
            if state != "busy" and state != "available":
                continue
            #m3-2.grenoble.iot-lab.info	Busy	M3 (at86rf231)	Grenoble		9982	20.70	26.76	-0.04
            m3id = fields[0].split(".")[0]
            nodeid = int(fields[5], 16)
            x = float(fields[6])
            y = float(fields[7])
            nodes.append((x, y, nodeid, m3id))

    # sparse (2.5-3 neighbors per node)
    #print_only_subset(nodes, coordinator_x, coordinator_y, 100, 5)

    # sparse 
    print_only_subset(nodes, coordinator_x, coordinator_y, 100, 3.5)

    # dense (5-6 neighbors per node)
    #print_only_subset(nodes, coordinator_x, coordinator_y, 30, 2.45)

    # dense (10-11 neighbors per node)
    #print_only_subset(nodes, coordinator_x, coordinator_y, 30, 1, 2.5)

if __name__ == "__main__":
    main()
    print("all done")

