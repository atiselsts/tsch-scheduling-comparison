#!/usr/bin/python3

import os
import sys
import time
import subprocess
import energymodel

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

ALGOS = ["instant",
         "connections",
         "orchestra-greedy",
         "orchestra",
]

ALGONAMES = [
    #"Instant (fast switching)",
    "Instant (regular mode)",
    #"Instant (slow switching)",
    "Instant (connection mode)",
    "RPL + Greedy Orchestra",
    "RPL + Orchestra",
]

BASIC_ALGOS = ["instant",
               "connections",
               "orchestra-greedy",
               "orchestra",
]

BASIC_ALGONAMES = ["Instant (regular mode)",
                   "Instant (connection mode)",
                   "RPL + Greedy Orchestra",
                   "RPL + Orchestra",
]

MAX_DIO_INTERVALS = [2, 4, 8, 16, 32]
MAX_DIO_INTERVALS_LOG = [0, 1, 2, 3, 4]

PROBING_INTERVALS = [5, 10, 15, 20, 25]

MAX_WEARABLES = 10

CI = 0.9

SLOTS_PER_SECOND = 100

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
    pl.xlabel("Number of wearables")
    pl.ylabel(ylabel)

    pl.xticks([1, 2, 3, 4], ["1", "2", "4", "8"])

    if "energy" in filename:
        bbox = (0.0, 0.0)
        loc = "lower left"
        pl.ylim([0, 700])
    elif "makespan" in filename:
        if "_s" in filename:
            bbox = (1.0, 1.0)
            loc = "upper right"
        else:
            bbox = (0.0, 1.0)
            loc = "upper left"
        pl.ylim([0, 300])
    else:
        # fairness
        bbox = (0.0, 1.0)
        loc = "upper left"
        pl.ylim([0, 50])

    if "makespan" in filename:
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
def graph_ci_grid(data, ylabel, filename):
    pl.figure(figsize=(3.5, 2.5))

    for i, a in enumerate(BASIC_ALGOS):
        algo_data = data[i]

        to_plot = []
        yerr = []

        for d in algo_data:
            mean, sigma = np.mean(d), np.std(d)
            stderr = 1.0 * sigma / (len(d) ** 0.5)
            ci = stats.norm.interval(CI, loc=mean, scale=stderr) - mean

            to_plot.append(mean)
            yerr.append(ci[0])

        x = np.arange(len(to_plot)) + 1.0
        marker = BASIC_MARKERS[i]
        color = BASIC_COLORS[i]
        if a == "connections":
            pl.errorbar(x, to_plot, yerr=yerr, marker=marker, color=color, label=BASIC_ALGONAMES[i], markerfacecolor="None")
        else:
            pl.errorbar(x, to_plot, yerr=yerr, marker=marker, color=color, label=BASIC_ALGONAMES[i])

    pl.ylim(ymin=0)
    pl.ylabel(ylabel)

    if "density" in filename:
        bbox = (0.0, 1.2)
        loc = "upper left"
        x = range(1, 11)
        pl.xticks(x, [str(el) for el in x])
        pl.xlabel("Number of wearables")
    else:
        bbox = (0.0, 1.2)
        loc = "upper left"
        x = range(1, 11)
        pl.xticks(x, [str(el*el) for el in x])
        pl.xlabel("Number of access points")


    if "energy" in filename:
        pl.ylim([0, 700])
    elif "makespan" in filename:
        pl.ylim([0, 300]) # XXX: 500 in order to fit the legend in?
    else:
        # fairness
        pl.ylim([0, 50])

    if "makespan" in filename:
        legend = pl.legend(bbox_to_anchor=bbox, loc=loc, ncol=1,
                           prop={"size":9},
                           handler_map={lh.Line2D: lh.HandlerLine2D(numpoints=1)})

        pl.savefig(OUT_DIR + "/" + filename, format='pdf',
                   bbox_extra_artists=(legend,),
                   bbox_inches='tight')
    else:
        pl.savefig(OUT_DIR + "/" + filename, format='pdf',
                   bbox_inches='tight')

###########################################

def graph_ci_optimization(data, intervals, xlabel, ylabel, filename):
    pl.figure(figsize=(5, 2.5))

    to_plot = []
    yerr = []
    all_x = []
    all_y = []

    for i, d in enumerate(data):
        mean, sigma = np.mean(d), np.std(d)
        stderr = 1.0 * sigma / (len(d) ** 0.5)
        ci = stats.norm.interval(CI, loc=mean, scale=stderr) - mean

        for v in d:
          all_x.append(i)
          all_y.append(v)
        to_plot.append(mean)
        yerr.append(ci[0])

    x = np.arange(len(to_plot))
    pl.errorbar(x, to_plot, yerr=yerr, marker="o")

    c = pearsonr(all_x, all_y)
    print(filename, "Correlation: ", c)

    pl.ylim(ymin=0)
    pl.xlabel(xlabel)
    pl.ylabel(ylabel)

    if "dio" in filename:
        pl.xticks(x, [str(1 << (el + 1)) for el in intervals])
    else:
        pl.xticks(x, [str(el) for el in intervals])

    if "energy" in filename:
#        bbox = (0.0, 0.0)
#        loc = "lower left"
        pl.ylim([0, 700])
    elif "makespan" in filename:
#        bbox = (0.0, 1.0)
#        loc = "upper left"
        pl.ylim([0, 300])
    else:
#        # fairness
#        bbox = (0.0, 1.0)
#        loc = "upper left"
        pl.ylim([0, 50])

    pl.savefig(OUT_DIR + "/" + filename, format='pdf',
               bbox_inches='tight')

###########################################

def get_wearable_id_asn(line):
    #128043856:194:12803
    fields = line.split(":")
    wearble_id = int(fields[1]) - 192
    asn = int(fields[2])
    return wearble_id, asn

###########################################
def process_file(filename):
    r = []
    print("  " + filename)

    wearable_stats = [{} for _ in range(MAX_WEARABLES)]
    for i in range(MAX_WEARABLES):
        wearable_stats[i]["started"] = False
        wearable_stats[i]["start_slot"] = None
        wearable_stats[i]["missed_slotframes_in_row"] = 0
        wearable_stats[i]["skip_periods"] = []

    with open(filename, "r") as f:
        for line in f:
            if "BUG" in line:
                print(line)
                continue

            if "start send" in line:
                fields = line.split(" ")
                wid, asn = get_wearable_id_asn(fields[1])

                if not wearable_stats[wid]["started"]:
                    wearable_stats[wid]["started"] = True
                    wearable_stats[wid]["start_slot"] = asn
                else:
                    print("Error! started multiple times?")

            if "no gw" in line:
                #> 128043856:194:12803 no gw
                fields = line.split(" ")
                wid, asn = get_wearable_id_asn(fields[1])

                wearable_stats[wid]["missed_slotframes_in_row"] += 1

                continue

            if "sel gw" in line:
                #> 128526504:192:12852 sel gw 3
                fields = line.split(" ")
                wid, asn = get_wearable_id_asn(fields[1])

                if wearable_stats[wid]["missed_slotframes_in_row"]:
                    wearable_stats[wid]["skip_periods"].append(wearable_stats[wid]["missed_slotframes_in_row"])
                    wearable_stats[wid]["missed_slotframes_in_row"] = 0

                continue

            if "finished sending" in line:
                #> 210298240:192:21029 finished sending: 1503 data 37 probing 37 lost
                fields = line.split(" ")
                wid, asn = get_wearable_id_asn(fields[1])

                if wearable_stats[wid]["start_slot"]:
                  slots = asn - wearable_stats[wid]["start_slot"]
                  #> 152918240:193:15291 finished sending: 1092 d 0 pr 30 rxi 2 rxuc 17 rxbc 34 txuc 0 txbc 0 >_8_tx
                  sent = int(fields[4])
                  probing_sent = int(fields[6])
                  rxi = int(fields[8])
                  rxuc = int(fields[10])
                  rxbc = int(fields[12])
                  txuc = int(fields[14])
                  txbc = int(fields[16])

                  # convert packets to mJ and account per single wearable
                  energy = energymodel.account_ex(sent, probing_sent, rxi, rxuc, rxbc, txuc, txbc)

                  if len(wearable_stats[wid]["skip_periods"]):
                     avg_skip_period_len = np.mean(wearable_stats[wid]["skip_periods"])
                  else:
                     avg_skip_period_len = 0

                  r.append((slots, energy, avg_skip_period_len))

                wearable_stats[wid]["started"] = False
                wearable_stats[i]["start_slot"] = None
                wearable_stats[wid]["skip_periods"] = []
                wearable_stats[wid]["missed_slotframes_in_row"] = 0
                continue

    return r

###########################################

def test_groups(filenames, outfilename, description):
    print(description)

    makespan_results = [[] for _ in ALGOS]
    energy_results = [[] for _ in ALGOS]
    skip_period_results = [[] for _ in ALGOS]

    for i, a in enumerate(ALGOS):
        print("Algorithm " + ALGONAMES[i])
        for nw, fs in enumerate(filenames):
            print("{} wearables".format(nw + 1))
            t_makespan_results = []
            t_energy_results = []
            t_skip_period_results = []

            path = os.path.join(DATA_DIRECTORY, a, fs)

            for dirname in subprocess.check_output("ls -d " + path, shell=True).split():
                resultsfile = os.path.join(dirname.decode("ascii"), "COOJA.testlog")

                if not os.access(resultsfile, os.R_OK):
                    continue

                r = process_file(resultsfile)
                for slots, energy, avg_skip_period_len in r:
                    # convert slots to seconds here
                    t_makespan_results.append(1.0 * slots / SLOTS_PER_SECOND)
                    t_energy_results.append(energy)
                    # fairness
                    t_skip_period_results.append(avg_skip_period_len)

            makespan_results[i].append(t_makespan_results)
            energy_results[i].append(t_energy_results)
            skip_period_results[i].append(t_skip_period_results)

    # plot the results
    graph_ci(makespan_results, "Time, sec", "sim_makespan_" + outfilename)
    graph_ci(energy_results, "Energy per wearable, mJ", "sim_energy_" + outfilename)
    graph_ci(skip_period_results, "Avg. delay between\nactive slotframes,\nnumber of slotframes", "sim_fairness_" + outfilename)

    print("")

###########################################

def test_grid(filenames, outfilename, description, change_grid_size):
    print(description)

    makespan_results = [[] for _ in BASIC_ALGOS]
    energy_results = [[] for _ in BASIC_ALGOS]
    skip_period_results = [[] for _ in BASIC_ALGOS]

    grid_edge = 3
    nw = 4

    for j, a in enumerate(BASIC_ALGOS):
        print(BASIC_ALGONAMES[j])

        for i, fs in enumerate(filenames):
            if change_grid_size:
                grid_edge = i + 1
                print("{} grid edge".format(grid_edge))
            else:
                nw = i + 1
                print("{} num wear".format(nw))

            t_makespan_results = []
            t_energy_results = []
            t_skip_period_results = []

            path = os.path.join(DATA_DIRECTORY, a, fs)
            for dirname in subprocess.check_output("ls -d " + path, shell=True).split():

                resultsfile = os.path.join(dirname.decode("ascii"), "COOJA.testlog")
                if not os.access(resultsfile, os.R_OK):
                    continue

                r = process_file(resultsfile)
                for slots, energy, avg_skip_period_len in r:
                    # convert slots to seconds here
                    t_makespan_results.append(1.0 * slots / SLOTS_PER_SECOND)
                    t_energy_results.append(energy)
                    # fairness
                    t_skip_period_results.append(avg_skip_period_len)

            makespan_results[j].append(t_makespan_results)
            energy_results[j].append(t_energy_results)
            skip_period_results[j].append(t_skip_period_results)

    # plot the results
    graph_ci_grid(makespan_results, "Time, sec", "sim_makespan_" + outfilename)
    graph_ci_grid(energy_results, "Energy per wearable, mJ", "sim_energy_" + outfilename)
    graph_ci_grid(skip_period_results, "Avg. delay between\nactive slotframes,\nnumber of slotframes",
                  "sim_fairness_" + outfilename)

    print("")

###########################################

def test_rpl_optimization(rpltype, outfilename, xlabel, intervals):
    print("RPL optimization")

    makespan_results = [[] for _ in intervals]
    energy_results = [[] for _ in intervals]
    skip_period_results = [[] for _ in intervals]

    grid_edge = 3
    nw = 4

    filenames = ["random-m3w-*"]

    for j, interval in enumerate(intervals):
        print("interval=", interval)

        t_makespan_results = []
        t_energy_results = []
        t_skip_period_results = []

        for i, fs in enumerate(filenames):

            path = os.path.join(DATA_DIRECTORY, rpltype + "-optimization-" + str(interval), fs)
            print("path=", path)
            for dirname in subprocess.check_output("ls -d " + path, shell=True).split():

                resultsfile = os.path.join(dirname.decode("ascii"), "COOJA.testlog")
                r = process_file(resultsfile)

                for slots, energy, avg_skip_period_len in r:
                    # convert slots to seconds here
                    t_makespan_results.append(1.0 * slots / SLOTS_PER_SECOND)
                    t_energy_results.append(energy)
                    # fairness
                    t_skip_period_results.append(avg_skip_period_len)

        energy_results[j] = t_energy_results
        skip_period_results[j] = t_skip_period_results
        makespan_results[j] = t_makespan_results

    # plot the results
    graph_ci_optimization(makespan_results, intervals, xlabel, "Time, sec", "sim_makespan_" + outfilename)
    graph_ci_optimization(energy_results, intervals, xlabel, "Energy per wearable, mJ", "sim_energy_" + outfilename)
    graph_ci_optimization(skip_period_results, intervals, xlabel, "Avg. delay between\nactive slotframes,\nnumber of slotframes",
                  "sim_fairness_" + outfilename)

    print("")


###########################################

def main():
    try:
        os.mkdir(OUT_DIR)
    except:
        pass

    test_groups(["random-s1w-*", "random-s2w-*", "random-s3w-*", "random-s4w-*"], "s.pdf", "Static")
    time.sleep(1)
    test_groups(["random-m1w-*", "random-m2w-*", "random-m3w-*", "random-m4w-*"], "m.pdf", "Mobile")
    time.sleep(1)

    filenames = ["grid-m4w-s{}-*".format(grid_size) for grid_size in range(1, 11)]
    test_grid(filenames, "grid.pdf", "Mobile on grid", True)

    filenames = ["wgrid-m{}w-s2-*".format(nw) for nw in range(1, 11)]
    test_grid(filenames, "density_grid.pdf", "Mobile on grid", False)

    test_rpl_optimization("rpl-dio", "rpl-dio.pdf", "Max RPL DIO interval, sec",  MAX_DIO_INTERVALS_LOG)
    test_rpl_optimization("rpl-probing", "rpl-probing.pdf", "RPL probing interval, sec", PROBING_INTERVALS)


###########################################

if __name__ == '__main__':
    main()
    print("all done!")
