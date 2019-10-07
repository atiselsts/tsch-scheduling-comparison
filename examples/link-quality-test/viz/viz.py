#!/usr/bin/python3

import os

INDEX = 3

INFILES = [
    "file-3-neigh.log", # actually more like 2.5 with >80% link quality
    "file-4-neigh.log",
    "file-6-neigh.log", # actually more like 5 with >80% link quality
    "file-10-neigh.log",
]

OUTFILES = [
    "trace-3-neigh.txt",
    "trace-4-neigh.txt",
    "trace-6-neigh.txt",
    "trace-10-neigh.txt",
]

OUTDIR = "../traces"

nodes_assoc = {}

# (from, to) -> number of packets
packets_rxed = {}
# (from, to) -> number of packets
packets_rxed_last_round = {}
# (from, to) -> number of rounds
rounds_rxed = {}

COORD_NODE_ID = "m3-177"

order_3_neigh = {}
order_4_neigh = {}
order_6_neigh = {}
order_10_neigh = {}

order_3_neigh["m3-177"] = 1
order_3_neigh["m3-184"] = 2
order_3_neigh["m3-159"] = 3
order_3_neigh["m3-193"] = 4
order_3_neigh["m3-141"] = 5
order_3_neigh["m3-202"] = 6
order_3_neigh["m3-123"] = 7
order_3_neigh["m3-221"] = 8
order_3_neigh["m3-239"] = 9
order_3_neigh["m3-294"] = 10
order_3_neigh["m3-105"] = 11
order_3_neigh["m3-259"] = 12
order_3_neigh["m3-91"] = 13
order_3_neigh["m3-301"] = 14
order_3_neigh["m3-82"] = 15
order_3_neigh["m3-277"] = 16
order_3_neigh["m3-73"] = 17
order_3_neigh["m3-310"] = 18
order_3_neigh["m3-4"] = 19
order_3_neigh["m3-11"] = 20
order_3_neigh["m3-319"] = 21
order_3_neigh["m3-20"] = 22
order_3_neigh["m3-328"] = 23
order_3_neigh["m3-363"] = 24
order_3_neigh["m3-337"] = 25
order_3_neigh["m3-41"] = 26
order_3_neigh["m3-346"] = 27
order_3_neigh["m3-51"] = 28
order_3_neigh["m3-355"] = 29
order_3_neigh["m3-60"] = 30
order_3_neigh["m3-69"] = 31

order_4_neigh["m3-177"] = 1
order_4_neigh["m3-181"] = 2
order_4_neigh["m3-166"] = 3
order_4_neigh["m3-188"] = 4
order_4_neigh["m3-153"] = 5
order_4_neigh["m3-195"] = 6
order_4_neigh["m3-141"] = 7
order_4_neigh["m3-201"] = 8
order_4_neigh["m3-129"] = 9
order_4_neigh["m3-213"] = 10
order_4_neigh["m3-225"] = 11
order_4_neigh["m3-117"] = 12
order_4_neigh["m3-292"] = 13
order_4_neigh["m3-237"] = 14
order_4_neigh["m3-105"] = 15
order_4_neigh["m3-251"] = 16
order_4_neigh["m3-297"] = 17
order_4_neigh["m3-265"] = 18
order_4_neigh["m3-94"] = 19
order_4_neigh["m3-88"] = 20
order_4_neigh["m3-82"] = 21
order_4_neigh["m3-277"] = 22
order_4_neigh["m3-303"] = 23
order_4_neigh["m3-76"] = 24
order_4_neigh["m3-70"] = 25
order_4_neigh["m3-309"] = 26
order_4_neigh["m3-2"] = 27
order_4_neigh["m3-7"] = 28
order_4_neigh["m3-316"] = 29
order_4_neigh["m3-13"] = 30
order_4_neigh["m3-322"] = 31

order_6_neigh["m3-177"] = 1
order_6_neigh["m3-179"] = 2
order_6_neigh["m3-170"] = 3
order_6_neigh["m3-184"] = 4
order_6_neigh["m3-161"] = 5
order_6_neigh["m3-189"] = 6
order_6_neigh["m3-154"] = 7
order_6_neigh["m3-145"] = 8
order_6_neigh["m3-195"] = 9
order_6_neigh["m3-138"] = 10
order_6_neigh["m3-200"] = 11
order_6_neigh["m3-129"] = 12
order_6_neigh["m3-205"] = 13
order_6_neigh["m3-122"] = 14
order_6_neigh["m3-213"] = 15
order_6_neigh["m3-223"] = 16
order_6_neigh["m3-233"] = 17
order_6_neigh["m3-113"] = 18
order_6_neigh["m3-292"] = 19
order_6_neigh["m3-240"] = 20
order_6_neigh["m3-106"] = 21
order_6_neigh["m3-251"] = 22
order_6_neigh["m3-297"] = 23
order_6_neigh["m3-261"] = 24
order_6_neigh["m3-97"] = 25
order_6_neigh["m3-93"] = 26
order_6_neigh["m3-88"] = 27
order_6_neigh["m3-271"] = 28
order_6_neigh["m3-301"] = 29
order_6_neigh["m3-83"] = 30
order_6_neigh["m3-78"] = 31

order_10_neigh["m3-177"] = 1
order_10_neigh["m3-179"] = 2
order_10_neigh["m3-181"] = 3
order_10_neigh["m3-167"] = 4
order_10_neigh["m3-183"] = 5
order_10_neigh["m3-163"] = 6
order_10_neigh["m3-185"] = 7
order_10_neigh["m3-159"] = 8
order_10_neigh["m3-188"] = 9
order_10_neigh["m3-156"] = 10
order_10_neigh["m3-190"] = 11
order_10_neigh["m3-151"] = 12
order_10_neigh["m3-147"] = 13
order_10_neigh["m3-193"] = 14
order_10_neigh["m3-143"] = 15
order_10_neigh["m3-195"] = 16
order_10_neigh["m3-139"] = 17
order_10_neigh["m3-197"] = 18
order_10_neigh["m3-135"] = 19
order_10_neigh["m3-199"] = 20
order_10_neigh["m3-131"] = 21
order_10_neigh["m3-201"] = 22
order_10_neigh["m3-127"] = 23
order_10_neigh["m3-203"] = 24
order_10_neigh["m3-123"] = 25
order_10_neigh["m3-205"] = 26
order_10_neigh["m3-207"] = 27
order_10_neigh["m3-211"] = 28
order_10_neigh["m3-215"] = 29
order_10_neigh["m3-219"] = 30
order_10_neigh["m3-119"] = 31

orders = [order_3_neigh, order_4_neigh, order_6_neigh, order_10_neigh]

INFILE = INFILES[INDEX]
order = orders[INDEX]

num_nodes = len(order)

NORMAL_PER_ROUND = None

# XXX: at the moment, the channel info from the trace file is not fully used
DEFAULT_CHANNELS = [15, 20, 25, 26]

def process_packet_stats():
    links = {}
    prev_from = -1
    normal_expected = None
    for key in sorted(packets_rxed.keys()):
        (from_order, to_order) = key
        if prev_from != from_order:
            #print("")
            prev_from = from_order
        received = packets_rxed[key]
        expected = NORMAL_PER_ROUND * rounds_rxed[key]
        if normal_expected is None:
            normal_expected = expected
        #print("{} -> {}: {} from {}".format(from_order, to_order, received, expected))
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
        if (links[key] + links[rkey]) / 2 > normal_expected * 0.8:
            total_bidir_links += 1
        else:
            pass
            #print("  too few packets")

    avg_neighbors = 2 * total_bidir_links / len(nodes_assoc)
    print("total links {}, neighbors per node {}".format(total_bidir_links, avg_neighbors))

# output example:
#0;addnode;123.0
def start_trace_file(outf):
    for i in range(num_nodes):
        s = "0;addnode;{}.0\n".format(i + 1)
        outf.write(s)

# output example:
#0;setedgex;105.0;122.0;80;-92;85;18
def update_trace_file(packets_rxed, packets_rxed_prev, time_sec, outf):
    approx_time_ms = int(time_sec * 1000)
    if approx_time_ms == 0:
        # all nodes are added at time 0;
        # to make sure that happens before the links are added, set this to 1 ms minimum
        approx_time_ms = 1
    LQI = 85
    RSSI = -90
#    channel = 20
    num_nodes = len(order)

    for i in range(num_nodes):
        for j in range(num_nodes):
            if i == j:
                continue
            from_id = i + 1
            to_id = j + 1
            key = (from_id, to_id)
            num_packets = packets_rxed.get(key, 0)
            num_packets_prev = packets_rxed_prev.get(key, 0)
            if num_packets != num_packets_prev:
                pdr = 100.0 * num_packets / NORMAL_PER_ROUND
                for channel in DEFAULT_CHANNELS:
                    s = "{};setedgex;{}.0;{}.0;{:.1f};{};{};{}\n".format(
                        approx_time_ms, from_id, to_id, pdr, RSSI, LQI, channel)
                    outf.write(s)
        outf.write("\n")
    outf.write("\n")
  

def main():
    global NORMAL_PER_ROUND
    outfile = OUTFILES[INDEX]

    first_round_start_time = None
    round_start_time = None
    packets_rxed_last_round = {}
    packets_rxed_prev_round = {}
    
    nodes_assoc[COORD_NODE_ID] = 1
    num_associated = 1 
    all_assoc = False

    with open(os.path.join(OUTDIR, outfile), "w") as outf:
      start_trace_file(outf)
      with open(INFILE, "rt") as f:
        for line in f:
            fields = line.strip().split(";")
            if len(fields) < 3:
                continue
            ts = float(fields[0])
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
                        #print("starting a new round after assoc")
                        if round_start_time is not None:
                            # end previous round here, if needed
                            start = round_start_time - first_round_start_time
                            end = ts - first_round_start_time
                            if 0:
                                # use the midpoint
                                time_sec = (start + end) / 2.0
                            else:
                                # use the starting time of the test - allows to get results sooner.
                                time_sec = start
                            update_trace_file(packets_rxed_last_round, packets_rxed_prev_round, time_sec, outf)
                        # for the next round
                        round_start_time = ts
                        if first_round_start_time is None:
                            first_round_start_time = ts
                        packets_rxed_prev_round = dict(packets_rxed_last_round)
                        packets_rxed_last_round = {}
                continue
            #1569917003.937725;m3-239;8: 30 total
            if " total" in text:
                subfields = text.split()
                from_order = int(subfields[0][:-1])
                to_order = order[node]
                #print("from=", subfields[0], from_order)
                if to_order > num_nodes or from_order > num_nodes:
                    #print("ignoring bad node IDs at line " + line)
                    continue
                if to_order != from_order:
                    num_packets = int(subfields[1])
                    key = (from_order,to_order)
                    packets_rxed[key] = packets_rxed.get(key, 0) + num_packets
                    packets_rxed_last_round[key] = packets_rxed_last_round.get(key, 0) + num_packets
                    rounds_rxed[key] = rounds_rxed.get(key, 0) + 1

    process_packet_stats()

if __name__ == "__main__":
    try:
        os.mkdir(OUTDIR)
    except:
        pass
    main()
    print("all done")
