#!/usr/bin/python

import sys, os, copy, errno
import multiprocessing
import subprocess

from parameters import *

OUT_DIRECTORY = os.path.join(SELF_PATH, "simulations")

# tailor the workload depending on the number of cores;
# but leave some cores free for other things
NUM_CORES = multiprocessing.cpu_count() * 7 // 8

ENV = {
    "FIRMWARE_TYPE" : "1",
    "ORCHESTRA_CONF_UNICAST_PERIOD" : "11"
}

########################################

def create_out_dir(name):
    try:
        os.mkdir(name)
    except IOError as e:
        if e.errno != errno.EEXIST:
           print("Failed to create " + name)
           print(e)
        pass
    except Exception as ex:
        pass

########################################

def generate_simulations(dirname, env, wildcards, experiments):
    makefile = open("Makefile.tmpl", "r").read()

    # replace the template symbols with their values
    for key in env:
        makefile = makefile.replace("@" + key + "@", str(env[key]))

    print("dirname=", dirname)

    filenames = []
    for fs in wildcards:
        fs = os.path.join(SELF_PATH, fs)
        try:
            filenames += subprocess.check_output("ls " + fs, shell=True).split()
        except Exception as ex:
            print(ex)

    all_directories = []
    for exp in experiments:
        exp_dirname = os.path.join(dirname, exp)
        create_out_dir(exp_dirname)

        for filename in filenames:
            sim_name = os.path.basename(os.path.splitext(filename)[0])
            sim_dirname = os.path.join(exp_dirname, sim_name)
            create_out_dir(sim_dirname)

            all_directories.append(sim_dirname)

            subprocess.call("cp " + filename + " " + sim_dirname + "/sim.csc", shell=True)
            subprocess.call("cp ../common-conf.h " + sim_dirname, shell=True)
            with open(sim_dirname + "/Makefile.common", "w") as f:
                f.write(makefile)

            # all files go into "node"
            create_out_dir(sim_dirname + "/node")
            subprocess.call("cp ../" + exp + "/project-conf.h " + sim_dirname + "/node", shell=True)
            subprocess.call("cp ../" + exp + "/Makefile " + sim_dirname + "/node", shell=True)
            subprocess.call("cp ../" + exp + "/node.c " + sim_dirname + "/node", shell=True)
    return all_directories

########################################

def generate_runner(description, all_directories, do_overwrite):
    open_as = "w" if do_overwrite else "a+"
    with open("run-" + description + ".sh", open_as) as f:
        if do_overwrite:
            f.write("#!/bin/bash\n")

        for i, dirname in enumerate(all_directories):
            f.write("./run_cooja.py " + dirname + " &\n")
            if i % NUM_CORES == NUM_CORES - 1:
                f.write("wait\n\n")
        f.write("wait\n")

    os.chmod("run-" + description + ".sh", 0o755)

########################################
def main():
    # sparse, medium, and dense networks - depending on the neighbor count
    wildcards = ["sim-3-neigh*.csc", "sim-7-neigh*.csc", "sim-11-neigh*.csc"]

    all_directories = []
    dirname1 = OUT_DIRECTORY
    create_out_dir(dirname1)
    for i, a in enumerate(ALGORITHMS):
        firmware_type = i + 1
        dirname2 = os.path.join(dirname1, a)
        create_out_dir(dirname2)
        for si in SEND_INTERVALS:
            dirname3 = os.path.join(dirname2, "si_{}".format(si))
            create_out_dir(dirname3)
            for ss in SLOTFRAME_SIZES:
                dirname4 = os.path.join(dirname3, "sf_{}".format(ss))
                create_out_dir(dirname4)
                cenv = copy.copy(ENV)
                cenv["FIRMWARE_TYPE"] = str(firmware_type)
                cenv["SEND_INTERVAL_SEC"] = str(si)
                cenv["ORCHESTRA_CONF_UNICAST_PERIOD"] = str(ss)
                all_directories += generate_simulations(dirname4, cenv, wildcards, EXPERIMENTS)
    generate_runner("all", all_directories, True)


    wildcards = ["3nodes-cooja-ll.csc"]
    all_directories = generate_simulations(dirname4, cenv, wildcards, EXPERIMENTS)
    generate_runner("lite", all_directories, True)


########################################
if __name__ == '__main__':
    main()
    print("all done!")

