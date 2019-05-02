#!/usr/bin/python3

import os
import sys
import time
import subprocess

#import pylab as pl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pl
import matplotlib.legend_handler as lh
from scipy import stats
from scipy.stats.stats import pearsonr
import numpy as np

#
# This calculates and plot these metrics:
# - End-to-end PDR
# - Link-layer PRR (between a node and all of its neighbors)
# - Radio Duty Cycle
#
# The radio duty cycle is based on Energest results.
# For Cooja motes, those are approximate, as e.g.
# the packet transmission time is only modeled with millisecond accuracy.
#

matplotlib.style.use('seaborn')
matplotlib.rcParams['pdf.fonttype'] = 42


OUT_DIR = "../plots"

DATA_DIRECTORY="../simulations"

ALGOS = ["orchestra_sb",
         "orchestra_rb_s",
         "orchestra_rb_ns",
#         "orchestra_rb_ns_sr",
]

ALGONAMES = [
    "Orchestra SB",
    "Orchestra RB / Storing",
    "Orchestra RB / Non-Storing",
#    "Orchestra RB / Non-Storing (SR)", # with RPL storing rule
]

# The nodes generate 1 packet per minute; allow first 10 mins for the network tree building
FIRST_SEQNUM = 11
LAST_SEQNUM =  15

# The root node is ignored in the calculations (XXX: maybe should not ignore its PRR?)
ROOT_ID = 1

# confidence interval
CI = 0.9

###########################################

MARKERS = ["o", "s", "X", "X", "X"]
BASIC_MARKERS = ["o", "s", "X", "X", "X"]

COLORS = ["green", "slateblue", "orange", "red"]
BASIC_COLORS = ["green", "slateblue", "orange", "red"]

def graph_ci(data, ylabel, filename):
    pl.figure(figsize=(6, 3.5))

    width = 0.15

#    print(filename)
    for i, a in enumerate(ALGOS):
        algo_data = data[i]
#        print(ALGONAMES[i])

        to_plot = []
        yerr = []
        for d in algo_data:
            #print("d=", d)
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

    pl.xticks([1, 2, 3, 4], ["sparse", "e. sparse", "dense", "e. dense"])

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

    def calc(self):
        if self.associated_at_minutes is None:
            self.is_valid = False
            return

        first_seqnum = max(FIRST_SEQNUM, self.associated_at_minutes + 1)
        if first_seqnum > LAST_SEQNUM:
            self.is_valid = False
            return

        self.is_valid = True

        if self.packets_tx:
            self.prr = 100.0 * self.packets_ack / self.packets_tx
        else:
            self.prr = 0.0
        expected = LAST_SEQNUM - first_seqnum + 1
        actual = len(self.seqnums)
        #print("seqnums=", self.seqnums, self.associated_at_minutes)
        self.pdr = 100.0 * actual / expected
        if self.radio_total:
            self.rdc = 100.0 * self.radio_on / self.radio_total
        else:
            print("warning: no radio duty cycle for {}".format(self.id))
            self.rdc = 0.0

def process_file(filename):
    motes = {}
    has_assoc = set()
    print(filename)

    in_initialization = True

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

            if "association done" in line:
                #print(line)
                has_assoc.add(node)
                motes[node].associated_at_minutes = (ts // 1000 + 59) // 60
                continue

            if in_initialization:
                # ignore the first N minutes of the test, while the network is being built
                if "initial phase complete" in line:
                    in_initialization = False
                else:
                    continue

            if node == ROOT_ID:
                # 314937392 1 [INFO: Node      ] seqnum=6 from=fd00::205:5:5:5
                if "seqnum=" in line:
                    sn = int(fields[5].split("=")[1])
                    if not (FIRST_SEQNUM <= sn <= LAST_SEQNUM):
                        continue
                    fromaddr = fields[6].split("=")[1]
                    fromnode = int(fromaddr.split(":")[-1], 16)
                    if fromnode not in motes:
                        motes[fromnode] = MoteStats(fromnode)

                    if fromnode in has_assoc \
                       and motes[fromnode].associated_at_minutes < sn:
                        # account for the seqnum
                        motes[fromnode].seqnums.add(sn)

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
                # TODO: accnt for queue drops!
                continue

    r = []
    for k in motes:
        m = motes[k]
        m.calc()
        if m.is_valid:
            r.append((m.pdr, m.prr, m.rdc))
    return r

###########################################

def test_groups(filenames, outfilename, description):
    print(description)

    pdr_results = [[] for _ in ALGOS]
    prr_results = [[] for _ in ALGOS]
    rdc_results = [[] for _ in ALGOS]

    for i, a in enumerate(ALGOS):
        print("Algorithm " + ALGONAMES[i])
        for j, fs in enumerate(filenames):
            t_pdr_results = []
            t_prr_results = []
            t_rdc_results = []

            path = os.path.join(DATA_DIRECTORY, a, fs)

            for dirname in subprocess.check_output("ls -d " + path, shell=True).split():
                resultsfile = os.path.join(dirname.decode("ascii"), "COOJA.testlog")

                if not os.access(resultsfile, os.R_OK):
                    continue

                r = process_file(resultsfile)
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

def main():
    try:
        os.mkdir(OUT_DIR)
    except:
        pass

    test_groups(["sparse-*", "e-sparse-*", "dense-*", "e-dense-*"], "collection.pdf", "Collection")
    #test_groups(["sparse-*", "e-sparse-*", "dense-*", "e-dense-*"], "query.pdf", "Data query")
    #test_groups(["sparse-*", "e-sparse-*", "dense-*", "e-dense-*"], "local.pdf", "Local traffic")

###########################################

if __name__ == '__main__':
    main()
    print("all done!")
