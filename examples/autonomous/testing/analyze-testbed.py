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
from scipy import stats
from scipy.stats.stats import pearsonr
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

DATA_DIRECTORY="../simulations"
DATA_DIRECTORY2="../simulations-all-enabled"

TESTBED_HOST = "elsts@grenoble.iot-lab.fr"

TESTBED_LOCAL_DIR = "../iot-lab/"
TESTBED_REMOTE_DIR = "iot-lab-firmwares"

DATA_FILE = "cached_data.json"
DATA_FILE2 = "cached_data2.json"

START_TIME_MINUTES = 30
END_TIME_MINUTES = 60

# The root node is ignored in the calculations (XXX: maybe should not ignore its PRR?)
ROOT_ID_SIM = 1
ROOT_ID_TESTBED = 177

# confidence interval
CI = 0.9

ONLY_MEDIAN = True

###########################################

MARKERS = ["o", "s", "X", "X", "X", "X"]
BASIC_MARKERS = ["o", "s", "X", "X", "X", "X"]

###########################################

def graph_ci(data, ylabel, filename):
    pl.figure(figsize=(6, 3.5))

    width = 0.15

#   print(filename)
    for i, a in enumerate(ALGORITHMS):
        algo_data = data[i]
#       print(ALGONAMES[i])

        to_plot = []
        yerr = []
        for d in algo_data:
#           if "pdr" in filename:
#               print("d=", d)
            mean, sigma = np.mean(d), np.std(d)
            stderr = 1.0 * sigma / (len(d) ** 0.5)
            ci = stats.norm.interval(CI, loc=mean, scale=stderr) - mean

            to_plot.append(mean)
            yerr.append(ci[0])

        x = np.arange(len(to_plot)) + (1.0 - width * 2) + width * i
        if 0:
            pl.errorbar(x, to_plot, width, yerr=yerr, marker=MARKERS[i], label=ALGONAMES[a])
        else:
            pl.bar(x, to_plot, width, yerr=yerr, label=ALGONAMES[a], color=COLORS[a])
#        print("plot ", ylabel)
#        print(to_plot)

    pl.ylim(ymin=0)
    pl.xlabel("Experiment type")
    pl.ylabel(ylabel)

#    pl.xticks([1, 2, 3, 4], ["sparse", "e. sparse", "dense", "e. dense"])
    pl.xticks([1, 2], ["sparse", "dense"])

    bbox = (1.0, 1.4)
    loc = "upper right"
    # pl.ylim([0, 700])

    if "pdr" in filename:
        legend = pl.legend(bbox_to_anchor=bbox, loc=loc, ncol=1,
                           prop={"size":11},
                           handler_map={lh.Line2D: lh.HandlerLine2D(numpoints=1)})

        pl.savefig(OUT_DIR + "/" + filename, format='pdf',
                   bbox_extra_artists=(legend,),
                   bbox_inches='tight')
    else:
        pl.savefig(OUT_DIR + "/" + filename, format='pdf',
                   bbox_inches='tight')

###########################################

def graph_line(xdata, ydata, xlabel, ylabel, pointlabels, filename):
    pl.figure(figsize=(6, 3.5))

    width = 0.15

    if len(xdata) == len(ALGORITHMS):
        algos = ALGORITHMS
    elif len(xdata) == len(BEST_ALGORITHMS):
        algos = BEST_ALGORITHMS
    elif len(xdata) == 2:
        algos = COMPARATIVE_ALGORITHMS
    else:
        raise "Unknown data dimensions"

    for i, a in enumerate(algos):
        algo_xdata = xdata[i]
        algo_ydata = ydata[i]

        to_plot_x = algo_xdata #[np.mean(d) for d in algo_xdata]
        to_plot_y = algo_ydata #[np.mean(d) for d in algo_ydata]

        pl.scatter(to_plot_x, to_plot_y, label=ALGONAMES[a], color=COLORS[a])

        if pointlabels is not None:
            for j, sf in enumerate(pointlabels[i]):
                pl.gca().annotate("{}".format(sf), (to_plot_x[j] + 0.1, to_plot_y[j] + 1), fontsize=6)

    pl.ylim(bottom=0, top=105)
    pl.xlabel(xlabel)
    pl.ylabel(ylabel)
    if "duty" in filename:
        pl.xlim([0, 13])
    else: # send frequency
        pl.xscale("log")

    pl.gca().axhline(y=100)

    bbox = (1.0, 1.3)
    loc = "upper right"

    if "pdr" in filename:
        legend = pl.legend(bbox_to_anchor=bbox, loc=loc, ncol=2,
                           prop={"size":11},
                           handler_map={lh.Line2D: lh.HandlerLine2D(numpoints=1)})

        pl.savefig(OUT_DIR + "/" + filename, format='pdf',
                   bbox_extra_artists=(legend,),
                   bbox_inches='tight')
    else:
        pl.savefig(OUT_DIR + "/" + filename, format='pdf',
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
    node_id_to_mote_id = {}
    print(filename)

    in_initialization = True

    first_seqnum, last_seqnum = get_seqnums(send_interval)
    start_ts_unix = None

    ROOT_ID = ROOT_ID_TESTBED if is_testbed else ROOT_ID_SIM

    with open(filename, "r") as f:
        for line in f:
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

            if node == ROOT_ID or "local" in experiment:
                # 314937392 1 [INFO: Node      ] seqnum=6 from=fd00::205:5:5:5
                if "seqnum=" in line:
                    #print(line)
                    sn = int(fields[5].split("=")[1])
                    if not (first_seqnum <= sn <= last_seqnum):
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

            if "add packet failed" in line:
                # TODO: account for queue drops!
                continue

    r = []
    for k in motes:
        m = motes[k]
        if m.id == ROOT_ID:
            continue
        m.calc(send_interval, first_seqnum, last_seqnum)
        if m.is_valid:
            #print(" ", m.id, m.pdr, m.prr)
            r.append((m.pdr, m.prr, m.rdc))
#        else:
#            print("mote {} does not have valid PDR: packets={}".format(m.id, m.seqnums))
    return r

###########################################

def compare_basic_metrics(filenames, experiment, description, ss):
    print(description)

    pdr_results = [[] for _ in ALGORITHMS]
    prr_results = [[] for _ in ALGORITHMS]
    rdc_results = [[] for _ in ALGORITHMS]

    outfilename = experiment + ".pdf"

    for a in ALGORITHMS:
        print("Algorithm {}_{}".format(ALGONAMES[a], ss))
        for j, fs in enumerate(filenames):
            t_pdr_results = []
            t_prr_results = []
            t_rdc_results = []

            path = os.path.join(DATA_DIRECTORY, "{}_{}".format(a, ss), "exp-" + experiment, fs)

            for dirname in subprocess.check_output("ls -d " + path, shell=True).split():
                resultsfile = os.path.join(dirname.decode("ascii"), "COOJA.testlog")

                if not os.access(resultsfile, os.R_OK):
                    continue

                r = process_file(resultsfile, experiment)
                for pdr, prr, rdc in r:
                    t_pdr_results.append(pdr)
                    t_prr_results.append(prr)
                    t_rdc_results.append(rdc)

            pdr_results[i].append(t_pdr_results)
            prr_results[i].append(t_prr_results)
            rdc_results[i].append(t_rdc_results)

    # plot the results
    graph_ci(pdr_results, "End-to-end PDR, %", "sim_pdr_" + outfilename)
    graph_ci(prr_results, "Link-layer PRR, %", "sim_prr_" + outfilename)
    graph_ci(rdc_results, "Radio duty cycle, %", "sim_rdc_" + outfilename)

    print("")

###########################################

def compare_per_duty_cycle(filenames, experiment, description):
    print("per duty cycle", description)

    outfilename = experiment + ".pdf"

    for j, fs in enumerate(filenames):
#        t_pdr_results = []
#        t_prr_results = []
#        t_rdc_results = []

        pdr_results = [[] for _ in ALGORITHMS]
        rdc_results = [[] for _ in ALGORITHMS]

        for a in ALGORITHMS:

            print("Algorithm {}".format(ALGONAMES[a]))

            for ss in SLOTFRAME_SIZES:

                t_pdr_results = []
                t_rdc_results = []

                path = os.path.join(DATA_DIRECTORY, "{}_{}".format(a, ss), "exp-" + experiment, fs)

                for dirname in subprocess.check_output("ls -d " + path, shell=True).split():
                    resultsfile = os.path.join(dirname.decode("ascii"), "COOJA.testlog")

                    if not os.access(resultsfile, os.R_OK):
                        continue

                    r = process_file(resultsfile, experiment)
                    for pdr, _, rdc in r:
                        t_pdr_results.append(pdr)
                        t_rdc_results.append(rdc)

                pdr_results[i].append(np.mean(t_pdr_results))
                rdc_results[i].append(np.mean(t_rdc_results))

        # plot the results
        pdffile = "sim_pdr_per_duty_cycle_" + fs.replace("*", "").replace("-", "") + "_" + outfilename
        graph_line(rdc_results, pdr_results, "Duty cycle, %", "End-to-end PDR, %",
                   pdffile)

###########################################

def test_groups(filenames, experiment, description):
    print(description)

#    compare_basic_metrics(filenames, experiment, description, ss=11)

    compare_per_duty_cycle(filenames, experiment, description)

###########################################

def load_simulations(data_directory, data, a, si, sf, exp, nn):
    data[a][str(si)][str(sf)][exp][str(nn)] = {}

    t_pdr_results = []
    t_prr_results = []
    t_rdc_results = []

    a_pdr_results = []
    a_prr_results = []
    a_rdc_results = []

    path = os.path.join(data_directory,
                        a,
                        "si_{}".format(si),
                        "sf_{}".format(sf),
                        exp,
                        "sim-{}-neigh-realsim-*".format(nn))

    for dirname in subprocess.check_output("ls -d " + path, shell=True).split():
        resultsfile = os.path.join(dirname.decode("ascii"), "COOJA.testlog")

        if not os.access(resultsfile, os.R_OK):
            continue

        r = process_file(resultsfile, exp, si, False)
        pdr = [x[0] for x in r]
        prr = [x[1] for x in r]
        rdc = [x[2] for x in r]
        t_pdr_results += pdr
        t_prr_results += prr
        t_rdc_results += rdc
        a_pdr_results.append(np.mean(pdr))
        a_prr_results.append(np.mean(prr))
        a_rdc_results.append(np.mean(rdc))

    if ONLY_MEDIAN:
        if len(a_pdr_results):
            midpoint = len(a_pdr_results) // 2
            print("pdr=", sorted(a_pdr_results))
            pdr_metric = sorted(a_pdr_results)[midpoint]
            prr_metric = sorted(a_prr_results)[midpoint]
            rdc_metric = sorted(a_rdc_results)[midpoint]
        else:
            pdr_metric = 0
            prr_metric = 0
            rdc_metric = 0
    else:
        pdr_metric = np.mean(t_pdr_results)
        prr_metric = np.mean(t_prr_results)
        rdc_metric = np.mean(t_rdc_results)

    data[a][str(si)][str(sf)][exp][str(nn)]["pdr"] = pdr_metric
    data[a][str(si)][str(sf)][exp][str(nn)]["prr"] = prr_metric
    data[a][str(si)][str(sf)][exp][str(nn)]["rdc"] = rdc_metric

###########################################

def exec_remote_cmd(cmd):
    subprocess.call("ssh " + TESTBED_HOST + " '" + cmd + "'", shell=True)

###########################################

def exec_local_cmd(cmd):
    subprocess.call(cmd, shell=True)

###########################################

def load_testbed(data_directory, data, a, si, sf, exp, nn):
    data[a][str(si)][str(sf)][exp][str(nn)] = {}

    filename = os.path.join(data_directory,
                        a,
                        "si_{}".format(si),
                        "sf_{}".format(sf),
                        exp,
                        "sim-{}-neigh-realsim-*".format(nn))

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

    local_file = os.path.join(TESTBED_LOCAL_DIR, filename)
    remote_file = os.path.join(TESTBED_REMOTE_DIR, filename)
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
            data[a][str(si)][str(sf)][exp][str(nn)]["pdr"] = 0.0
            data[a][str(si)][str(sf)][exp][str(nn)]["prr"] = 0.0
            data[a][str(si)][str(sf)][exp][str(nn)]["rdc"] = 0.0
            return

    r = process_file(local_file, exp, si, True)

    t_pdr_results = []
    t_prr_results = []
    t_rdc_results = []

    for pdr, prr, rdc in r:
        t_pdr_results.append(pdr)
        t_prr_results.append(prr)
        t_rdc_results.append(rdc)

    if ONLY_MEDIAN:
        if len(t_pdr_results):
            midpoint = len(t_pdr_results) // 2
            print("pdr=", sorted(t_pdr_results))
            pdr_metric = sorted(t_pdr_results)[midpoint]
            prr_metric = sorted(t_prr_results)[midpoint]
            rdc_metric = sorted(t_rdc_results)[midpoint]
        else:
            pdr_metric = 0.0
            prr_metric = 0.0
            rdc_metric = 0.0
    else:
        pdr_metric = np.mean(t_pdr_results)
        prr_metric = np.mean(t_prr_results)
        rdc_metric = np.mean(t_rdc_results)

#    if prr_metric == 0.0:
#        rdc_metric = 0.0
#    else:
#        rdc_metric = 1.0 + 0.2 * (100 / sf) # XXX - some sort of sense

    data[a][str(si)][str(sf)][exp][str(nn)]["pdr"] = pdr_metric
    data[a][str(si)][str(sf)][exp][str(nn)]["prr"] = prr_metric
    data[a][str(si)][str(sf)][exp][str(nn)]["rdc"] = rdc_metric

###########################################

def load_all(data_directory, is_testbed):
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
                        if is_testbed:
                            load_testbed(data_directory, data, a, si, sf, exp, nn)
                        else:
                            load_simulations(data_directory, data, a, si, sf, exp, nn)

    return data

###########################################

def aggregate(data, a, si, sf, exp, nn, metric):
    return data[a][str(si)][str(sf)][exp][str(nn)][metric]

###########################################

def plot_all(data, exp):
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

            filename = "sim_{}_pdr_per_duty_cycle_allsf_nn{}_si{}.pdf".format(exp, nn, si)
            graph_line(rdc_results,  pdr_results, "Duty cycle, %", "End-to-end PDR, %", pointlabels,
                       filename)

###########################################

def plot_comparative_runs(data1, data2, exp):
    # plot all per duty cycle
    for nn in NUM_NEIGHBORS:
        for si in SEND_INTERVALS:
            for i, a in enumerate(ALGORITHMS):
                print("Algorithm {}".format(ALGONAMES[a]))
                pdr_results = [[], []]
                rdc_results = [[], []]
                pointlabels = [[], []]

                for sf in SLOTFRAME_SIZES:
                    sfs = "sf={}".format(sf)
                    print(sfs)
                    rdc_results[0].append(aggregate(data1, a, si, sf, exp, nn, "rdc"))
                    pdr_results[0].append(aggregate(data1, a, si, sf, exp, nn, "pdr"))
                    pointlabels[0].append(sfs)

                    rdc_results[1].append(aggregate(data2, a, si, sf, exp, nn, "rdc"))
                    pdr_results[1].append(aggregate(data2, a, si, sf, exp, nn, "pdr"))
                    pointlabels[1].append(sfs)

                filename = "sim_comparative_{}_{}_pdr_per_duty_cycle_allsf_nn{}_si{}.pdf".format(exp, a, nn, si)
                graph_line(rdc_results,  pdr_results, "Duty cycle, %", "End-to-end PDR, %", pointlabels,
                           filename)

###########################################

def plot_best_per_send_frequency(data, exp):

    # plot comparison of the best
    for sfi in range(3):
        for nn in NUM_NEIGHBORS:
            pdr_results = [[] for _ in BEST_ALGORITHMS]
            rdc_results = [[] for _ in BEST_ALGORITHMS]
            si_results  = [[] for _ in BEST_ALGORITHMS]
            pointlabels = [[] for _ in BEST_ALGORITHMS]

            for si in SEND_INTERVALS:
                #print("si={}".format(si))
                fr = 60.0 / si

                for i, a in enumerate(BEST_ALGORITHMS):
                    print("Algorithm {}".format(ALGONAMES[a]))
                    if sfi == 0:
                        sf = 11
                    elif sfi == 1:
                        sf = 19
                    else:
                        sf = 101

                    rdc_results[i].append(aggregate(data, a, si, sf, exp, nn, "rdc"))
                    pdr_results[i].append(aggregate(data, a, si, sf, exp, nn, "pdr"))
                    si_results[i].append(fr)
                    pointlabels[i].append("rdc={:.1f}%".format(rdc_results[i][-1])) # the PDR

            filename = "sim_{}_pdr_per_sfr_sf{}_nn{}.pdf".format(exp, sf, nn)
            graph_line(si_results, pdr_results, "Send frequency, packets / minute", "End-to-end PDR, %", pointlabels,
                       filename)

###########################################

def ensure_loaded(data_file, data_directory, is_testbed):
    if os.access(data_file, os.R_OK):
        print("Cached file found, using it directly")
        with open(data_file, "r") as f:
            data = json.load(f)
    else:
        print("Cached file not found, parsing log files...")
        data = load_all(data_directory, is_testbed)
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
    safe_mkdir(TESTBED_LOCAL_DIR)
    safe_mkdir(TESTBED_REMOTE_DIR)

    data = ensure_loaded(DATA_FILE, DATA_DIRECTORY, True)

    for exp in EXPERIMENTS:
        plot_all(data, exp)

###########################################

if __name__ == '__main__':
    main()
    print("all done!")
