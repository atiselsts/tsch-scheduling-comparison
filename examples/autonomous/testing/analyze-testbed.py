#!/usr/bin/python3

import os
import sys
import time
import subprocess
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pl
import matplotlib.legend_handler as lh
import numpy as np

from parameters import *

#
# This calculates and plots these metrics:
# - End-to-end PDR
# - Link-layer PRR (between a node and all of its neighbors)
# - Radio Duty Cycle
#
# The radio duty cycle is based on Energest results.
# For Cooja motes, those are quite approximate
# (as e.g. clock drift is not simulated, SPI communication time is not simulated).
#

matplotlib.style.use('seaborn')
matplotlib.rcParams['pdf.fonttype'] = 42


OUT_DIR = "../plots"

DATA_DIRECTORY = "../simulations"

TESTBED_HOST = "elsts@grenoble.iot-lab.fr"

# (local, remote)
TESTBED_DIRS = [
    ("../iot-lab-realloc1/", "iot-lab-firmwares-realloc1"),
    ("../iot-lab-realloc2/", "iot-lab-firmwares-realloc2"),
    ("../iot-lab-realloc3/", "iot-lab-firmwares-realloc3"),
]

DATA_FILE = "cached_data.json"
DATA_FILE2 = "cached_data2.json"

START_TIME_MINUTES = 30
END_TIME_MINUTES = 58

# The root node is ignored in the calculations (XXX: maybe should not ignore its PRR?)
ROOT_ID_SIM = 1
ROOT_ID_TESTBED = 177

# confidence interval
CI = 0.9

ONLY_MEDIAN = False

node_id_to_mote_id = {}

###########################################

MARKERS = ["o", "s", "X", "X", "X", "X"]
BASIC_MARKERS = ["o", "s", "X", "X", "X", "X"]

###########################################

def graph_scatter(xdata, ydata, xlabel, ylabel, pointlabels, filename):
    pl.figure(figsize=(5, 4.5))

    algos = ALGORITHMS

    for i, a in enumerate(algos):
        algo_xdata = xdata[i]
        algo_ydata = ydata[i]

        to_plot_x = algo_xdata #[np.mean(d) for d in algo_xdata]
        to_plot_y = algo_ydata #[np.mean(d) for d in algo_ydata]

        pl.scatter(to_plot_x, to_plot_y, label=ALGONAMES[a], color=COLORS[a],
                   marker="o" if "Orchestra" in ALGONAMES[a] else "v")

        if pointlabels is not None:
            for j, sf in enumerate(pointlabels[i]):
                pl.gca().annotate("{}".format(sf), (to_plot_x[j] + 0.1, to_plot_y[j] + 1), fontsize=6)

    pl.ylim(bottom=0, top=105)
    pl.xlabel(xlabel)
    pl.ylabel(ylabel)
    if "duty" in filename:
        pl.xlim([0, 10])
    else: # send frequency
        pl.xscale("log")

    pl.gca().axhline(y=100, color="black", lw=1)

#    bbox = (1.0, 1.3)
#    loc = "upper right"

    if "pdr" in filename:
        legend = pl.legend()
#        legend = pl.legend(bbox_to_anchor=bbox, loc=loc, ncol=2,
#                           prop={"size":11},
#                           handler_map={lh.Line2D: lh.HandlerLine2D(numpoints=1)})

        pl.savefig(OUT_DIR + "/" + filename, format='pdf',
                   bbox_extra_artists=(legend,),
                   bbox_inches='tight')
    else:
        pl.savefig(OUT_DIR + "/" + filename, format='pdf',
                   bbox_inches='tight')
    pl.close()

###########################################

def graph_line(xdata, ydata, xlabel, ylabel, filename):
    pl.figure(figsize=(4, 2))

    algos = ALGORITHMS

    for i, a in enumerate(algos):
        algo_ydata = ydata[i]

        to_plot_y = algo_ydata #[np.mean(d) for d in algo_ydata]

        pl.plot(xdata, to_plot_y, label=ALGONAMES[a], color=COLORS[a],
                marker="o" if "Orchestra" in ALGONAMES[a] else "v")

    if "queue" in filename:
        # for the queue losses graph
        pl.ylim(bottom=0, top=300)
    else:
        # PDR and PAR
        pl.ylim(bottom=0, top=105)
        pl.gca().axhline(y=100, color="black", lw=1)

    pl.xlabel(xlabel)
    pl.ylabel(ylabel)
    pl.xticks(xdata, [str(u) for u in xdata])

#    legend = pl.legend()
    pl.savefig(OUT_DIR + "/" + filename, format='pdf',
#              bbox_extra_artists=(legend,),
               bbox_inches='tight')
    pl.close()

###########################################

def get_seqnums(send_interval, start_time = START_TIME_MINUTES):
    duration_seconds = (END_TIME_MINUTES - START_TIME_MINUTES) * 60
    num_packets = duration_seconds // send_interval
    if start_time <= START_TIME_MINUTES:
        first_packet = 1
    else:
        skipped_seqnums = (start_time - START_TIME_MINUTES) * 60 // send_interval
        first_packet = 1 + skipped_seqnums
    return (first_packet, num_packets)

###########################################

class MoteStats:
    def __init__(self, id):
        self.id = id
        self.seqnums = set()
        self.associated_at_minutes = None
        self.packets_tx = 0
        self.packets_ack = 0
        self.radio_on = 0
        self.radio_total = 0
        self.is_valid = False
        self.queue_losses = 0

    def calc(self, send_interval, first_seqnum, last_seqnum):
        if self.associated_at_minutes is None:
            print("node {} never associated".format(self.id))
            #self.is_valid = False
            #return
        elif self.associated_at_minutes >= 30:
            print("node {} associated too late: {}, seqnums={}".format(
                self.id, self.associated_at_minutes, self.seqnums))
            #self.is_valid = False
            #return

        self.is_valid = True
	# XXX: hack for the sparse test - disable node 259, too bad connectivity
        if self.id == 259:
            self.is_valid = False

        if self.packets_tx:
            self.prr = 100.0 * self.packets_ack / self.packets_tx
        else:
            self.prr = 0.0

        if self.associated_at_minutes is None:
            last_seqnum = 0
            first_seqnum = 0
        elif self.associated_at_minutes >= 30:
            first_seqnum, last_seqnum = get_seqnums(send_interval)

        expected = (last_seqnum - first_seqnum) + 1
        actual = len(self.seqnums)

        #print("node={} associated={}, seqnums={}".format(
        #        self.id, self.associated_at_minutes, self.seqnums))
        if expected:
            self.pdr = 100.0 * actual / expected
        else:
            self.pdr = 0.0

        if self.radio_total:
            self.rdc = 100.0 * self.radio_on / self.radio_total
        else:
            print("warning: no radio duty cycle for {}".format(self.id))
            self.rdc = 0.0

###########################################

def process_file(filename, experiment, send_interval, is_testbed):
    motes = {}
    has_assoc = set()
    print(filename)

    in_initialization = True

    first_seqnum, last_seqnum = get_seqnums(send_interval)
    start_ts_unix = None

    ROOT_ID = ROOT_ID_TESTBED if is_testbed else ROOT_ID_SIM

    with open(filename, "r") as f:
        for line in f:
            #print(line)
            if is_testbed:
                fields1 = line.strip().split(";")
                if len(fields1) < 3:
                    continue
                fields2 = fields1[2].split()
                fields = fields1[:2] + fields2
            else:
                fields = line.strip().split()

            try:
                # in milliseconds
                if is_testbed:
                    ts_unix = float(fields[0])
                    if start_ts_unix is None:
                        start_ts_unix = ts_unix
                    ts_unix -= start_ts_unix
                    ts = int(float(ts_unix) * 1000)
                    node = int(fields[1][3:])
                else:
                    ts = int(fields[0]) // 1000
                    node = int(fields[1]) 
            except:
                # failed to extract timestamp
                continue

            if node not in motes:
                motes[node] = MoteStats(node)

            if is_testbed and "Node ID:" in line:
                # 1570531244.735377;m3-197;[INFO: Main      ] Node ID: 43378
                node_id = int(fields[7])
                node_id_to_mote_id[node_id] = node

            if "association done (1" in line:
                #print(line)
                has_assoc.add(node)
                motes[node].seqnums = set()
                motes[node].associated_at_minutes = (ts // 1000 + 59) // 60
                continue

            if in_initialization:
                # ignore the first N minutes of the test, while the network is being built
                if ts > START_TIME_MINUTES * 60 * 1000:
                    in_initialization = False
                else:
                    continue

            # both for root and normal nodes
            if "add packet failed" in line:
                # account for queue drops
                motes[node].queue_losses += 1
                continue

            if node == ROOT_ID or "local" in experiment:
                # 314937392 1 [INFO: Node      ] seqnum=6 from=fd00::205:5:5:5
                if "seqnum=" in line:
                    sn = int(fields[5].split("=")[1])
                    if not (first_seqnum <= sn <= last_seqnum):
                        if sn > last_seqnum:
                            break
                        continue
                    if "=" not in fields[6]:
                        continue
                    fromtext, fromaddr = fields[6].split("=")
                    # this is needed to distinguish between "from" and "to" in the query example
                    if fromtext == "from":
                        fromnode = int(fromaddr.split(":")[-1], 16)
                        if is_testbed:
                            fromnode = node_id_to_mote_id.get(fromnode, 0)
                        if fromnode in has_assoc:
                            # account for the seqnum
                            motes[fromnode].seqnums.add(sn)
                            # print("add sn={} fromnode={}".format(sn, fromnode))

                if "local" not in experiment:
                    # ignore the root, except for PDR
                    continue

            if node not in has_assoc:
                continue

            # 600142000 28 [INFO: Link Stats] num packets: tx=0 ack=0 rx=0 to=0014.0014.0014.0014
            if "num packets" in line:
                tx = int(fields[7].split("=")[1])
                ack = int(fields[8].split("=")[1])
                rx = int(fields[9].split("=")[1])
                motes[node].packets_tx += tx
                motes[node].packets_ack += ack
                continue

            # 600073000:8 [INFO: Energest  ] Radio total :    1669748/  60000000 (27 permil)
            if "Radio total" in line:
                # only account for the period when data packets are sent
                if ts > START_TIME_MINUTES * 60 * 1000:
                    on = int(fields[8][:-1])
                    total = int(fields[9])
                    motes[node].radio_on += on
                    motes[node].radio_total += total
                    continue

    r = []
    root_queue_losses = 0
    for k in motes:
        m = motes[k]
        if m.id == ROOT_ID:
            root_queue_losses = m.queue_losses
            continue
        m.calc(send_interval, first_seqnum, last_seqnum)
        if m.is_valid:
            #print(" {} {:.1f} {:.1f} {} {}".format(m.id, m.pdr, m.prr, m.packets_ack, m.packets_tx))
            r.append((m.pdr, m.prr, m.packets_ack, m.packets_tx, m.rdc, m.queue_losses))
        else:
            print("mote {} does not have valid PDR: packets={}".format(m.id, m.seqnums))
    return r, root_queue_losses

###########################################

def exec_remote_cmd(cmd):
    subprocess.call("ssh " + TESTBED_HOST + " '" + cmd + "'", shell=True)

###########################################

def exec_local_cmd(cmd):
    subprocess.call(cmd, shell=True)

###########################################

def load_single_testbed(local, remote, filename, exp, si):
    local_file = os.path.join(local, filename)
    remote_file = os.path.join(remote, filename)
    local_file_tgz = local_file + ".tgz"
    remote_file_tgz = remote_file + ".tgz"

    if not os.access(local_file, os.R_OK):
        print("Trying to get the remote file...")
        exec_remote_cmd("tar -czf " + remote_file_tgz + " " + remote_file)
        subprocess.call("scp " + TESTBED_HOST + ":" + remote_file_tgz + " " + local_file_tgz, shell=True)
        exec_local_cmd("tar -xzf " + local_file_tgz)
        exec_local_cmd("mv " + remote_file + " " + local_file)
        exec_remote_cmd("rm " + remote_file_tgz)
        exec_local_cmd("rm " + local_file_tgz)
        if not os.access(local_file, os.R_OK):
            print("failed to read file " + local_file)
            return (0.0, 0.0, 0.0, 0.0)

    r, root_queue_losses = process_file(local_file, exp, si, True)

    t_pdr_results = []
    t_prr_results = []
    t_rdc_results = []
    t_queue_losses = []

    all_packets_ack = 0
    all_packets_tx = 0

    for pdr, prr, packets_ack, packets_tx, rdc, queue_losses in r:
        t_pdr_results.append(pdr)
        all_packets_ack += packets_ack
        all_packets_tx += packets_tx
        t_prr_results.append(prr)
        t_rdc_results.append(rdc)
        t_queue_losses.append(queue_losses)
    t_queue_losses.append(root_queue_losses)

    if ONLY_MEDIAN:
        if len(t_pdr_results):
            midpoint = len(t_pdr_results) // 2
            print("pdr=", sorted(t_pdr_results))
            pdr_metric = sorted(t_pdr_results)[midpoint]
            prr_metric = sorted(t_prr_results)[midpoint]
            rdc_metric = sorted(t_rdc_results)[midpoint]
            queue_losses = sorted(t_queue_losses)[midpoint]
        else:
            pdr_metric = 0.0
            prr_metric = 0.0
            rdc_metric = 0.0
            queue_losses = 0.0
    else:
        pdr_metric = np.mean(t_pdr_results)
        prr_metric = 100.0 * all_packets_ack / all_packets_tx
        rdc_metric = np.mean(t_rdc_results)
        queue_losses = np.mean(t_queue_losses)
#        print("pdr=", pdr_metric, "all=", sorted(t_pdr_results))
        #print("prr=", prr_metric, "all=", ", ".join(["{:.1f}".format(u) for u in sorted(t_prr_results)]))
        
    return (pdr_metric, prr_metric, rdc_metric, queue_losses)

###########################################

def load_testbed(data_directory, data, a, si, sf, exp, nn):
    data[a][str(si)][str(sf)][exp][str(nn)] = {}

    filename = ""
    if nn == 10:
        filename = "dense-"
    else:
        filename = "sparse-"
    filename += a + "_"
    filename += "si_{}_".format(si)
    filename += "sf_{}_".format(sf)
    filename += exp
    filename += ".log"

    metrics = []
    for local, remote in TESTBED_DIRS:
        metrics.append(load_single_testbed(local, remote, filename, exp, si))

    if 0:
        # use the median result
        midpoint = len(metrics) // 2
        metrics.sort(key = lambda u: u[0]) # sort by PDR
        pdr_metric = metrics[midpoint][0]
        prr_metric = metrics[midpoint][1]
        rdc_metric = metrics[midpoint][2]
        queue_losses = metrics[midpoint][3]
    else:
        pdr_metric = np.mean([u[0] for u in metrics])
        prr_metric = np.mean([u[1] for u in metrics])
        rdc_metric = np.mean([u[2] for u in metrics])
        queue_losses = np.mean([u[3] for u in metrics])

    data[a][str(si)][str(sf)][exp][str(nn)]["pdr"] = pdr_metric
    data[a][str(si)][str(sf)][exp][str(nn)]["prr"] = prr_metric
    data[a][str(si)][str(sf)][exp][str(nn)]["rdc"] = rdc_metric
    data[a][str(si)][str(sf)][exp][str(nn)]["queue_losses"] = queue_losses
    print("")

###########################################

def load_all(data_directory):
    data = {}
    for a in ALGORITHMS:
        data[a] = {}
        for si in SEND_INTERVALS:
            data[a][str(si)] = {}
            for sf in SLOTFRAME_SIZES:
                data[a][str(si)][str(sf)] = {}
                for exp in EXPERIMENTS:
                    data[a][str(si)][str(sf)][exp] = {}
                    for nn in NUM_NEIGHBORS:
                        load_testbed(data_directory, data, a, si, sf, exp, nn)

    return data

###########################################

def aggregate(data, a, si, sf, exp, nn, metric):
    return data[a][str(si)][str(sf)][exp][str(nn)][metric]

###########################################

def plot_all_pdr(data, exp):
    # plot all per duty cycle
    for nn in NUM_NEIGHBORS:
        for si in SEND_INTERVALS:
            pdr_results = [[] for _ in ALGORITHMS]
            rdc_results = [[] for _ in ALGORITHMS]
            pointlabels = [[] for _ in ALGORITHMS]
            for sf in SLOTFRAME_SIZES:
                sfs = "sf={}".format(sf)
                print(sfs)
                for i, a in enumerate(ALGORITHMS):
                    print("Algorithm {}".format(ALGONAMES[a]))
                    rdc_results[i].append(aggregate(data, a, si, sf, exp, nn, "rdc"))
                    pdr_results[i].append(aggregate(data, a, si, sf, exp, nn, "pdr"))
                    pointlabels[i].append(sfs)

            filename = "realloc_{}_pdr_per_duty_cycle_allsf_nn{}_si{}.pdf".format(exp, nn, si)
            graph_scatter(rdc_results,  pdr_results, "Duty cycle, %", "End-to-end PDR, %", pointlabels,
                          filename)

###########################################

def plot_all_par(data, exp):
    # plot all per duty cycle
    for nn in NUM_NEIGHBORS:
        for si in SEND_INTERVALS:
            par_results = [[] for _ in ALGORITHMS]
            for i, a in enumerate(ALGORITHMS):
                print("Algorithm {}".format(ALGONAMES[a]))
                for j, sf in enumerate(SLOTFRAME_SIZES):
                    par_results[i].append(aggregate(data, a, si, sf, exp, nn, "prr"))

            filename = "realloc_{}_par_per_slotframe_allsf_nn{}_si{}.pdf".format(exp, nn, si)
            print(par_results)
            graph_line(SLOTFRAME_SIZES, par_results, "Slotframe size, slots", "Packet ACK Rate, %", filename)

###########################################

def plot_all_queue_losses(data, exp):
    # plot all per duty cycle
    for nn in NUM_NEIGHBORS:
        for si in SEND_INTERVALS:
            results = [[] for _ in ALGORITHMS]
            for i, a in enumerate(ALGORITHMS):
                print("Algorithm {}".format(ALGONAMES[a]))
                for j, sf in enumerate(SLOTFRAME_SIZES):
                    results[i].append(aggregate(data, a, si, sf, exp, nn, "queue_losses"))

            filename = "realloc_{}_queue_losses_per_slotframe_allsf_nn{}_si{}.pdf".format(exp, nn, si)
            graph_line(SLOTFRAME_SIZES, results, "Slotframe size, slots", "Num queue losses", filename)


###########################################

def ensure_loaded(data_file, data_directory):
    if os.access(data_file, os.R_OK):
        print("Cached file found, using it directly")
        with open(data_file, "r") as f:
            data = json.load(f)
    else:
        print("Cached file not found, parsing log files...")
        data = load_all(data_directory)
        with open(data_file, "w") as f:
            json.dump(data, f)
    return data

###########################################

def safe_mkdir(dirname):
    try:
        os.mkdir(dirname)
    except:
        pass

###########################################

def main():
    safe_mkdir(OUT_DIR)
    for local, remote in TESTBED_DIRS:
        safe_mkdir(local)
        safe_mkdir(remote)

    data = ensure_loaded(DATA_FILE, DATA_DIRECTORY)

    for exp in EXPERIMENTS:
        plot_all_pdr(data, exp)
        plot_all_par(data, exp)
        plot_all_queue_losses(data, exp)

###########################################

if __name__ == '__main__':
    main()
    print("all done!")
