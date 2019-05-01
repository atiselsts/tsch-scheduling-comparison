#!/usr/bin/python3

import os
import sys
import time
import subprocess
#import energymodel

import pylab as pl
import matplotlib
import matplotlib.legend_handler as lh
from scipy import stats
from scipy.stats.stats import pearsonr
import numpy as np

matplotlib.style.use('seaborn')
matplotlib.rcParams['pdf.fonttype'] = 42

OUT_DIR = "../plots"

DATA_DIRECTORY="../simulations"

ALGOS = ["orchestra_sb",
         "orchestra_rb_s",
         "orchestra_rb_ns",
]

ALGONAMES = [
    "Orchestra SB",
    "Orchestra RB / Storing",
    "Orchestra RB / Non-Storing",
]

SLOTS_PER_SECOND = 100

CI = 0.9

###########################################

MARKERS = ["o", "s", "X", "X", "X"]
BASIC_MARKERS = ["o", "s", "X", "X", "X"]

COLORS = ["green", "slateblue", "orange", "red"]
BASIC_COLORS = ["green", "slateblue", "orange", "red"]

def graph_ci(data, ylabel, filename):
    pl.figure(figsize=(6, 3.5))

    width = 0.15

    print(filename)
    for i, a in enumerate(ALGOS):
        algo_data = data[i]
        print(ALGONAMES[i])

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
        print("plot ", ylabel)
        print(to_plot)

    pl.ylim(ymin=0)
    pl.xlabel("Experiment type")
    pl.ylabel(ylabel)

    pl.xticks([1, 2, 3, 4], ["sparse", "dense"])

    bbox = (1.0, 1.0)
    loc = "upper right"
#    pl.ylim([0, 700])

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

FIRST_SEQNUM = 5
LAST_SEQNUM = 10

class MoteStats:
    def __init__(self, id):
        self.id = id
        self.seqnums = set()
        self.packets_tx = 0
        self.packets_ack = 0
        self.radio_on = 0
        self.radio_total = 0

    def calc(self):
        if self.packets_tx:
            self.prr = 100.0 * self.packets_ack / self.packets_tx
        else:
            self.prr = 0.0
        expected = LAST_SEQNUM - FIRST_SEQNUM + 1
        actual = len(self.seqnums)
        self.pdr = actual / expected
        if self.radio_total:
            self.rdc = self.radio_on / self.radio_total
        else:
            print("warning: no radio duty cycle for {}".format(self.id))
            self.rdc = 0.0

def process_file(filename):
    motes = {}
    print(filename)

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

            fields = line.split()
            try:
                # in milliseconds
                ts = int(fields[0]) // 1000
                node = int(fields[1]) 
            except:
                # failed to extract timestamp
                continue
            if node not in motes:
                motes[node] = MoteStats(node)

            # 314937392 1 [INFO: Node      ] seqnum=6 from=fd00::205:5:5:5
            if "seqnum=" in line:
                sn = int(fields[5].split("=")[1])
                if not (FIRST_SEQNUM <= sn <= LAST_SEQNUM):
                    continue
                fromaddr = fields[6].split("=")[1]
                fromnode = int(fromaddr.split(":")[-1], 16)
                if fromnode not in motes:
                    motes[fromnode] = MoteStats(fromnode)
                motes[fromnode].seqnums.add(sn)
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

    test_groups(["sparse", "dense"], "collection.pdf", "Collection")


###########################################

if __name__ == '__main__':
    main()
    print("all done!")
