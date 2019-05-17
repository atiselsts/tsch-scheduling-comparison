#!/usr/bin/python3

import os
import sys
import time
import subprocess

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

START_TIME_MINUTES = 10
END_TIME_MINUTES = 30

# The root node is ignored in the calculations (XXX: maybe should not ignore its PRR?)
ROOT_ID = 1

# confidence interval
CI = 0.9

###########################################

MARKERS = ["o", "s", "X", "X", "X"]
BASIC_MARKERS = ["o", "s", "X", "X", "X"]

COLORS = ["green", "slateblue", "orange", "red"]
BASIC_COLORS = ["green", "slateblue", "orange", "red"]

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
            pl.errorbar(x, to_plot, width, yerr=yerr, marker=MARKERS[i], label=ALGONAMES[i])
        else:
            pl.bar(x, to_plot, width, yerr=yerr, label=ALGONAMES[i], color=COLORS[i])
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

    for i, a in enumerate(ALGORITHMS):
        algo_xdata = xdata[i]
        algo_ydata = ydata[i]

        to_plot_x = algo_xdata #[np.mean(d) for d in algo_xdata]
        to_plot_y = algo_ydata #[np.mean(d) for d in algo_ydata]

        pl.scatter(to_plot_x, to_plot_y, label=ALGONAMES[i], color=COLORS[i])

        if pointlabels is not None:
            for j, sf in enumerate(pointlabels[i]):
                pl.gca().annotate("sf={}".format(sf), (to_plot_x[j] + 0.1, to_plot_y[j] + 1), fontsize=6)

    pl.ylim(bottom=0, top=105)
    pl.xlabel(xlabel)
    pl.ylabel(ylabel)
    if "duty" in filename:
        pl.xlim([0, 12.5])
    else: # send frequency
        pl.xscale("log")


    bbox = (1.0, 1.4)
    loc = "upper right"

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

# The nodes generate 1 packet per minute; allow first 10 mins for the network tree building
def get_seqnums(send_interval):
    skip = START_TIME_MINUTES * 60 // send_interval
    expect = END_TIME_MINUTES * 60 // send_interval
    return (skip + 1, expect - 1)

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
            self.is_valid = False
            return

        if self.associated_at_minutes >= 30:
            print("node {} associated too late: {}, seqnums={}".format(
                self.id, self.associated_at_minutes, self.seqnums))
            self.is_valid = False
            return

        self.is_valid = True

        if self.packets_tx:
            self.prr = 100.0 * self.packets_ack / self.packets_tx
        else:
            self.prr = 0.0
        expected = (last_seqnum - first_seqnum) + 1
        actual = len(self.seqnums)
        self.pdr = 100.0 * actual / expected
        if self.radio_total:
            self.rdc = 100.0 * self.radio_on / self.radio_total
        else:
            print("warning: no radio duty cycle for {}".format(self.id))
            self.rdc = 0.0

def process_file(filename, experiment, send_interval):
    motes = {}
    has_assoc = set()
    print(filename)

    in_initialization = True

    first_seqnum, last_seqnum = get_seqnums(send_interval)

    with open(filename, "r") as f:
        for line in f:
            fields = line.strip().split()
            try:
                # in milliseconds
                ts = int(fields[0]) // 1000
                node = int(fields[1]) 
            except:
                # failed to extract timestamp
                continue

            if node not in motes:
                motes[node] = MoteStats(node)

            if "association done (1" in line:
                #print(line)
                has_assoc.add(node)
                motes[node].seqnums = set()
                motes[node].associated_at_minutes = (ts // 1000 + 59) // 60
                continue

            if in_initialization:
                # ignore the first N minutes of the test, while the network is being built
                if "initial phase complete" in line:
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
                        if fromnode in has_assoc \
                           and motes[fromnode].associated_at_minutes < sn:
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

    for i, a in enumerate(ALGORITHMS):
        print("Algorithm {}_{}".format(ALGONAMES[i], ss))
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

        for i, a in enumerate(ALGORITHMS):

            print("Algorithm {}".format(ALGONAMES[i]))

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

def load_all():
    data = {}
    for a in ALGORITHMS:
        data[a] = {}
        for si in SEND_INTERVALS:
            data[a][si] = {}
            for sf in SLOTFRAME_SIZES:
                data[a][si][sf] = {}
                for exp in EXPERIMENTS:
                    data[a][si][sf][exp] = {}
                    for nn in NUM_NEIGHBORS:
                        data[a][si][sf][exp][nn] = {}

                        t_pdr_results = []
                        t_prr_results = []
                        t_rdc_results = []

                        path = os.path.join(DATA_DIRECTORY,
                                            a,
                                            "si_{}".format(si),
                                            "sf_{}".format(sf),
                                            exp,
                                            "sim-{}-neigh-new-*".format(nn))

                        for dirname in subprocess.check_output("ls -d " + path, shell=True).split():
                            resultsfile = os.path.join(dirname.decode("ascii"), "COOJA.testlog")

                            if not os.access(resultsfile, os.R_OK):
                                continue

                            r = process_file(resultsfile, exp, si)
                            for pdr, prr, rdc in r:
                                t_pdr_results.append(pdr)
                                t_prr_results.append(pdr)
                                t_rdc_results.append(rdc)

                        data[a][si][sf][exp][nn]["pdr"] = np.mean(t_pdr_results)
                        data[a][si][sf][exp][nn]["prr"] = np.mean(t_prr_results)
                        data[a][si][sf][exp][nn]["rdc"] = np.mean(t_rdc_results)
    return data

###########################################

def aggregate(data, a, si, sf, exp, nn, metric):
    return data[a][si][sf][exp][nn][metric]

###########################################

def plot_all(data, exp):
    for nn in NUM_NEIGHBORS:
        for si in SEND_INTERVALS:
            pdr_results = [[] for _ in ALGORITHMS]
            rdc_results = [[] for _ in ALGORITHMS]
            pointlabels = [[] for _ in ALGORITHMS]    
            for sf in SLOTFRAME_SIZES:
                print("sf={}".format(sf))
                for i, a in enumerate(ALGORITHMS):
                    print("Algorithm {}".format(ALGONAMES[i]))
                    rdc_results[i].append(aggregate(data, a, si, sf, exp, nn, "rdc"))
                    pdr_results[i].append(aggregate(data, a, si, sf, exp, nn, "pdr"))
                    pointlabels[i].append(sf)

            filename = "sim_{}_pdr_per_duty_cycle_allsf_nn{}_si{}.pdf".format(exp, nn, si)
            graph_line(rdc_results, pdr_results, "Duty cycle, %", "End-to-end PDR, %", pointlabels,
                       filename)

        pdr_results_all = [[] for _ in ALGORITHMS]
        rdc_results_all = [[] for _ in ALGORITHMS]
        si_results_all = [[] for _ in ALGORITHMS]
        pointlabels_all = [[] for _ in ALGORITHMS]

        for sf in SLOTFRAME_SIZES:
            pdr_results = [[] for _ in ALGORITHMS]
            rdc_results = [[] for _ in ALGORITHMS]
            si_results = [[] for _ in ALGORITHMS]
            pointlabels = [[] for _ in ALGORITHMS]    

            for si in SEND_INTERVALS:
                print("si={}".format(si))
                fr = 60.0 / si
                for i, a in enumerate(ALGORITHMS):
                    print("Algorithm {}".format(ALGONAMES[i]))
                    rdc_results[i].append(aggregate(data, a, si, sf, exp, nn, "rdc"))
                    pdr_results[i].append(aggregate(data, a, si, sf, exp, nn, "pdr"))
                    si_results[i].append(fr)
                    pointlabels[i].append(sf)

                    pdr_results_all[i].append(pdr_results[i][-1])
                    rdc_results_all[i].append(rdc_results[i][-1])
                    si_results_all[i].append(fr)
                    pointlabels_all[i].append(sf)

            filename = "sim_{}_pdr_per_sfr_nn{}_sf{}.pdf".format(exp, nn, sf)
            graph_line(si_results, pdr_results, "Send frequency, Hz", "End-to-end PDR, %", pointlabels,
                       filename)
        filename = "sim_{}_pdr_per_sfr_allsf_nn{}.pdf".format(exp, nn)
        graph_line(si_results_all, pdr_results_all, "Send frequency, Hz", "End-to-end PDR, %", pointlabels_all,
                       filename)

###########################################

def main():
    try:
        os.mkdir(OUT_DIR)
    except:
        pass

    data = load_all()

    for exp in EXPERIMENTS:
        plot_all(data, exp)

###########################################

if __name__ == '__main__':
    main()
    print("all done!")
