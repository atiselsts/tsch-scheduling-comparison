#!/usr/bin/python3

#INFILE = "file-sparse.log"
INFILE = "file-dense.log"

nodes_assoc = {}

# (from, to) -> number of packets
packets_rxed = {}
# (from, to) -> number of rounds
rounds_rxed = {}

COORD_NODE_ID = "m3-177"

is_valid_round = False

order = {}
if 0: # sparse subset
    order["m3-177"] = 1
    order["m3-184"] = 2
    order["m3-159"] = 3
    order["m3-193"] = 4
    order["m3-141"] = 5
    order["m3-202"] = 6
    order["m3-123"] = 7
    order["m3-221"] = 8
    order["m3-239"] = 9
    order["m3-294"] = 10
    order["m3-105"] = 11
    order["m3-259"] = 12
    order["m3-91"] = 13
    order["m3-301"] = 14
    order["m3-82"] = 15
    order["m3-277"] = 16
    order["m3-73"] = 17
    order["m3-310"] = 18
    order["m3-4"] = 19
    order["m3-11"] = 20
    order["m3-319"] = 21
    order["m3-20"] = 22
    order["m3-328"] = 23
    order["m3-363"] = 24
    order["m3-337"] = 25
    order["m3-41"] = 26
    order["m3-346"] = 27
    order["m3-51"] = 28
    order["m3-355"] = 29
    order["m3-60"] = 30
    order["m3-69"] = 31
else: # dense subset
    order["m3-177"] = 1
    order["m3-179"] = 2
    order["m3-170"] = 3
    order["m3-184"] = 4
    order["m3-161"] = 5
    order["m3-189"] = 6
    order["m3-154"] = 7
    order["m3-145"] = 8
    order["m3-195"] = 9
    order["m3-138"] = 10
    order["m3-200"] = 11
    order["m3-129"] = 12
    order["m3-205"] = 13
    order["m3-122"] = 14
    order["m3-213"] = 15
    order["m3-223"] = 16
    order["m3-233"] = 17
    order["m3-113"] = 18
    order["m3-292"] = 19
    order["m3-240"] = 20
    order["m3-106"] = 21
    order["m3-251"] = 22
    order["m3-297"] = 23
    order["m3-261"] = 24
    order["m3-97"] = 25
    order["m3-93"] = 26
    order["m3-88"] = 27
    order["m3-271"] = 28
    order["m3-301"] = 29
    order["m3-83"] = 30
    order["m3-78"] = 31

NORMAL_PER_ROUND = None

def process_packet_stats():
    links = {}
    prev_from = -1
    normal_expected = None
    for key in sorted(packets_rxed.keys()):
        (from_order, to_order) = key
        if prev_from != from_order:
            print("")
            prev_from = from_order
        received = packets_rxed[key]
        expected = NORMAL_PER_ROUND * rounds_rxed[key]
        if normal_expected is None:
            normal_expected = expected
        print("{} -> {}: {} from {}".format(from_order, to_order, received, expected))
        if received:
            links[key] = received

    keys = set()
    for key in list(links.keys()):
        (from_order, to_order) = key
        rkey = (to_order, from_order)
        if from_order < to_order:
            skey = key
        else:
            skey = rkey
        keys.add(skey)
        if rkey not in links:
            links[rkey] = 0

    print("\nbidirectional links")
    total_bidir_links = 0
    for key in sorted(keys):
        rkey = (key[1], key[0])
        print("{} <-> {}: {} {}".format(key[0], key[1], links[key], links[rkey]))
        # at least 50 % success rate?
        if links[key] + links[rkey] > normal_expected:
            total_bidir_links += 1
        else:
            pass
            #print("  too few packets")

    avg_neighbors = 2 * total_bidir_links / len(nodes_assoc)
    print("total links {}, neighbors per node {}".format(total_bidir_links, avg_neighbors))


def main():
    global NORMAL_PER_ROUND
    num_associated = 0
    all_assoc = False

    with open(INFILE, "rt") as f:
        for line in f:
            fields = line.strip().split(";")
            if len(fields) < 3:
                continue
            node = fields[1]
            text = fields[2]
            if node not in nodes_assoc:
                nodes_assoc[node] = False
            if "association done" in text:
                if nodes_assoc[node] == False:
                    nodes_assoc[node] = True
                    num_associated += 1                    
                    if num_associated == len(nodes_assoc):
                        print("all associated")
                        all_assoc = True
                continue
            if " schedule " in text and " packets" in text:
                subfields = text.split()
                if NORMAL_PER_ROUND is None:
                    # find out how many packets sent per round
                    NORMAL_PER_ROUND = int(subfields[2])
                if "coordinator" in text or node == COORD_NODE_ID:
                    if all_assoc:
                        print("starting a new round after assoc")
                        if is_valid_round:
                            # end previous round here, if needed
                            pass
                        is_valid_round = True
                continue
            #1569917003.937725;m3-239;8: 30 total
            if " total" in text:
                subfields = text.split()
                to_order = order[node]
                from_order = int(subfields[0][:-1])
                #print("from=", subfields[0], from_order)
                if to_order >= 32 or from_order >= 32:
                    continue
                if to_order != from_order:
                    num_packets = int(subfields[1])
                    key = (from_order,to_order)
                    packets_rxed[key] = packets_rxed.get(key, 0) + num_packets
                    rounds_rxed[key] = rounds_rxed.get(key, 0) + 1

    process_packet_stats()

if __name__ == "__main__":
    main()
    print("all done")
